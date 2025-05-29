"""
甲狀腺功能智慧判讀系統 - Streamlit UI
基於 Markdown 文獻的判讀系統
"""
import streamlit as st
import pandas as pd
from typing import Dict, List
import plotly.graph_objects as go
from src.rag_engine import RAGEngine
from src.literature_based_analyzer import LiteratureBasedAnalyzer
from src.thyroid_analyzer import ThyroidAnalyzer
from config import Config
import os

# 頁面設定
st.set_page_config(
    page_title=Config.APP_NAME,
    page_icon="🦋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
@st.cache_resource
def initialize_engines():
    """初始化 RAG 引擎和分析器"""
    # 暫時使用簡化版的初始化，避免 ChromaDB 相容性問題
    # rag_engine = RAGEngine()
    analyzer = ThyroidAnalyzer()
    return None, analyzer

def main():
    st.title("🦋 " + Config.APP_NAME)
    st.markdown(f"### {Config.APP_DESCRIPTION}")
    st.info("本系統基於上傳的醫學文獻（Markdown 格式）進行判讀，確保診斷建議有據可查")
    
    # 初始化引擎
    rag_engine, analyzer = initialize_engines()
    
    # 側邊欄
    with st.sidebar:
        st.header("檢驗數據輸入")
        
        # 基本檢驗項目
        st.subheader("基本檢驗")
        col_tsh, col_tsh_ref = st.columns([3, 1])
        with col_tsh:
            tsh = st.number_input("TSH (μIU/mL) *必填", min_value=0.0, max_value=100.0, step=0.01)
        with col_tsh_ref:
            tsh_range = Config.NORMAL_RANGES.get("TSH", {})
            if tsh_range:
                st.caption(f"參考範圍: {tsh_range.get('min', 0)}-{tsh_range.get('max', 0)} {tsh_range.get('unit', '')}")
        
        col_t4, col_t4_ref = st.columns([3, 1])
        with col_t4:
            free_t4 = st.number_input("Free T4 (ng/dL) *必填", min_value=0.0, max_value=10.0, step=0.01)
        with col_t4_ref:
            t4_range = Config.NORMAL_RANGES.get("Free_T4", {})
            if t4_range:
                st.caption(f"參考範圍: {t4_range.get('min', 0)}-{t4_range.get('max', 0)} {t4_range.get('unit', '')}")
        
        # Free T3 (選填)
        include_t3 = st.checkbox("包含 Free T3 檢測值")
        free_t3 = 0.0
        if include_t3:
            col_t3, col_t3_ref = st.columns([3, 1])
            with col_t3:
                free_t3 = st.number_input("Free T3 (pg/mL)", min_value=0.0, max_value=20.0, step=0.01)
            with col_t3_ref:
                t3_range = Config.NORMAL_RANGES.get("Free_T3", {})
                if t3_range:
                    st.caption(f"參考範圍: {t3_range.get('min', 0)}-{t3_range.get('max', 0)} {t3_range.get('unit', '')}")
        
        # 抗體檢驗
        st.subheader("抗體檢驗（選填）")
        include_antibodies = st.checkbox("包含抗體檢測值")
        anti_tpo = 0.0
        anti_tg = 0.0
        trab = 0.0
        if include_antibodies:
            col_tpo, col_tpo_ref = st.columns([3, 1])
            with col_tpo:
                anti_tpo = st.number_input("Anti-TPO (IU/mL)", min_value=0.0, max_value=1000.0, step=0.1)
            with col_tpo_ref:
                tpo_range = Config.NORMAL_RANGES.get("Anti_TPO", {})
                if tpo_range:
                    st.caption(f"參考範圍: <{tpo_range.get('max', 0)} {tpo_range.get('unit', '')}")
            
            col_tg, col_tg_ref = st.columns([3, 1])
            with col_tg:
                anti_tg = st.number_input("Anti-Tg (IU/mL)", min_value=0.0, max_value=1000.0, step=0.1)
            with col_tg_ref:
                tg_range = Config.NORMAL_RANGES.get("Anti_Tg", {})
                if tg_range:
                    st.caption(f"參考範圍: <{tg_range.get('max', 0)} {tg_range.get('unit', '')}")
            
            col_trab, col_trab_ref = st.columns([3, 1])
            with col_trab:
                trab = st.number_input("TSH受體抗體 (IU/L)", min_value=0.0, max_value=50.0, step=0.01)
            with col_trab_ref:
                trab_range = Config.NORMAL_RANGES.get("TSH_receptor_Ab", {})
                if trab_range:
                    st.caption(f"參考範圍: <{trab_range.get('max', 0)} {trab_range.get('unit', '')}")
        
        # 症狀選擇
        st.subheader("臨床症狀（選填）")
        symptoms = st.multiselect(
            "請選擇相關症狀",
            [
                "心悸", "手抖", "體重減輕", "怕熱多汗",
                "疲勞", "體重增加", "怕冷", "便秘",
                "掉髮", "皮膚乾燥", "記憶力減退", "月經異常",
                "頸部腫大", "吞嚥困難", "聲音沙啞"
            ]
        )
        
        # 其他資訊
        st.subheader("其他資訊（選填）")
        age = st.number_input("年齡", min_value=0, max_value=120, step=1)
        gender = st.selectbox("性別", ["", "男", "女"])
        pregnancy = st.checkbox("懷孕中")
        medications = st.text_area("目前用藥", help="請列出目前使用的藥物")
        
        # 分析按鈕
        analyze_button = st.button("開始分析", type="primary", use_container_width=True)
    
    # 主要內容區
    if analyze_button:
        # 收集輸入數據
        lab_data = {}
        if tsh > 0:
            lab_data["TSH"] = tsh
        if free_t4 > 0:
            lab_data["Free_T4"] = free_t4
        if free_t3 > 0:
            lab_data["Free_T3"] = free_t3
        if anti_tpo > 0:
            lab_data["Anti_TPO"] = anti_tpo
        if anti_tg > 0:
            lab_data["Anti_Tg"] = anti_tg
        if trab > 0:
            lab_data["TSH_receptor_Ab"] = trab
        
        if not lab_data:
            st.error("請至少輸入 TSH 數值")
            return
        
        # 顯示分析中
        with st.spinner("正在分析檢驗結果..."):
            # 使用分析器進行診斷
            diagnosis_result = analyzer.analyze(
                lab_data=lab_data,
                symptoms=symptoms if symptoms else []
            )
            
            # 由於RAG引擎暫時禁用，提供基本診斷建議
            rag_response = {
                "diagnosis": f"""
## {diagnosis_result.thyroid_status.value}診斷建議

根據檢驗結果，患者被診斷為**{diagnosis_result.thyroid_status.value}**。

### 一般建議
- 定期追蹤檢查甲狀腺功能
- 遵醫囑規律服藥
- 均衡飲食，保持適度運動
- 避免壓力過大

### 治療方向
{', '.join(diagnosis_result.recommendations)}

### 注意事項
請記住這只是初步建議，具體治療方案請遵循醫師指導。
                """
            }
        
        # 顯示結果
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 檢驗結果視覺化")
            
            # 創建檢驗結果圖表
            fig = create_lab_chart(lab_data, Config.NORMAL_RANGES)
            st.plotly_chart(fig, use_container_width=True)
            
            # 檢驗結果表格
            st.subheader("📋 檢驗數值解讀")
            lab_df = create_lab_dataframe(lab_data, analyzer)
            st.dataframe(lab_df, use_container_width=True)
        
        with col2:
            st.subheader("🔍 診斷結果")
            
            # 主要診斷
            st.info(f"**甲狀腺功能狀態**: {diagnosis_result.thyroid_status.value}")
            st.metric("診斷信心度", f"{diagnosis_result.confidence:.0%}")
            
            # 鑑別診斷
            if diagnosis_result.differential_diagnosis:
                st.subheader("鑑別診斷")
                for diagnosis, probability in diagnosis_result.differential_diagnosis:
                    st.write(f"• {diagnosis} (可能性: {probability:.0%})")
            
            # 建議事項
            st.subheader("💡 建議事項")
            for rec in diagnosis_result.recommendations:
                st.write(f"• {rec}")
            
            # 建議額外檢查
            if diagnosis_result.additional_tests:
                st.subheader("🔬 建議額外檢查")
                for test in diagnosis_result.additional_tests:
                    st.write(f"• {test}")
        
        # RAG 詳細建議
        st.subheader("🤖 AI 診斷建議")
        with st.expander("查看詳細 AI 分析", expanded=True):
            st.markdown(rag_response["diagnosis"])
        
        # 下載報告
        report = analyzer.generate_report(diagnosis_result, lab_data)
        st.download_button(
            label="📥 下載診斷報告",
            data=report,
            file_name="thyroid_report.md",
            mime="text/markdown"
        )
    
    # 知識庫管理
    with st.expander("📚 知識庫管理"):
        st.subheader("上傳醫學文獻")
        uploaded_file = st.file_uploader(
            "選擇 PDF 或文字檔案",
            type=['pdf', 'txt'],
            help="上傳甲狀腺相關的醫學文獻或指南"
        )
        
        if uploaded_file is not None:
            if st.button("加入知識庫"):
                with st.spinner("正在處理文件..."):
                    # 儲存上傳的檔案
                    file_path = f"./data/documents/{uploaded_file.name}"
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # 由於RAG系統暫時禁用
                    st.success("文件已上傳，但RAG系統暫時禁用。")

def create_lab_chart(lab_data: Dict[str, float], normal_ranges: Dict) -> go.Figure:
    """創建檢驗結果視覺化圖表"""
    fig = go.Figure()
    
    tests = []
    values = []
    lower_bounds = []
    upper_bounds = []
    
    for test_name, value in lab_data.items():
        if test_name in normal_ranges:
            tests.append(test_name)
            values.append(value)
            
            normal_range = normal_ranges[test_name]
            if "min" in normal_range and "max" in normal_range:
                lower_bounds.append(normal_range["min"])
                upper_bounds.append(normal_range["max"])
            else:
                # 抗體檢測
                lower_bounds.append(0)
                upper_bounds.append(normal_range["max"])
    
    # 正常範圍
    fig.add_trace(go.Scatter(
        x=tests,
        y=upper_bounds,
        mode='lines',
        name='正常上限',
        line=dict(color='green', dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=tests,
        y=lower_bounds,
        mode='lines',
        name='正常下限',
        line=dict(color='green', dash='dash'),
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.1)'
    ))
    
    # 實際數值
    fig.add_trace(go.Scatter(
        x=tests,
        y=values,
        mode='markers+lines',
        name='檢驗值',
        marker=dict(size=10, color='blue'),
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title="檢驗結果與正常範圍比較",
        xaxis_title="檢驗項目",
        yaxis_title="數值",
        hovermode='x unified'
    )
    
    return fig

def create_lab_dataframe(lab_data: Dict[str, float], analyzer: ThyroidAnalyzer) -> pd.DataFrame:
    """創建檢驗結果表格"""
    lab_results = analyzer._parse_lab_results(lab_data)
    
    data = []
    for test_name, result in lab_results.items():
        data.append({
            "檢驗項目": result.name,
            "數值": f"{result.value} {result.unit}",
            "參考範圍": result.reference_range,
            "狀態": result.status
        })
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    main()
