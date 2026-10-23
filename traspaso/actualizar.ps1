# AL LLEGAR a esta PC: baja de GitHub el código y la base de datos que dejó la otra PC.
# Uso:  powershell -ExecutionPolicy Bypass -File traspaso\actualizar.ps1
# OJO: reemplaza la base de datos de ESTA PC por la del respaldo (lo que no se guardó aquí se pierde).
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
Paso "Bajando los cambios de GitHub"
if (git status --porcelain) {
    Write-Host "Hay cambios sin guardar en esta PC:" -ForegroundColor Yellow
    git status --short
    Falla "Guárdalos primero (guardar.ps1) o descártalos, para no mezclar trabajos de dos PCs"
}
git pull --ff-only
if ($LASTEXITCODE -ne 0) { Falla "No se pudo bajar de GitHub" }

Paso "Cargando la base de datos del respaldo"
Write-Host "Se reemplazará la base 'minimarket' de esta PC por la del respaldo." -ForegroundColor Yellow
Write-Host "Apaga el sistema (cierra las ventanas del backend y frontend) antes de seguir."
if ((Read-Host "¿Continuar? (s/N)") -notmatch "^[sS]") { Falla "Cancelado: el código se actualizó, la base NO" }
$mysql = Buscar "mysql"
$env:MYSQL_PWD = "minimarket"
$ruta = $respaldo -replace "\\", "/"
& $mysql -u minimarket --default-character-set=utf8mb4 minimarket -e "source $ruta"
$codigo = $LASTEXITCODE
Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
if ($codigo -ne 0) { Falla "No se pudo importar la base" }

Paso "Actualizando dependencias y migraciones"
Set-Location (Join-Path $raiz "backend")
& .venv\Scripts\pip.exe install -r requirements.txt --quiet
& .venv\Scripts\alembic.exe upgrade head
if ($LASTEXITCODE -ne 0) { Falla "Las migraciones fallaron" }
Set-Location (Join-Path $raiz "frontend")
npm ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { Falla "No se pudieron instalar las dependencias del frontend" }

Set-Location $raiz
Write-Host "`nListo: esta PC tiene el código y los datos de la otra. Enciende con traspaso\iniciar.ps1" -ForegroundColor Green
