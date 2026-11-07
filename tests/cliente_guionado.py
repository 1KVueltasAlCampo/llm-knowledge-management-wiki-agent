"""Cliente HTTP falso que devuelve respuestas guionadas, para probar el wiki sin red ni saldo."""

from types import SimpleNamespace

from test_responder import AJUSTES
from wikillm.common.modelo import ClienteModelo


class ClienteGuionado:
    """Devuelve los textos en orden y guarda cada solicitud; falla si se acaba el guion."""

    def __init__(self, textos):
        self.textos = list(textos)
        self.solicitudes = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **argumentos):
        self.solicitudes.append(argumentos)
        if len(self.solicitudes) > len(self.textos):
            raise AssertionError("El modelo recibió más llamadas que respuestas guionadas")
        uso = SimpleNamespace(
            prompt_tokens=1000,
            prompt_cache_hit_tokens=0,
            prompt_cache_miss_tokens=1000,
            completion_tokens=100,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=0),
        )
        mensaje = SimpleNamespace(content=self.textos[len(self.solicitudes) - 1])
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)], usage=uso)


def modelo_guionado(tmp_path, textos):
    http = ClienteGuionado(textos)
    modelo = ClienteModelo(AJUSTES, ruta_registro=tmp_path / "llamadas.jsonl", cliente=http)
    return modelo, http
