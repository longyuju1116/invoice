---
title: 請款單系統
emoji: 📋
colorFrom: blue
colorTo: purple
sdk: docker
app_file: Dockerfile
pinned: false
---

# RequestPayment - 請款單系統 (Docker 版本)

一個基於 **FastAPI** 的現代化請款單系統，使用 Docker 容器化部署，支援 Hugging Face Spaces。

## 🚀 功能特色

- **現代化 FastAPI 後端**：基於 FastAPI 0.104+，提供高性能 API
- **Docker 容器化**：完整的容器化部署方案
- **請款單管理**：創建、預覽、下載 PDF 請款單
- **文件上傳支援**：存摺影本圖片上傳功能
- **RESTful API**：完整的 API 文檔和測試界面
- **響應式前端**：現代化的 Web 界面

## 🛠 技術棧

- **後端框架**：FastAPI 0.104+
- **服務器**：Uvicorn
- **容器化**：Docker
- **資料驗證**：Pydantic
- **檔案處理**：本地文件系統
- **PDF 生成**：ReportLab
- **日誌系統**：Loguru

## 📦 快速開始

### 在 Hugging Face Spaces 部署

1. **Fork 此專案**到您的 GitHub 帳戶

2. **在 Hugging Face Spaces 創建新的 Space**
   - 選擇 **"Docker"** 類型
   - 連接您的 GitHub 倉庫
   - 設定 Python 版本為 3.11

3. **自動部署**
   - Hugging Face Spaces 會自動構建 Docker 映像並啟動應用
   - 訪問您的 Space URL 即可使用

### 本地 Docker 部署

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd RequestPayment
   ```

2. **使用 Docker Compose 啟動**
   ```bash
   docker-compose up --build
   ```

3. **或使用 Docker 直接啟動**
   ```bash
   docker build -t request-payment .
   docker run -p 7860:7860 request-payment
   ```

4. **訪問應用**
   - 應用主頁: http://localhost:7860
   - API 文檔: http://localhost:7860/docs
   - 健康檢查: http://localhost:7860/health

## 📋 使用說明

### 1. 填寫基本資訊
- **申請日期**：使用民國年格式 (例：111.11.11)
- **受款人**：請款人姓名
- **付款方式**：現金、匯款、轉捐款、預支、其他
- **請款單位**：輔導活動執委會、行政財務執委會、資訊媒體執委會、其他

### 2. 新增請款明細
- **專案類型**：A.會議、B.活動、C.志工培訓、D.學校訪談、E.專案補助、F.其他
- **費用類型**：1.交通費、2.場地租借、3.餐費、4.文宣、5.電話費、6.補助、7.志工津貼、8.設備器材、9.雜支
- **執行內容**：詳細說明執行內容
- **金額**：請款金額

### 3. 上傳存摺影本
- 選擇匯款或預支付款方式時需要上傳存摺影本
- 支援 JPG、PNG、GIF 格式

### 4. 生成 PDF
- 使用 API 端點創建請款單
- 系統會生成請款單並提供下載連結

## 🏗 專案結構

```
RequestPayment/
├── src/request_payment/           # 主要應用程式碼
│   ├── api/v1/                   # API 路由
│   ├── core/                     # 核心配置和異常處理
│   ├── models/                   # 資料模型和 Schemas
│   ├── services/                 # 業務邏輯服務層
│   └── utils/                    # 工具函數
├── static/                       # 靜態文件 (HTML, CSS, JS)
├── uploads/                      # 文件上傳目錄
├── Dockerfile                    # Docker 映像配置
├── docker-compose.yml           # Docker Compose 配置
├── requirements.txt             # Python 依賴
└── README.md                    # 專案說明
```

## 📁 檔案管理

### 支持的檔案類型
- **圖片**: .jpg, .jpeg, .png, .gif
- **文檔**: .pdf

### 存儲結構
```
uploads/
├── images/          # 用戶上傳的圖片
└── temp/           # 臨時文件
```

### 檔案大小限制
- 圖片檔案: 最大 2MB
- 一般檔案: 最大 5MB

## 🔧 配置說明

系統使用環境變數進行配置，主要配置項：

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `HOST` | 應用主機 | `0.0.0.0` |
| `PORT` | 應用埠號 | `7860` |
| `ENVIRONMENT` | 運行環境 | `production` |
| `LOG_LEVEL` | 日誌級別 | `INFO` |

## 🌟 主要特性

### 1. Docker 容器化
- 完整的容器化部署
- 環境一致性保證
- 易於擴展和維護

### 2. FastAPI 後端
- 高性能異步 API
- 自動生成 API 文檔
- 完整的類型提示

### 3. 文件處理
- 安全的文件上傳
- 文件類型驗證
- 存摺影本處理

### 4. PDF 生成
- 專業的請款單格式
- 中文字體支援
- 自動分頁處理

## 🔒 安全性

- 文件上傳驗證
- 輸入驗證
- 安全的檔案處理
- CORS 配置

## 🐳 Docker 部署

### 構建映像
```bash
docker build -t request-payment .
```

### 運行容器
```bash
docker run -p 7860:7860 request-payment
```

### 使用 Docker Compose
```bash
docker-compose up --build
```

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個專案！

## 📄 授權

這個專案使用 MIT 授權。

## 📞 支援

如有問題或建議，請在 GitHub 上創建 Issue。

---

**注意**: 這個版本使用 Docker 容器化部署，確保在不同環境下的一致性，特別適合 Hugging Face Spaces 等雲端平台部署。
