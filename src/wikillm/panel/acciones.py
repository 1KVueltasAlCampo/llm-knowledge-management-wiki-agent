"""Acciones que el panel puede ejecutar: un catálogo cerrado con parámetros validados.

Las que usan el modelo o la GPU corren dentro del proceso, con las mismas funciones que las
órdenes de consola, la salida capturada y el cliente del modelo observado; las demás corren como
subprocesos y su salida se transmite línea a línea. Ninguna acción acepta una orden ni una ruta
libres: de la página solo llegan los parámetros declarados aquí, ya validados.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from wikillm.arnes.__main__ import armar_brazos, crear_indice_rag
from wikillm.arnes.__main__ import principal as principal_arnes
from wikillm.arnes.comparar import crear_resolutor
from wikillm.common.config import Settings, load_settings
from wikillm.common.modelo import ClienteModelo
from wikillm.common.responder import Brazo
from wikillm.panel import datos
from wikillm.panel.archivos import ArchivoNoPermitido, normalizar
from wikillm.panel.observado import ClienteObservado
from wikillm.wiki.__main__ import principal as principal_wiki

Emitir = Callable[[dict[str, Any]], None]
WIKI_DEMO = "data/wiki/demo"
WIKI_BASE = "data/wiki/dev2"
REGISTRO_DEL_MODELO = Path("results/demo/llamadas.jsonl")
EVIDENCIA_DE_LA_DEMO = Path("results/demo/comparaciones.jsonl")
ENSAYOS = Path("results/demo/ensayos")
PREGUNTA_MAXIMA = 400
PAPERS_DEL_CORPUS = 50
TIEMPO_MAXIMO_DE_SUBPROCESO = 180.0
LINEA_DE_PROGRESO = re.compile(r"%\||it/s\]|s/it\]")
PASOS_DEL_PILOTO = "0,5"
TIPOS_DEL_PILOTO = "T1,T4,T5"


class AccionDesconocida(LookupError):
    """La acción pedida no está en el catálogo."""


class ParametroInvalido(ValueError):
    """Un parámetro no cumple lo que declara el catálogo."""


class ConfirmacionRequerida(PermissionError):
    """La acción gasta saldo o borra estado y no llegó la confirmación explícita."""


class TopeDeSesion(RuntimeError):
    """El gasto de la sesión alcanzó su tope: no se aceptan más acciones de pago."""


@dataclass(frozen=True)
class Parametro:
    nombre: str
    tipo: str  # texto | entero | carpeta | opcion
    etiqueta: str
    por_defecto: Any = None
    minimo: int = 0
    maximo: int = 0
    opciones: tuple[str, ...] = ()


@dataclass(frozen=True)
class Accion:
    id: str
    titulo: str
    resumen: str
    parametros: tuple[Parametro, ...] = ()
    gasta: bool = False
    usd_estimado: float = 0.0
    estimacion: str = ""
    destructiva: bool = False
    grabar: bool = True

    def a_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "resumen": self.resumen,
            "gasta": self.gasta,
            "estimacion": self.estimacion,
            "destructiva": self.destructiva,
            "parametros": [
                {
                    "nombre": p.nombre,
                    "tipo": p.tipo,
                    "etiqueta": p.etiqueta,
                    "por_defecto": p.por_defecto,
                    "minimo": p.minimo,
                    "maximo": p.maximo,
                    "opciones": list(p.opciones),
                }
                for p in self.parametros
            ],
        }


P_PREGUNTA = Parametro("pregunta", "texto", "Pregunta", "")
P_WIKI = Parametro("wiki", "carpeta", "Carpeta del wiki", WIKI_DEMO)
P_PASO = Parametro("paso", "entero", "Ingerir hasta el paper n.º", 6, 1, PAPERS_DEL_CORPUS)

CATALOGO: tuple[Accion, ...] = (
    Accion(
        "calentar",
        "Cargar el índice del RAG",
        "Carga el modelo de embeddings en la GPU y abre el índice vectorial una sola vez.",
        grabar=False,
    ),
    Accion(
        "git_wiki",
        "Historial versionado del wiki",
        "Una copia versionada por ingesta, con su etiqueta paso-N.",
        (P_WIKI,),
    ),
    Accion(
        "comparar",
        "Preguntar a los dos sistemas",
        "El RAG y el WikiLLM responden la misma pregunta con el mismo modelo.",
        (P_PREGUNTA, P_WIKI),
        gasta=True,
        usd_estimado=0.003,
        estimacion="≈ 0,001 USD (RAG: 1 llamada; wiki: 2 a 4)",
    ),
    Accion(
        "estimar_ingesta",
        "Estimar el costo de una ingesta",
        "Cuántos papers faltan y cuánto costaría ingerirlos. No llama al modelo.",
        (P_PASO, P_WIKI),
    ),
    Accion(
        "ingerir",
        "Ingerir un paper en el wiki",
        "El agente actualiza el wiki con el siguiente paper (plan y escritura) y valida las citas.",
        (P_PASO, P_WIKI),
        gasta=True,
        usd_estimado=0.015,
        estimacion="≈ 0,008 USD · unos 40 s (2 llamadas)",
    ),
    Accion(
        "estimar_corrida",
        "Estimar el costo de una corrida",
        "Cuánto costaría correr el banco en los dos sistemas. No llama al modelo.",
        (Parametro("alcance", "opcion", "Alcance", "piloto", opciones=("piloto", "completa")),),
    ),
    Accion(
        "metricas",
        "Métricas del piloto",
        "Cobertura, abstención, fundamentación y contexto por sistema y por paso.",
    ),
    Accion(
        "validar_banco", "Validar el banco de preguntas", "Revisa el formato de las 60 preguntas."
    ),
    Accion(
        "verificar",
        "Verificar la preparación",
        "Datos, índice, GPU, wiki y repositorio: lo que debe estar listo antes de empezar.",
    ),
    Accion(
        "reiniciar_wiki",
        "Reiniciar el wiki de la demostración",
        "Reemplaza data/wiki/demo por una copia limpia del paso 5 y aparta la evidencia anterior.",
        destructiva=True,
        grabar=False,
    ),
)
POR_ID = {a.id: a for a in CATALOGO}


def _validar(p: Parametro, valor: Any, raiz: Path) -> Any:
    if p.tipo == "texto":
        if not isinstance(valor, str):
            raise ParametroInvalido(f"«{p.etiqueta}» debe ser texto")
        limpio = " ".join(valor.split())
        if not limpio:
            raise ParametroInvalido(f"«{p.etiqueta}» está vacía")
        if len(limpio) > PREGUNTA_MAXIMA:
            raise ParametroInvalido(f"«{p.etiqueta}» pasa de {PREGUNTA_MAXIMA} caracteres")
        if any(ord(c) < 32 for c in limpio):
            raise ParametroInvalido(f"«{p.etiqueta}» tiene caracteres de control")
        return limpio
    if p.tipo == "entero":
        if isinstance(valor, bool) or not isinstance(valor, int):
            if isinstance(valor, str) and valor.strip().isdigit():
                valor = int(valor)
            else:
                raise ParametroInvalido(f"«{p.etiqueta}» debe ser un número entero")
        if not p.minimo <= valor <= p.maximo:
            raise ParametroInvalido(f"«{p.etiqueta}» debe estar entre {p.minimo} y {p.maximo}")
        return valor
    if p.tipo == "opcion":
        if valor not in p.opciones:
            raise ParametroInvalido(f"«{p.etiqueta}» debe ser una de: {', '.join(p.opciones)}")
        return valor
    if p.tipo == "carpeta":
        return _validar_wiki(valor, raiz)
    raise ParametroInvalido(f"Tipo de parámetro desconocido: {p.tipo}")


def _validar_wiki(valor: Any, raiz: Path) -> str:
    if not isinstance(valor, str):
        raise ParametroInvalido("La carpeta del wiki debe ser texto")
    try:
        relativa = normalizar(valor)
    except ArchivoNoPermitido as error:
        raise ParametroInvalido(f"Carpeta del wiki no válida: {error}") from None
    partes = relativa.split("/")
    if len(partes) != 3 or partes[:2] != ["data", "wiki"]:
        raise ParametroInvalido("El wiki debe ser una carpeta dentro de data/wiki/")
    if (raiz / "data" / "wiki").resolve() not in (raiz / relativa).resolve().parents:
        raise ParametroInvalido("El wiki queda fuera de data/wiki/")
    return relativa


def validar(accion: Accion, crudos: Any, raiz: Path) -> dict[str, Any]:
    """Parámetros normalizados de una acción, o ParametroInvalido."""
    if crudos is None:
        crudos = {}
    if not isinstance(crudos, dict):
        raise ParametroInvalido("Los parámetros deben ser un objeto")
    desconocidos = sorted(set(crudos) - {p.nombre for p in accion.parametros})
    if desconocidos:
        raise ParametroInvalido(f"Parámetros no admitidos: {', '.join(desconocidos)}")
    return {
        p.nombre: _validar(p, crudos.get(p.nombre, p.por_defecto), raiz) for p in accion.parametros
    }


def _citar(texto: str) -> str:
    if '"' not in texto:
        return f'"{texto}"'
    return "'" + texto.replace("'", "''") + "'"


def _en_windows() -> bool:
    return sys.platform == "win32"


def comando_equivalente(accion: Accion, v: dict[str, Any]) -> str | None:
    """La orden de consola que hace lo mismo; solo se muestra, nunca se ejecuta."""
    wiki = v.get("wiki", WIKI_DEMO)
    arnes = "uv run python -m wikillm.arnes"
    comandos = {
        "git_wiki": f"git -C {wiki} log --oneline --decorate",
        "metricas": "uv run python -m wikillm.eval metricas "
        "--respuestas results/piloto-1/respuestas.jsonl",
        "validar_banco": "uv run python -m wikillm.eval validar-banco",
        "verificar": "uv run python scripts/verificar_demo.py",
        "reiniciar_wiki": r".\scripts\preparar_demo.ps1"
        if _en_windows()
        else f"rm -rf {WIKI_DEMO} && cp -r {WIKI_BASE} {WIKI_DEMO}",
    }
    if accion.id in comandos:
        return comandos[accion.id]
    if accion.id == "comparar":
        return f"{arnes} comparar {_citar(v['pregunta'])} --wiki {wiki}"
    if accion.id in ("ingerir", "estimar_ingesta"):
        extra = " --estimar" if accion.id == "estimar_ingesta" else ""
        return f"uv run python -m wikillm.wiki ingerir --paso {v['paso']} --wiki {wiki}{extra}"
    if accion.id == "estimar_corrida":
        return f"{arnes} correr {' '.join(_argumentos_de_la_estimacion(v['alcance']))}"
    return None


def _argumentos_de_la_estimacion(alcance: str) -> list[str]:
    base = ["--corrida", "demo-estimar", "--estado-minimo", "borrador"]
    if alcance == "piloto":
        base += ["--pasos", PASOS_DEL_PILOTO, "--tipos", TIPOS_DEL_PILOTO]
    return [*base, "--estimar"]


def comando_de_subproceso(accion_id: str, v: dict[str, Any], python: str) -> list[str]:
    comandos = {
        "git_wiki": ["git", "-c", "core.quotepath=false", "-C", v.get("wiki", WIKI_DEMO)]
        + ["log", "--oneline", "--decorate"],
        "metricas": [python, "-m", "wikillm.eval", "metricas"]
        + ["--respuestas", "results/piloto-1/respuestas.jsonl"],
        "validar_banco": [python, "-m", "wikillm.eval", "validar-banco"],
        "verificar": [python, "scripts/verificar_demo.py"],
    }
    if accion_id not in comandos:
        raise AccionDesconocida(accion_id)
    return comandos[accion_id]


class GastoDeSesion:
    """Dólares de las llamadas al modelo desde que arrancó el panel, con un tope."""

    def __init__(self, tope_usd: float) -> None:
        self.tope = tope_usd
        self._total = 0.0
        self._cerrojo = threading.Lock()

    def sumar(self, usd: float) -> None:
        with self._cerrojo:
            self._total += usd

    @property
    def total(self) -> float:
        return self._total

    @property
    def agotado(self) -> bool:
        return self._total >= self.tope


class EscritorDeLineas:
    """Archivo de texto que entrega cada línea completa que se le escribe (para ``stderr``)."""

    def __init__(self, destino: Callable[[str], None]) -> None:
        self._destino = destino
        self._pendiente = ""

    def write(self, texto: str) -> int:
        *completas, self._pendiente = re.split(r"[\r\n]", self._pendiente + texto)
        for linea in completas:
            self._entregar(linea)
        return len(texto)

    def _entregar(self, linea: str) -> None:
        if linea.strip() and not LINEA_DE_PROGRESO.search(linea):
            self._destino(linea.rstrip())

    def flush(self) -> None:
        pass

    def cerrar(self) -> None:
        pendiente, self._pendiente = self._pendiente, ""
        self._entregar(pendiente)


def correr_subproceso(
    comando: list[str], emitir: Emitir, *, cwd: Path, limite: float = TIEMPO_MAXIMO_DE_SUBPROCESO
) -> int:
    """Ejecuta una orden fija y transmite su salida (``stdout`` y ``stderr``) línea a línea."""
    entorno = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1"}
    proceso = subprocess.Popen(  # noqa: S603 - la orden sale del catálogo, no de la página
        comando,
        cwd=cwd,
        env=entorno,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    vigilante = threading.Timer(limite, proceso.kill)
    vigilante.daemon = True
    vigilante.start()
    try:
        assert proceso.stdout is not None
        for linea in proceso.stdout:
            emitir({"t": "linea", "texto": linea.rstrip("\r\n")})
        return proceso.wait()
    finally:
        vigilante.cancel()


class FabricaDeBrazos:
    """Construye los brazos reales reutilizando el índice del RAG entre preguntas.

    Cargar el modelo de embeddings tarda varios segundos; se hace una vez y el índice se vuelve
    a poner en cero en cada comparación, como si fuera una corrida nueva.
    """

    def __init__(self) -> None:
        self._indice: Any = None
        self._clave: tuple[str, ...] | None = None
        self._cerrojo = threading.Lock()

    @property
    def listo(self) -> bool:
        return self._indice is not None

    def indice(self, ajustes: Settings, argumentos: argparse.Namespace) -> Any:
        clave = (
            str(argumentos.gold),
            str(getattr(argumentos, "chroma", "")),
            ajustes.embedding_model,
            ajustes.embedding_device,
        )
        with self._cerrojo:
            if self._indice is None or self._clave != clave:
                self._indice = crear_indice_rag(ajustes, argumentos)
                self._clave = clave
            return self._indice

    def calentar(self, ajustes: Settings) -> Any:
        argumentos = argparse.Namespace(
            gold=Path("data/gold"), chroma=Path("data/chroma"), corrida="demo"
        )
        return self.indice(ajustes, argumentos)

    def reiniciar(self) -> None:
        if self._indice is not None:
            self._indice.reiniciar()

    def __call__(
        self, modelo: ClienteModelo, ajustes: Settings, argumentos: argparse.Namespace
    ) -> list[Brazo]:
        indice = self.indice(ajustes, argumentos)
        indice.reiniciar()
        return armar_brazos(modelo, ajustes, argumentos, indice)


def _modelo_observado(ajustes: Settings, ruta: Path, emitir: Emitir) -> ClienteModelo:
    return ClienteObservado(ajustes, emitir=emitir, ruta_registro=ruta)


def _quitar_solo_lectura(funcion: Callable[[str], object], ruta: str, _: BaseException) -> None:
    os.chmod(ruta, stat.S_IWRITE)  # los objetos de Git son de solo lectura en Windows
    funcion(ruta)


class Ejecutor:
    """Valida y ejecuta las acciones del catálogo dentro de la raíz del repositorio."""

    def __init__(
        self,
        raiz: Path,
        gasto: GastoDeSesion,
        *,
        brazos: Callable[..., list[Brazo]] | None = None,
        modelo: Callable[[Settings, Path, Emitir], ClienteModelo] = _modelo_observado,
        arnes: Callable[..., int] = principal_arnes,
        wiki: Callable[..., int] = principal_wiki,
        python: str = sys.executable,
        ahora: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.raiz = raiz
        self.gasto = gasto
        self._brazos = brazos if brazos is not None else FabricaDeBrazos()
        self._modelo = modelo
        self._arnes = arnes
        self._wiki = wiki
        self._python = python
        self._ahora = ahora

    @property
    def rag_listo(self) -> bool:
        return bool(getattr(self._brazos, "listo", False))

    # --- validación -------------------------------------------------------------------------
    def preparar(
        self, accion_id: Any, crudos: Any, confirmo: bool
    ) -> tuple[Accion, dict[str, Any]]:
        accion = POR_ID.get(accion_id) if isinstance(accion_id, str) else None
        if accion is None:
            raise AccionDesconocida(f"La acción {accion_id!r} no existe")
        valores = validar(accion, crudos, self.raiz)
        if (accion.gasta or accion.destructiva) and not confirmo:
            motivo = "borra el estado actual" if accion.destructiva else "gasta saldo"
            raise ConfirmacionRequerida(f"«{accion.titulo}» {motivo}: falta la confirmación")
        if accion.gasta and self.gasto.agotado:
            raise TopeDeSesion(
                f"El gasto de la sesión llegó al tope ({self.gasto.tope:.2f} USD): "
                "las acciones que llaman al modelo están bloqueadas. Reinicia el panel."
            )
        return accion, valores

    def parametros_grabados(self, accion: Accion, valores: dict[str, Any]) -> dict[str, Any]:
        """Parámetros con el estado del wiki al lanzar: una reproducción elige por ellos."""
        if accion.id == "comparar":
            estado = datos.estado_del_wiki(self.raiz, valores["wiki"])
            return {**valores, "paso_wiki": estado["ingeridos"]}
        return dict(valores)

    # --- ejecución --------------------------------------------------------------------------
    def funcion(self, accion: Accion, valores: dict[str, Any]) -> Callable[[Emitir], int]:
        def correr(emitir: Emitir) -> int:
            comando = comando_equivalente(accion, valores)
            if comando:
                emitir({"t": "linea", "canal": "comando", "texto": comando})
            if accion.id in ("git_wiki", "metricas", "validar_banco", "verificar"):
                return correr_subproceso(
                    comando_de_subproceso(accion.id, valores, self._python),
                    emitir,
                    cwd=self.raiz,
                )
            return getattr(self, f"_{accion.id}")(valores, emitir)

        return correr

    def _en_proceso(
        self, principal: Callable[..., int], argv: list[str], emitir: Emitir, **kw: Any
    ) -> int:
        def salida(texto: str) -> None:
            for linea in texto.splitlines() or [""]:
                emitir({"t": "linea", "texto": linea})

        errores = EscritorDeLineas(lambda t: emitir({"t": "linea", "canal": "error", "texto": t}))
        try:
            with contextlib.redirect_stderr(errores):  # type: ignore[type-var]
                return principal(argv, salida=salida, **kw)
        finally:
            errores.cerrar()

    def _calentar(self, valores: dict[str, Any], emitir: Emitir) -> int:
        calentar = getattr(self._brazos, "calentar", None)
        if calentar is None:
            emitir({"t": "linea", "texto": "No hay índice que cargar."})
            return 0
        ajustes = load_settings()
        if self.rag_listo:
            # Without this the button reports a 0.0 s "load", which reads like a failure.
            indice = calentar(ajustes)
            emitir(
                {
                    "t": "linea",
                    "texto": "El índice del RAG ya estaba cargado en memoria: "
                    f"{indice.total_fragmentos} fragmentos.",
                }
            )
            return 0
        emitir(
            {
                "t": "linea",
                "texto": f"Cargando el modelo de embeddings ({ajustes.embedding_model}) "
                f"en {ajustes.embedding_device}…",
            }
        )
        inicio = time.perf_counter()
        indice = calentar(ajustes)
        emitir(
            {
                "t": "linea",
                "texto": f"Índice del RAG listo: {indice.total_fragmentos} fragmentos "
                f"({time.perf_counter() - inicio:.1f} s).",
            }
        )
        return 0

    def _comparar(self, valores: dict[str, Any], emitir: Emitir) -> int:
        argv = ["comparar", "--wiki", valores["wiki"], "--", valores["pregunta"]]
        codigo = self._en_proceso(
            self._arnes,
            argv,
            emitir,
            crear_brazos=self._brazos,
            crear_modelo=lambda ajustes, ruta: self._modelo(ajustes, ruta, emitir),
        )
        if codigo == 0:
            resolutor = crear_resolutor(Path("data/gold"), Path("data/gold/spans.jsonl"))
            resultado = datos.resultado_de_comparacion(self.raiz, resolutor)
            if resultado is not None:
                emitir({"t": "resultado", "tipo": "comparacion", "datos": resultado})
        return codigo

    def _ingerir(self, valores: dict[str, Any], emitir: Emitir) -> int:
        antes = datos.estado_del_wiki(self.raiz, valores["wiki"])["ingeridos"]
        argv = ["ingerir", "--paso", str(valores["paso"]), "--wiki", valores["wiki"]]
        codigo = self._en_proceso(
            self._wiki,
            argv,
            emitir,
            crear_modelo=lambda ajustes: self._modelo(ajustes, REGISTRO_DEL_MODELO, emitir),
        )
        if codigo == 0:
            despues = datos.estado_del_wiki(self.raiz, valores["wiki"])["ingeridos"]
            entrada = datos.ultima_ingesta(self.raiz, valores["wiki"])
            if despues > antes and entrada is not None:
                emitir(
                    {
                        "t": "resultado",
                        "tipo": "ingesta",
                        "datos": {
                            **entrada,
                            "papers_nuevos": despues - antes,
                            "ingeridos": despues,
                        },
                    }
                )
        return codigo

    def _estimar_ingesta(self, valores: dict[str, Any], emitir: Emitir) -> int:
        argv = ["ingerir", "--paso", str(valores["paso"]), "--wiki", valores["wiki"], "--estimar"]
        return self._en_proceso(self._wiki, argv, emitir)

    def _estimar_corrida(self, valores: dict[str, Any], emitir: Emitir) -> int:
        argv = ["correr", *_argumentos_de_la_estimacion(valores["alcance"])]
        return self._en_proceso(self._arnes, argv, emitir)

    def _reiniciar_wiki(self, valores: dict[str, Any], emitir: Emitir) -> int:
        base, destino = self.raiz / WIKI_BASE, self.raiz / WIKI_DEMO
        if not base.is_dir():
            emitir(
                {
                    "t": "linea",
                    "canal": "error",
                    "texto": f"Falta {WIKI_BASE} (el wiki de desarrollo con 5 papers).",
                }
            )
            return 1
        emitir({"t": "linea", "texto": f"Copiando {WIKI_BASE} → {WIKI_DEMO}…"})
        if destino.exists():
            shutil.rmtree(destino, onexc=_quitar_solo_lectura)
        shutil.copytree(base, destino)
        evidencia = self.raiz / EVIDENCIA_DE_LA_DEMO
        if evidencia.exists():
            (self.raiz / ENSAYOS).mkdir(parents=True, exist_ok=True)
            apartada = ENSAYOS / f"comparaciones-{self._ahora():%Y%m%d-%H%M%S}.jsonl"
            shutil.move(evidencia, self.raiz / apartada)
            emitir({"t": "linea", "texto": f"Evidencia anterior apartada en {apartada.as_posix()}"})
        if hasattr(self._brazos, "reiniciar"):
            self._brazos.reiniciar()
        ingeridos = datos.estado_del_wiki(self.raiz, WIKI_DEMO)["ingeridos"]
        emitir(
            {
                "t": "linea",
                "texto": f"Wiki de la demostración listo en {WIKI_DEMO}: "
                f"{ingeridos} papers ingeridos (paso {ingeridos}).",
            }
        )
        return 0
