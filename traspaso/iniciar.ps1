# Enciende el backend (puerto 8010) y el frontend (puerto 3010) en dos ventanas.
# Uso:  powershell -ExecutionPolicy Bypass -File traspaso\iniciar.ps1
$raiz = Split-Path -Parent $PSScriptRoot
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$raiz\backend'; .venv\Scripts\uvicorn app.main:app --port 8010"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$raiz\frontend'; npm run dev"
Write-Host "Encendiendo... en unos segundos abre http://localhost:3010 (usuario admin / Admin123*)"
Write-Host "Para apagar, cierra las dos ventanas."
