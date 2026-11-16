# Design

## Decisiones

- **Apagado por defecto.** Un brazo nuevo y un parámetro `capas=None` evitan tocar el WikiLLM base:
  con los parámetros por defecto, `INSTRUCCIONES_AGENTE`, `analizar_accion` y el bucle producen lo
  mismo. Una prueba lo comprueba (`test_sin_capas_el_agente_conserva_su_protocolo`).
- **Tercer brazo en la misma corrida, no una corrida aparte.** Así comparte el wiki ya ingerido
  (la ingesta se paga una vez) y ve la misma hora, carga de API y tarifa que los otros brazos. Su
  `ingerir` devuelve costo cero y su lista de papers es la del wiki compartido, de modo que la
  comprobación de estado de la reanudación sigue valiendo.
- **Programas externos, sin dependencias.** `graphify` y `tgrep` se pasan como rutas a ejecutables;
  si faltan o fallan, `ErrorDeCapa` detiene la corrida con un mensaje claro y lo escrito se
  conserva. Los tests usan un ejecutor falso y nunca los invocan.
- **El grafo se reconstruye cuando cambia el paso.** Se copian `pages/` e `index.md` a una carpeta
  de trabajo (`data/grafo/<corrida>`, ignorada por Git) y se ejecuta `graphify update`, que no
  llama a ningún modelo. El índice de tgrep se reconstruye igual con `--force`.
- **Misma configuración que la evaluada.** `graph` sustituye a `search`, `read` acepta
  `slug#Encabezado` y los nombres del grafo (`pages/<slug>.md`), y `grep` no cuenta como lectura,
  devuelve 3 líneas recortadas a 300 caracteres y se rechaza hasta haber leído una página
  (variante `tras_lectura` de la evaluación).
- **Rutas de tgrep.** Solo se normalizan las barras de la ruta, no las del texto: el wiki tiene
  LaTeX y `\geq` no debe volverse `/geq`.

## Riesgos

- **Fidelidad con lo evaluado.** El texto del protocolo se arma igual que en el script de
  evaluación, pero la medición se hizo con 15 papers y pocas preguntas. Conviene repetirla sobre la
  corrida completa antes de sacar conclusiones.
- **Latencia del grafo.** Cada consulta lanza un proceso (≈4 s con el grafo ya construido); el
  tiempo por respuesta del brazo con capas será mayor y se reporta tal cual.
- **Costo.** Un tercer brazo añade respuestas; ver «Impact» del proposal.
