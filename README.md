# 甲狀腺功能智慧判讀系統

一個基於 RAG（檢索增強生成）技術的甲狀腺功能檢驗判讀系統，協助醫療人員和患者解讀甲狀腺功能檢查結果，提供鑑別診斷和臨床建議。

## 功能特色

- 🔬 **智慧檢驗判讀**：自動解析甲狀腺功能檢驗數值
- 🤖 **RAG 技術支援**：結合醫學文獻知識庫提供準確建議
- 📊 **視覺化呈現**：圖表化顯示檢驗結果與正常範圍比較
- 🏥 **鑑別診斷**：提供可能的診斷和機率評估
- 💊 **治療建議**：根據診斷結果給予初步治療方向
- 📚 **知識庫擴充**：支援上傳醫學文獻持續優化系統

## 系統架構

- **前端介面**：Streamlit Web UI
- **API 服務**：FastAPI RESTful API
- **RAG 引擎**：LangChain + ChromaDB
- **AI 模型**：OpenAI GPT-4

## 安裝指南

### 1. 環境需求

- Python 3.8+
- pip 或 conda

### 2. 安裝步驟

```bash
# 克隆專案
git clone https://github.com/yourusername/thyroidfunction.git
cd thyroidfunction

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 檔案，填入您的 OpenAI API Key
```

### 3. 啟動應用程式

#### Streamlit UI
```bash
streamlit run app.py
```

#### FastAPI 服務
```bash
uvicorn api:app --reload
```

## 使用說明

### Web 介面使用

1. 開啟瀏覽器訪問 `http://localhost:8501`
2. 在側邊欄輸入檢驗數值
3. 選擇相關症狀（選填）
4. 點擊「開始分析」獲得診斷結果
5. 可下載診斷報告

### API 使用範例

```python
import requests

# 分析檢驗結果
response = requests.post(
    "http://localhost:8000/analyze",
    json={
        "lab_data": {
            "TSH": 5.2,
            "Free_T4": 0.9,
            "Anti_TPO": 150
        },
        "symptoms": ["疲勞", "體重增加", "怕冷"]
    }
)

result = response.json()
print(f"診斷：{result['thyroid_status']}")
print(f"建議：{result['recommendations']}")
```

## 檢驗項目說明

| 檢驗項目 | 正常範圍 | 單位 |
|---------|---------|------|
| TSH | 0.4-4.0 | μIU/mL |
| Free T4 | 0.8-1.8 | ng/dL |
| Free T3 | 2.3-4.2 | pg/mL |
| Anti-TPO | < 34 | IU/mL |
| Anti-Tg | < 115 | IU/mL |
| TSH受體抗體 | < 1.75 | IU/L |

## 注意事項

⚠️ **重要提醒**：
- 本系統僅供參考，不能取代專業醫療診斷
- 診斷結果應由合格醫師確認
- 治療決策須考慮完整臨床資訊

## 開發團隊

- 專案負責人：[您的名字]
- 開發日期：2024

## 授權

本專案採用 MIT 授權條款 