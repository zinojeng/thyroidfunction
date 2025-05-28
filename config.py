"""
甲狀腺功能判讀系統配置檔
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI 設定
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 模型設定
    EMBEDDING_MODEL = "text-embedding-ada-002"
    LLM_MODEL = "gpt-4-turbo-preview"
    
    # 向量資料庫設定
    VECTOR_DB_PATH = "./data/vector_db"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # 文檔路徑
    DEFAULT_DOCUMENT_PATH = "./Thyroid function.md"
    
    # 甲狀腺檢驗正常值範圍
    NORMAL_RANGES = {
        "TSH": {"min": 0.4, "max": 4.0, "unit": "μIU/mL"},
        "Free_T4": {"min": 0.8, "max": 1.8, "unit": "ng/dL"},
        "Free_T3": {"min": 2.3, "max": 4.2, "unit": "pg/mL"},
        "Anti_TPO": {"max": 34, "unit": "IU/mL"},
        "Anti_Tg": {"max": 115, "unit": "IU/mL"},
        "TSH_receptor_Ab": {"max": 1.75, "unit": "IU/L"}
    }
    
    # 應用程式設定
    APP_NAME = "甲狀腺功能智慧判讀系統"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "基於醫學文獻的甲狀腺功能檢驗判讀系統" 