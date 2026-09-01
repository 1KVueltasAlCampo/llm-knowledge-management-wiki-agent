# Entrega final

`informe.tex` — documento de entrega, en el formato de presentación de documentos de la
Facultad Barberi (Universidad Icesi). Una columna, tamaño carta, márgenes de 2,54 cm,
citación APA.

## Compilar

```
pdflatex informe.tex && pdflatex informe.tex
```

Dos pasadas: la primera resuelve las referencias cruzadas de tablas y figuras, la segunda
las escribe. El `informe.pdf` versionado corresponde a la última compilación.

Dependencias en Debian/Ubuntu:

```
sudo apt install texlive-latex-recommended texlive-latex-extra \
                 texlive-fonts-recommended texlive-lang-spanish texlive-pictures
```

## Contenido

El documento se compone a partir de `definicion_problema.md`, `cronograma.md` y
`cumplimiento_rubrica.md` de la raíz del repositorio, más `docs/estado-del-arte.md` para
la revisión de literatura. Esos archivos siguen siendo la fuente; el `.tex` es la versión
con formato de entrega.

El cronograma de `cronograma.md` está representado como diagrama de Gantt en la Figura 1,
dibujado en TikZ dentro del propio `.tex` (sin dependencias externas ni imágenes).

## Estado

Las secciones III y IV son *Resultados esperados* y *Discusión* de riesgos previstos: el
proyecto está en fase de fundamentación y no hay mediciones todavía. Cuando existan,
sustituyen el contenido de III sin alterar la estructura.
