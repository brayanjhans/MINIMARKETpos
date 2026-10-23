# Instala el Minimarket POS en una PC nueva y carga la base de datos de traspaso/minimarket.sql.
# Uso (desde la carpeta del proyecto):  powershell -ExecutionPolicy Bypass -File traspaso\instalar.ps1
# Se puede volver a ejecutar: lo que ya está hecho se salta.

# "Continue": los avisos que pip/npm escriben en stderr no deben cortar el script; se revisa $LASTEXITCODE
$ErrorActionPreference = "Continue"
$raiz = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $raiz "backend"
$frontend = Join-Path $raiz "frontend"
$respaldo = Join-Path $PSScriptRoot "minimarket.sql"

function Paso($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Falla($texto) { Write-Host "ERROR: $texto" -ForegroundColor Red; exit 1 }

# --- 1. Programas necesarios ---------------------------------------------------------------------
Paso "Revisando programas"
$python = $null
foreach ($c in @("py -3.14", "python")) {
    try {
        $v = Invoke-Expression "$c --version" 2>$null
        if ($LASTEXITCODE -ne 0) { continue }
        if ($v -match "3\.1[4-9]") { $python = $c; break }
    } catch {}
}
if (-not $python) { Falla "Falta Python 3.14 (https://www.python.org/downloads/). Marca 'Add python.exe to PATH'." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Falla "Falta Node.js 24 (https://nodejs.org)." }
$mysql = (Get-Command mysql -ErrorAction SilentlyContinue).Source
if (-not $mysql) {
    $mysql = Get-ChildItem "C:\Program Files\MySQL" -Recurse -Filter mysql.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $mysql) { Falla "Falta MySQL 8.0 (https://dev.mysql.com/downloads/installer/). Instala 'MySQL Server'." }
Write-Host "Python: $python | Node: $(node -v) | MySQL: $mysql"

# --- 2. Backend -------------------------------------------------------------------------------------
Paso "Backend: entorno de Python y dependencias"
Set-Location $backend
if (-not (Test-Path ".venv\Scripts\python.exe")) { Invoke-Expression "$python -m venv .venv" }
& .venv\Scripts\python.exe -m pip install --upgrade pip --quiet
& .venv\Scripts\pip.exe install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { Falla "No se pudieron instalar las dependencias del backend" }

if (-not (Test-Path ".env")) {
    Paso "Backend: creando .env con una clave secreta nueva"
    $clave = & .venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(64))"
    (Get-Content ".env.example") -replace "^JWT_SECRET=.*", "JWT_SECRET=$clave" -replace "^CORS_ORIGENES=.*", "CORS_ORIGENES=http://localhost:3010" |
        Set-Content ".env" -Encoding UTF8
    Write-Host "Si traes el .env de la otra PC, reemplázalo: así siguen valiendo los QR de los tickets impresos." -ForegroundColor Yellow
} else {
    Write-Host ".env ya existe: se deja como está"
}

# --- 3. Base de datos -------------------------------------------------------------------------------
Paso "Base de datos MySQL"
$seguro = Read-Host "Contraseña de root de MySQL" -AsSecureString
$env:MYSQL_PWD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($seguro))
try {
    $tablas = & $mysql -u root -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='minimarket'"
    if ($LASTEXITCODE -ne 0) { Falla "No se pudo entrar a MySQL como root (¿contraseña correcta? ¿servicio MySQL encendido?)" }
    $importar = $true
    if ([int]$tablas -gt 0) {
        $r = Read-Host "La base 'minimarket' ya tiene $tablas tablas. ¿Reemplazarla por la del respaldo? (s/N)"
        $importar = $r -match "^[sS]"
    }
    & $mysql -u root -e "CREATE DATABASE IF NOT EXISTS minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci; CREATE USER IF NOT EXISTS 'minimarket'@'localhost' IDENTIFIED BY 'minimarket'; GRANT ALL ON minimarket.* TO 'minimarket'@'localhost'; GRANT ALL ON minimarket_test.* TO 'minimarket'@'localhost'; SET PERSIST log_bin_trust_function_creators = 1;"
    if ($LASTEXITCODE -ne 0) { Falla "No se pudo crear la base o el usuario" }
    if ($importar) {
        & $mysql -u root -e "DROP DATABASE minimarket; CREATE DATABASE minimarket CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
        $ruta = $respaldo -replace "\\", "/"
        & $mysql -u root --default-character-set=utf8mb4 minimarket -e "source $ruta"
        if ($LASTEXITCODE -ne 0) { Falla "No se pudo importar $respaldo" }
        Write-Host "Respaldo importado"
    }
} finally {
    Remove-Item Env:MYSQL_PWD -ErrorAction SilentlyContinue
}
& .venv\Scripts\alembic.exe upgrade head
if ($LASTEXITCODE -ne 0) { Falla "Las migraciones fallaron" }

# --- 4. Frontend ------------------------------------------------------------------------------------
Paso "Frontend: dependencias"
Set-Location $frontend
npm ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { Falla "No se pudieron instalar las dependencias del frontend" }

Set-Location $raiz
Paso "Listo"
Write-Host "Para encender el sistema:  powershell -ExecutionPolicy Bypass -File traspaso\iniciar.ps1"
Write-Host "Luego abre http://localhost:3010  (usuario admin / Admin123*)"
