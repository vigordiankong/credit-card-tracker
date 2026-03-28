# 💳 卡優惠 - 台灣信用卡優惠追蹤器

自動追蹤中信、國泰、玉山、台新、永豐、LINE Bank 最新信用卡優惠，部署為 PWA 可安裝到手機桌面！

## ✨ 功能特色

- 🏦 追蹤 6 家銀行：中信 / 國泰 / 玉山 / 台新 / 永豐 / LINE Bank
- 🔍 搜尋 + 篩選（銀行、類別）
- ❤️ 收藏喜愛的優惠
- ⚖️ 銀行比較頁面
- 📱 PWA - 可安裝到手機主畫面
- ⏰ GitHub Actions 每天自動爬取更新
- 🆓 完全免費（GitHub Pages + GitHub Actions）

## 🚀 快速開始

### Step 1：Fork 這個 Repo

點選右上角 **Fork** 按鈕，複製到你的 GitHub 帳號。

### Step 2：啟用 GitHub Pages

1. 進入你 Fork 的 Repo
2. 點選 **Settings** → **Pages**
3. Source 選擇 **GitHub Actions**
4. 儲存

### Step 3：啟用 GitHub Actions 寫入權限

1. **Settings** → **Actions** → **General**
2. 找到 **Workflow permissions**
3. 選擇 **Read and write permissions**
4. 點 **Save**

### Step 4：觸發第一次部署

1. 點選 **Actions** 標籤
2. 找到 "🚀 部署到 GitHub Pages" workflow
3. 點 **Run workflow** → **Run workflow**
4. 等待完成後，就能用網址存取 App！

**你的 App 網址會是：**
`https://你的GitHub帳號.github.io/credit-card-tracker/`

### Step 5：安裝到手機

- **iPhone**：Safari 打開網址 → 分享 → 加入主畫面
- **Android**：Chrome 打開網址 → 選單 ⋮ → 新增至主畫面

---

## 🛠️ 本機開發

### 環境需求
- Python 3.10+
- Node.js（可選，若要修改前端）

### 安裝

```bash
# 安裝 Python 套件
pip install -r requirements.txt

# 安裝 Playwright 瀏覽器
playwright install chromium
```

### 執行爬蟲

```bash
# 完整爬取（需要網路）
python main.py

# 只產生初始示範資料（不爬網路，用於測試）
python main.py --init
```

### 在本機預覽前端

```bash
# 方法一：使用 Python 內建 HTTP Server
cd frontend
python -m http.server 8080
# 瀏覽器開啟 http://localhost:8080

# 方法二：修改 frontend/index.html 中的 dataUrl 為 '../data/offers.json'
# 再用上面的指令啟動
```

---

## 📁 專案結構

```
credit-card-tracker/
│
├── scrapers/                 # 爬蟲模組
│   ├── __init__.py
│   ├── base.py               # 基底爬蟲類別
│   ├── ctbc.py               # 中國信託
│   ├── cathay.py             # 國泰世華
│   ├── esun.py               # 玉山銀行
│   ├── taishin.py            # 台新銀行
│   ├── sinopac.py            # 永豐銀行
│   └── linebank.py           # LINE Bank
│
├── data/
│   └── offers.json           # 爬取後的優惠資料
│
├── frontend/                 # PWA 前端
│   ├── index.html            # 主頁面（含所有 CSS/JS）
│   ├── manifest.json         # PWA 設定
│   └── sw.js                 # Service Worker（離線支援）
│
├── .github/
│   └── workflows/
│       ├── scrape.yml        # 每日自動爬取
│       └── deploy.yml        # 自動部署到 GitHub Pages
│
├── main.py                   # 主程式入口
├── requirements.txt          # Python 套件清單
└── README.md
```

---

## ⚙️ 自動排程說明

`scrape.yml` 設定為每天 UTC 00:00（台灣時間 AM 8:00）自動執行：

```yaml
schedule:
  - cron: '0 0 * * *'   # 每天台灣時間 AM 8:00
```

若要修改排程時間，編輯 `.github/workflows/scrape.yml` 的 cron 表達式。

---

## 🔧 新增更多銀行

1. 在 `scrapers/` 新增一個 `.py` 檔案（參考 `ctbc.py`）
2. 繼承 `BaseScraper` 類別
3. 實作 `_scrape_page()` 方法
4. 在 `scrapers/__init__.py` 加入新爬蟲
5. 若網站無法爬取，補充 `_get_fallback_data()` 備用資料

---

## ⚠️ 注意事項

- 銀行網站可能更新結構導致爬蟲失效，此時會自動使用備用示範資料
- 優惠資料以各銀行官網為準，本工具僅供參考
- 請勿過度頻繁爬取，避免對銀行伺服器造成負擔

---

## 📄 License

MIT License - 歡迎自由使用、修改、分享
