#!/bin/bash

# RequestPayment 系統啟動腳本

echo "🚀 啟動 RequestPayment 系統..."

# 檢查 Python 版本
python_version=$(python3 --version 2>&1 | grep -o '3\.[0-9]\+')
if [[ $python_version < "3.11" ]]; then
    echo "❌ 需要 Python 3.11 或更高版本，當前版本: $python_version"
    exit 1
fi

echo "✅ Python 版本檢查通過: $python_version"

# 檢查虛擬環境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  建議在虛擬環境中運行"
    echo "   創建虛擬環境: python3 -m venv venv"
    echo "   啟動虛擬環境: source venv/bin/activate"
fi

# 檢查依賴
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 安裝依賴..."
    pip3 install -r requirements.txt
fi

# 創建必要的目錄
echo "📁 創建必要的目錄..."
mkdir -p uploads/images uploads/temp static

# 啟動應用程式
echo "🌐 啟動應用程式..."
echo "   主頁: http://localhost:7860"
echo "   API 文檔: http://localhost:7860/docs"
echo "   健康檢查: http://localhost:7860/health"
echo ""
echo "按 Ctrl+C 停止應用程式"
echo ""

python3 -m src.request_payment.main 