# AL TERMINAR en esta PC: exporta la base de datos y sube TODO (código + base) a GitHub.
# Uso:  powershell -ExecutionPolicy Bypass -File traspaso\guardar.ps1
$ErrorActionPreference = "Continue"
$raiz = Split-Path -Parent $PSScriptRoot
$respaldo = Join-Path $PSScriptRoot "minimarket.sql"
function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Falla($texto) { Write-Host "ERROR: $texto" -ForegroundColor Red; exit 1 }
function Buscar($exe) {
    $ruta = (Get-Command $exe -ErrorAction SilentlyContinue).Source
    if (-not $ruta) {
        $ruta = Get-ChildItem "C:\Program Files\MySQL" -Recurse -Filter "$exe.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $ruta) { Falla "No se encontró $exe (MySQL 8.0)" }
    return $ruta
}

Set-Location $raiz
Paso "Exportando la base de datos minimarket"
$mysqldump = Buscar "mysqldump"
$env:MYSQL_PWD = "minimarket"
& $mysqldump -u minimarket --single-transaction --routines --triggers --no-tablespaces --set-gtid-purged=OFF `
    --default-character-set=utf8mb4 --result-file="$respaldo" minimarket
$codigo = $LASTEXITCODE
Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
if ($codigo -ne 0) { Falla "No se pudo exportar la base (¿MySQL encendido?)" }
Write-Host "Base exportada: $((Get-Item $respaldo).Length / 1KB -as [int]) KB"

Paso "Subiendo a GitHub"
git add -A
git commit -q -m "Traspaso: base de datos y cambios del $(Get-Date -Format 'yyyy-MM-dd HH:mm') en $env:COMPUTERNAME"
git push
if ($LASTEXITCODE -ne 0) { Falla "No se pudo subir a GitHub (¿internet? ¿hay cambios de la otra PC sin bajar? usa actualizar.ps1 primero)" }
Write-Host "`nListo. En la otra PC ejecuta: powershell -ExecutionPolicy Bypass -File traspaso\actualizar.ps1" -ForegroundColor Green
