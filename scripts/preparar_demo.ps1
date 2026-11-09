# Deja listo el estado inicial de la demostración: el wiki en el paso 5.
#
# Copia limpia del wiki de desarrollo (data/wiki/dev2, con sus 5 papers y sus copias paso-1 a
# paso-5) en data/wiki/demo, que es el que modifica la ingesta en vivo. Si ya había una
# demostración, aparta sus comparaciones en results/demo/ensayos/ para que la evidencia nueva
# empiece vacía. No llama al modelo ni gasta saldo.
#
# Uso (desde la raíz del repositorio):  .\scripts\preparar_demo.ps1

$ErrorActionPreference = "Stop"

if (-not (Test-Path "data/wiki/dev2")) {
    throw "Falta data/wiki/dev2 (el wiki de desarrollo con 5 papers). Se construye con: " +
          "uv run python -m wikillm.wiki ingerir --paso 5 --wiki data/wiki/dev2"
}
if (Test-Path "data/wiki/demo") { Remove-Item "data/wiki/demo" -Recurse -Force }
Copy-Item "data/wiki/dev2" "data/wiki/demo" -Recurse

$evidencia = "results/demo/comparaciones.jsonl"
if (Test-Path $evidencia) {
    New-Item -ItemType Directory -Force "results/demo/ensayos" | Out-Null
    $marca = Get-Date -Format "yyyyMMdd-HHmmss"
    Move-Item $evidencia "results/demo/ensayos/comparaciones-$marca.jsonl"
}

$ingeridos = (Get-Content "data/wiki/demo/estado.json" -Raw | ConvertFrom-Json).ingeridos.Count
Write-Host "Wiki de la demostracion listo en data/wiki/demo: $ingeridos papers ingeridos (paso $ingeridos)."
