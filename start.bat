@echo off
title Memorarq - Inicializacao
echo ==========================================
echo         INICIANDO MEMORARQ
echo ==========================================

:: 1. Verifica e cria o ambiente virtual isolado (venv)
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [SETUP] Primeira execucao detectada. Preparando o sistema...
    echo [SETUP] Criando ambiente virtual interno...
    python -m venv venv
    
    echo [SETUP] Ativando ambiente...
    call venv\Scripts\activate.bat
    
    echo [SETUP] Instalando dependencias - Isso pode demorar alguns minutos...
    python -m pip install --upgrade pip >nul
    pip install -r requirements.txt
) ELSE (
    call venv\Scripts\activate.bat
)

:: 2. Instala e verifica os binarios do sistema automaticamente
echo.
echo [SETUP] Verificando dependencias de OCR - Poppler e Tesseract...
python backend\setup_binaries.py

:: 3. Muda para o diretorio do backend onde esta a API
cd backend

:: 4. Inicia o Servidor FastAPI
echo [SISTEMA] Inicializando o Servidor da API e da Interface...
python -m uvicorn app:app --host 127.0.0.1 --port 8000

:: 5. Abre o navegador automaticamente
echo.
echo [SISTEMA] Abrindo o Memorarq no navegador...
start http://127.0.0.1:8000

pause