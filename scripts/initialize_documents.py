"""
初始化文檔腳本
將 Markdown 文檔載入系統
"""
import os
import shutil
from pathlib import Path

def initialize_documents():
    """初始化文檔結構"""
    # 創建必要的目錄
    directories = [
        "./data",
        "./data/documents",
        "./data/vector_db"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # 複製 Thyroid function.md 到正確位置
    source_files = [
        "Thyroid function.md",
        "./Thyroid function.md"
    ]
    
    destination = "./data/documents/Thyroid function.md"
    
    for source in source_files:
        if os.path.exists(source):
            shutil.copy2(source, destination)
            print(f"已複製 {source} 到 {destination}")
            break
    
    # 刪除 RTF 檔案
    rtf_files = [
        "異常甲狀腺功能檢測的解讀與評估.md",
        "./異常甲狀腺功能檢測的解讀與評估.md"
    ]
    
    for rtf_file in rtf_files:
        if os.path.exists(rtf_file) and rtf_file.endswith('.md'):
            # 檢查是否為 RTF 格式
            with open(rtf_file, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if 'rtf1' in first_line:
                    os.remove(rtf_file)
                    print(f"已刪除 RTF 檔案：{rtf_file}")

if __name__ == "__main__":
    initialize_documents() 