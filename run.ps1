# Launcher en PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Plataforma Web de Gestión Documental con Control de Versiones" -ForegroundColor Yellow
Write-Host "  Iniciando servidor local en http://127.0.0.1:8000 ..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Start-Process "http://127.0.0.1:8000"
$pythonPath = "C:\Users\jorai\AppData\Local\Programs\Python\Python314\python.exe"
if (Test-Path $pythonPath) {
    & $pythonPath -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
} else {
    python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
}
