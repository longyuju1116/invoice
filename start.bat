@echo off
chcp 65001 >nul

echo 🚀 啟動 RequestPayment 系統...

REM 檢查 Python 版本
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，請先安裝 Python 3.11+
    pause
    exit /b 1
)

echo ✅ Python 檢查通過

REM 檢查虛擬環境
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  建議在虛擬環境中運行
    echo    創建虛擬環境: python -m venv venv
    echo    啟動虛擬環境: venv\Scripts\activate
)

REM 檢查依賴
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo 📦 安裝依賴...
    pip install -r requirements.txt
)

REM 創建必要的目錄
echo 📁 創建必要的目錄...
if not exist "uploads\images" mkdir "uploads\images"
if not exist "uploads\temp" mkdir "uploads\temp"
if not exist "static" mkdir "static"

REM 啟動應用程式
echo 🌐 啟動應用程式...
echo    主頁: http://localhost:7860
echo    API 文檔: http://localhost:7860/docs
echo    健康檢查: http://localhost:7860/health
echo.
echo 按 Ctrl+C 停止應用程式
echo.

python -m src.request_payment.main

pause 