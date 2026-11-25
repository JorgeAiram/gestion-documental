@echo off
title Plataforma de Gestion Documental con Control de Versiones
echo ========================================================
echo   Plataforma Web de Gestion Documental (DocuControl)
echo   Iniciando servidor local en http://127.0.0.1:8000 ...
echo ========================================================

start "" "http://127.0.0.1:8000"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
if %errorlevel% neq 0 (
    echo.
    echo Intentando con ruta absoluta de Python...
    "C:\Users\jorai\AppData\Local\Programs\Python\Python314\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
)
pause
