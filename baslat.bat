@echo off
chcp 65001 >nul
setlocal

set "APP_DIR=C:\Users\omerg\Desktop\zikirhalkasi"
set "APP_FILE=%APP_DIR%\main.py"

if not exist "%APP_FILE%" (
    echo [HATA] main.py bulunamadi: "%APP_FILE%"
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

if exist "%APP_DIR%\.venv\Scripts\python.exe" (
    set "PY_EXE=%APP_DIR%\.venv\Scripts\python.exe"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [HATA] Sistemde Python bulunamadi.
        pause
        exit /b 1
    )
    set "PY_EXE=python"
)

echo [BILGI] Streamlit baslatiliyor: "%APP_FILE%"
"%PY_EXE%" -m streamlit run "%APP_FILE%" --browser.gatherUsageStats=false
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [UYARI] Streamlit hata kodu ile kapandi: %EXIT_CODE%
    pause
)

endlocal