#!/usr/bin/env python3
"""
Docker 部署測試腳本
用於驗證應用程式在 Docker 容器中是否正常運行
"""

import requests
import time
import sys
from typing import Dict, Any


def test_health_endpoint(base_url: str) -> bool:
    """測試健康檢查端點"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康檢查通過: {data}")
            return True
        else:
            print(f"❌ 健康檢查失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查錯誤: {e}")
        return False


def test_api_docs(base_url: str) -> bool:
    """測試 API 文檔端點"""
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API 文檔可訪問")
            return True
        else:
            print(f"❌ API 文檔訪問失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 文檔錯誤: {e}")
        return False


def test_main_page(base_url: str) -> bool:
    """測試主頁端點"""
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ 主頁可訪問")
            return True
        else:
            print(f"❌ 主頁訪問失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 主頁錯誤: {e}")
        return False


def test_api_endpoints(base_url: str) -> bool:
    """測試 API 端點"""
    try:
        # 測試 API 路由
        response = requests.get(f"{base_url}/api/v1/", timeout=10)
        if response.status_code == 200:
            print("✅ API 路由可訪問")
            return True
        else:
            print(f"❌ API 路由訪問失敗: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API 路由錯誤: {e}")
        return False


def main():
    """主測試函數"""
    print("🐳 Docker 部署測試開始...")
    print("=" * 50)
    
    # 配置測試 URL
    base_url = "http://localhost:7860"
    
    # 等待應用程式啟動
    print("⏳ 等待應用程式啟動...")
    time.sleep(5)
    
    # 執行測試
    tests = [
        ("健康檢查", lambda: test_health_endpoint(base_url)),
        ("主頁", lambda: test_main_page(base_url)),
        ("API 文檔", lambda: test_api_docs(base_url)),
        ("API 路由", lambda: test_api_endpoints(base_url)),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 測試 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 測試失敗")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！Docker 部署成功！")
        print(f"🌐 應用程式地址: {base_url}")
        print(f"📚 API 文檔: {base_url}/docs")
        return 0
    else:
        print("❌ 部分測試失敗，請檢查應用程式配置")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 