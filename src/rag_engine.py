"""
RAG (Retrieval-Augmented Generation) 引擎
整合文獻解析和向量檢索
"""
import os
from typing import List, Dict, Any
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.schema import Document
from config import Config
from src.document_parser import MarkdownDocumentParser
from src.literature_based_analyzer import LiteratureBasedAnalyzer

class RAGEngine:
    def __init__(self):
        """初始化 RAG 引擎"""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=Config.OPENAI_API_KEY,
            model=Config.EMBEDDING_MODEL
        )
        self.vector_store = None
        self.document_parser = MarkdownDocumentParser()
        self.literature_analyzer = LiteratureBasedAnalyzer()
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """初始化向量資料庫"""
        if os.path.exists(Config.VECTOR_DB_PATH):
            self.vector_store = Chroma(
                persist_directory=Config.VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
        else:
            self.vector_store = Chroma(
                persist_directory=Config.VECTOR_DB_PATH,
                embedding_function=self.embeddings
            )
            self._load_initial_documents()
    
    def _load_initial_documents(self):
        """載入初始醫學文件"""
        # 檢查是否有 Markdown 文檔
        doc_paths = [
            "./Thyroid function.md",
            "./data/documents/Thyroid function.md"
        ]
        
        for doc_path in doc_paths:
            if os.path.exists(doc_path):
                # 解析文檔
                parsed_data = self.document_parser.parse_markdown_document(doc_path)
                
                # 保存解析後的知識庫
                kb_path = "./data/thyroid_knowledge_base.json"
                os.makedirs("./data", exist_ok=True)
                self.document_parser.save_parsed_knowledge(parsed_data, kb_path)
                
                # 載入到文獻分析器
                self.literature_analyzer.load_knowledge_base(kb_path)
                
                # 創建文檔用於向量檢索
                documents = self._create_documents_from_parsed_data(parsed_data)
                
                # 分割文件
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=Config.CHUNK_SIZE,
                    chunk_overlap=Config.CHUNK_OVERLAP,
                    separators=["\n\n", "\n", "。", "，", " ", ""]
                )
                
                split_documents = text_splitter.split_documents(documents)
                
                # 加入向量資料庫
                self.vector_store.add_documents(split_documents)
                self.vector_store.persist()
                
                print(f"成功載入文檔: {doc_path}")
                break
    
    def _create_documents_from_parsed_data(self, parsed_data: Dict[str, Any]) -> List[Document]:
        """從解析的數據創建文檔"""
        documents = []
        
        # 為每個模式創建詳細文檔
        for pattern in parsed_data.get("patterns", []):
            # 主要模式文檔
            content = f"模式: {pattern['tsh_status']}, {pattern['ft4_status']}"
            documents.append(Document(
                page_content=content,
                metadata={"pattern": pattern}
            ))
        
        # 解析臨床指南
        guidelines = parsed_data["guidelines"]
        for guideline in guidelines:
            documents.append(Document(
                page_content=f"指南: {guideline['condition']}",
                metadata={"guideline": guideline}
            ))
        
        # 解析問答對
        qa_pairs = parsed_data["qa_pairs"]
        for qa in qa_pairs:
            documents.append(Document(
                page_content=f"Q: {qa['question']}\nA: {qa['answer']}",
                metadata={"qa_pair": qa}
            ))
        
        return documents
    
    def _create_thyroid_guidelines(self) -> List[Document]:
        """創建甲狀腺診斷指南文件"""
        guidelines = [
            Document(
                page_content="""
                甲狀腺功能異常的診斷與鑑別
                
                1. 甲狀腺功能亢進 (Hyperthyroidism)
                診斷標準：
                - TSH < 0.4 μIU/mL (降低)
                - Free T4 > 1.8 ng/dL 和/或 Free T3 > 4.2 pg/mL (升高)
                
                常見原因：
                - Graves' disease（瀰漫性毒性甲狀腺 