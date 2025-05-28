"""
甲狀腺功能判讀 API 服務
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import uvicorn
from src.rag_engine import RAGEngine
from src.thyroid_analyzer import ThyroidAnalyzer
from config import Config

app = FastAPI(
    title=Config.APP_NAME + " API",
    version=Config.APP_VERSION,
    description="甲狀腺功能智慧判讀 API 服務"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化引擎
rag_engine = RAGEngine()
analyzer = ThyroidAnalyzer()

# 資料模型
class LabData(BaseModel):
    """檢驗數據模型"""
    TSH: Optional[float] = Field(None, description="TSH 數值 (μIU/mL)")
    Free_T4: Optional[float] = Field(None, description="Free T4 數值 (ng/dL)")
    Free_T3: Optional[float] = Field(None, description="Free T3 數值 (pg/mL)")
    Anti_TPO: Optional[float] = Field(None, description="Anti-TPO 數值 (IU/mL)")
    Anti_Tg: Optional[float] = Field(None, description="Anti-Tg 數值 (IU/mL)")
    TSH_receptor_Ab: Optional[float] = Field(None, description="TSH受體抗體 (IU/L)")

class AnalysisRequest(BaseModel):
    """分析請求模型"""
    lab_data: LabData
    symptoms: Optional[List[str]] = Field(None, description="症狀列表")
    age: Optional[int] = Field(None, description="年齡")
    gender: Optional[str] = Field(None, description="性別")
    pregnancy: Optional[bool] = Field(False, description="是否懷孕")
    medications: Optional[List[str]] = Field(None, description="目前用藥")
    question: Optional[str] = Field(None, description="特定問題")

class AnalysisResponse(BaseModel):
    """分析回應模型"""
    thyroid_status: str
    confidence: float
    differential_diagnosis: List[Dict[str, float]]
    recommendations: List[str]
    additional_tests: List[str]
    ai_diagnosis: str
    report: str

@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "status": "active"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_thyroid_function(request: AnalysisRequest):
    """
    分析甲狀腺功能
    
    接收檢驗數據和臨床資訊，返回診斷建議
    """
    try:
        # 轉換檢驗數據
        lab_data = {k: v for k, v in request.lab_data.dict().items() if v is not None}
        
        if not lab_data:
            raise HTTPException(status_code=400, detail="請提供至少一項檢驗數據")
        
        # 使用分析器進行診斷
        diagnosis_result = analyzer.analyze(
            lab_data=lab_data,
            symptoms=request.symptoms
        )
        
        # 使用 RAG 獲取 AI 診斷
        question = request.question or f"患者檢驗結果顯示{diagnosis_result.thyroid_status.value}，請提供詳細的診斷和治療建議。"
        rag_response = rag_engine.query(question, lab_data)
        
        # 生成報告
        report = analyzer.generate_report(diagnosis_result, lab_data)
        
        # 構建回應
        response = AnalysisResponse(
            thyroid_status=diagnosis_result.thyroid_status.value,
            confidence=diagnosis_result.confidence,
            differential_diagnosis=[
                {"diagnosis": diag, "probability": prob}
                for diag, prob in diagnosis_result.differential_diagnosis
            ],
            recommendations=diagnosis_result.recommendations,
            additional_tests=diagnosis_result.additional_tests,
            ai_diagnosis=rag_response["diagnosis"],
            report=report
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...)):
    """
    上傳醫學文件到知識庫
    
    支援 PDF 和文字檔案格式
    """
    try:
        # 檢查檔案類型
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="只支援 PDF 和 TXT 格式")
        
        # 儲存檔案
        file_path = f"./data/documents/{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 加入 RAG 系統
        doc_type = "pdf" if file.filename.endswith('.pdf') else "txt"
        result = rag_engine.add_document(file_path, doc_type)
        
        return {"message": result, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/normal_ranges")
async def get_normal_ranges():
    """獲取檢驗項目的正常值範圍"""
    return Config.NORMAL_RANGES

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "service": "thyroid-analyzer"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 