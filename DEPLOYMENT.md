# 🚀 部署指南

本指南將幫助您將 RequestPayment 系統部署到 Hugging Face Spaces 或本地環境。

## 📋 目錄

- [Hugging Face Spaces 部署](#hugging-face-spaces-部署)
- [本地 Docker 部署](#本地-docker-部署)
- [本地開發環境](#本地開發環境)
- [測試部署](#測試部署)
- [故障排除](#故障排除)

## 🌐 Hugging Face Spaces 部署

### 步驟 1: 準備 GitHub 倉庫

1. **Fork 此專案**到您的 GitHub 帳戶
2. **確保以下文件存在**：
   - `Dockerfile`
   - `requirements.txt`
   - `README.md` (包含 Hugging Face Spaces 配置)

### 步驟 2: 創建 Hugging Face Space

1. 訪問 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 點擊 "Create new Space"
3. 選擇以下配置：
   - **Owner**: 您的用戶名
   - **Space name**: `request-payment` (或您喜歡的名稱)
   - **Space SDK**: `Docker`
   - **License**: 選擇適當的授權
   - **Visibility**: 選擇 Public 或 Private

### 步驟 3: 連接 GitHub 倉庫

1. 在 Space 設置中，選擇 "Repository" 標籤
2. 選擇您 fork 的 GitHub 倉庫
3. 點擊 "Save"

### 步驟 4: 自動部署

Hugging Face Spaces 會自動：
- 檢測 `Dockerfile`
- 構建 Docker 映像
- 啟動應用程式
- 提供公開 URL

### 步驟 5: 驗證部署

部署完成後，訪問您的 Space URL 並檢查：
- 主頁是否正常載入
- API 文檔是否可訪問 (`/docs`)
- 健康檢查是否通過 (`/health`)

## 🐳 本地 Docker 部署

### 前置需求

- Docker 20.10+
- Docker Compose 2.0+

### 步驟 1: 克隆專案

```bash
git clone <your-repository-url>
cd RequestPayment
```

### 步驟 2: 構建並啟動

使用 Docker Compose (推薦)：
```bash
docker-compose up --build
```

或使用 Docker 直接啟動：
```bash
# 構建映像
docker build -t request-payment .

# 運行容器
docker run -p 7860:7860 request-payment
```

### 步驟 3: 驗證部署

訪問 http://localhost:7860 檢查應用程式是否正常運行。

## 💻 本地開發環境

### 前置需求

- Python 3.11+
- pip

### 步驟 1: 設置虛擬環境

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 步驟 2: 安裝依賴

```bash
pip install -r requirements.txt
```

### 步驟 3: 啟動應用程式

```bash
python -m src.request_payment.main
```

### 步驟 4: 驗證

訪問 http://localhost:7860 檢查應用程式。

## 🧪 測試部署

### 自動測試

運行測試腳本：
```bash
python test_docker.py
```

### 手動測試

1. **健康檢查**：
   ```bash
   curl http://localhost:7860/health
   ```

2. **API 文檔**：
   訪問 http://localhost:7860/docs

3. **主頁**：
   訪問 http://localhost:7860

4. **API 端點**：
   ```bash
   curl http://localhost:7860/api/v1/
   ```

## 🔧 故障排除

### 常見問題

#### 1. 端口被佔用

**錯誤**: `Address already in use`

**解決方案**：
```bash
# 查找佔用端口的進程
lsof -i :7860

# 終止進程
kill -9 <PID>

# 或使用不同端口
docker run -p 7861:7860 request-payment
```

#### 2. Docker 構建失敗

**錯誤**: `Failed to build Docker image`

**解決方案**：
```bash
# 清理 Docker 緩存
docker system prune -a

# 重新構建
docker build --no-cache -t request-payment .
```

#### 3. 依賴安裝失敗

**錯誤**: `pip install failed`

**解決方案**：
```bash
# 更新 pip
pip install --upgrade pip

# 清理緩存
pip cache purge

# 重新安裝
pip install -r requirements.txt
```

#### 4. 權限問題

**錯誤**: `Permission denied`

**解決方案**：
```bash
# 修復文件權限
chmod +x src/request_payment/main.py

# 或使用 sudo (不推薦)
sudo docker run -p 7860:7860 request-payment
```

### 日誌檢查

#### Docker 日誌
```bash
# 查看容器日誌
docker logs <container_id>

# 實時日誌
docker logs -f <container_id>
```

#### 應用程式日誌
應用程式使用 Loguru 進行日誌記錄，日誌會輸出到控制台。

### 環境變數

可以通過環境變數配置應用程式：

```bash
# 設置環境變數
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export HOST=0.0.0.0
export PORT=7860

# 啟動應用程式
python -m src.request_payment.main
```

## 📊 監控和維護

### 健康檢查

應用程式提供健康檢查端點：
- URL: `/health`
- 方法: GET
- 響應: JSON 格式的健康狀態

### 性能監控

- 使用 Docker stats 監控容器資源使用
- 檢查應用程式日誌
- 監控 API 響應時間

### 備份

定期備份重要數據：
- 上傳的文件 (`uploads/` 目錄)
- 配置文件
- 日誌文件

## 🔒 安全考慮

### 生產環境

1. **更改默認密鑰**：
   - 修改 `SECRET_KEY` 環境變數
   - 使用強密碼生成器

2. **限制 CORS**：
   - 配置允許的域名
   - 移除 `*` 通配符

3. **文件上傳安全**：
   - 驗證文件類型
   - 限制文件大小
   - 掃描惡意文件

4. **HTTPS**：
   - 在生產環境使用 HTTPS
   - 配置 SSL 證書

### 防火牆配置

確保只開放必要的端口：
- 7860: 應用程式端口
- 22: SSH (如果需要)

## 📞 支援

如果遇到問題：

1. 檢查 [故障排除](#故障排除) 部分
2. 查看應用程式日誌
3. 在 GitHub 上創建 Issue
4. 聯繫開發團隊

---

**注意**: 本指南適用於 RequestPayment 系統的 Docker 版本。確保您使用的是正確的版本和配置。 