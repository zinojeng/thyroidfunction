"""
醫學文檔解析器
支援 Markdown、PDF、TXT 等格式的文獻解析
"""
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import markdown
from bs4 import BeautifulSoup

@dataclass
class ThyroidPattern:
    """甲狀腺功能模式"""
    pattern_id: str
    tsh_status: str  # 低/正常/高
    ft4_status: str  # 低/正常/高
    ft3_status: Optional[str] = None
    common_causes: List[str] = None
    interfering_factors: List[str] = None
    differential_diagnosis: List[str] = None
    recommendations: List[str] = None
    additional_tests: List[str] = None
    case_examples: List[Dict[str, str]] = None
    notes: Optional[str] = None

@dataclass
class ClinicalGuideline:
    """臨床指南"""
    condition: str
    diagnostic_criteria: Dict[str, Any]
    symptoms: List[str]
    treatment_suggestions: List[str]
    special_considerations: Optional[Dict[str, Any]] = None

class MarkdownDocumentParser:
    def __init__(self):
        """初始化 Markdown 文檔解析器"""
        self.patterns = []
        self.guidelines = []
        self.qa_pairs = []
        
    def parse_markdown_document(self, file_path: str) -> Dict[str, Any]:
        """解析 Markdown 格式的醫學文檔"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 解析 Markdown 結構
        sections = self._extract_sections_from_markdown(content)
        
        # 解析各種模式
        patterns = self._extract_thyroid_patterns_from_markdown(sections)
        
        # 解析問答對
        qa_pairs = self._extract_qa_pairs_from_markdown(sections)
        
        # 提取參考值範圍
        reference_ranges = self._extract_reference_ranges(content)
        
        return {
            "patterns": patterns,
            "qa_pairs": qa_pairs,
            "reference_ranges": reference_ranges,
            "raw_sections": sections
        }
    
    def _extract_sections_from_markdown(self, content: str) -> Dict[str, str]:
        """從 Markdown 內容提取章節"""
        sections = {}
        
        # 分割主要章節
        # 2.2 不同甲狀腺功能檢測模式的解讀與評估
        pattern_section = re.search(
            r'(\*\*2\.2.*?不同甲狀腺功能檢測模式.*?\*\*.*?)(?=\*\*3\.|$)', 
            content, 
            re.DOTALL
        )
        
        if pattern_section:
            pattern_content = pattern_section.group(1)
            
            # 提取各個子模式 (2.2.1 - 2.2.7)
            pattern_matches = re.findall(
                r'(\*\*2\.2\.\d+.*?\*\*.*?)(?=\*\*2\.2\.\d+|\*\*3\.|$)',
                pattern_content,
                re.DOTALL
            )
            
            for i, match in enumerate(pattern_matches):
                sections[f"pattern_{i+1}"] = match
        
        # 提取問答環節
        qa_section = re.search(
            r'(\*\*4.*?問答環節\*\*.*?)(?=\*\*\[重點摘要\]|$)',
            content,
            re.DOTALL
        )
        
        if qa_section:
            sections["qa_section"] = qa_section.group(1)
        
        # 提取總結與建議
        summary_section = re.search(
            r'(\*\*3.*?總結與建議\*\*.*?)(?=\*\*4\.|$)',
            content,
            re.DOTALL
        )
        
        if summary_section:
            sections["summary"] = summary_section.group(1)
        
        return sections
    
    def _extract_thyroid_patterns_from_markdown(self, sections: Dict[str, str]) -> List[ThyroidPattern]:
        """從 Markdown 章節中提取甲狀腺功能模式"""
        patterns = []
        
        # 定義模式映射
        pattern_definitions = {
            "pattern_1": ("低", "高", "2.2.1"),
            "pattern_2": ("低", "正常", "2.2.2"),
            "pattern_3": ("低", "低", "2.2.3"),
            "pattern_4": ("正常", "正常", "2.2.4"),
            "pattern_5": ("高", "低", "2.2.5"),
            "pattern_6": ("高", "正常", "2.2.6"),
            "pattern_7": ("特殊", "特殊", "2.2.7")  # TSH 無法抑制
        }
        
        for pattern_key, (tsh_status, ft4_status, section_num) in pattern_definitions.items():
            if pattern_key in sections:
                pattern = self._parse_pattern_section_markdown(
                    sections[pattern_key],
                    tsh_status,
                    ft4_status,
                    section_num
                )
                patterns.append(pattern)
        
        return patterns
    
    def _parse_pattern_section_markdown(
        self, 
        section_text: str, 
        tsh_status: str, 
        ft4_status: str,
        section_num: str
    ) -> ThyroidPattern:
        """解析單個 Markdown 模式章節"""
        pattern = ThyroidPattern(
            pattern_id=section_num,
            tsh_status=tsh_status,
            ft4_status=ft4_status,
            common_causes=[],
            interfering_factors=[],
            differential_diagnosis=[],
            recommendations=[],
            additional_tests=[],
            case_examples=[]
        )
        
        # 提取標題
        title_match = re.search(r'\*\*2\.2\.\d+\s+(.*?)\*\*', section_text)
        if title_match:
            pattern.notes = title_match.group(1).strip()
        
        # 提取常見原因
        causes_match = re.search(
            r'\*\*常見原因[：:]\*\*(.*?)(?=\*\*|$)', 
            section_text, 
            re.DOTALL
        )
        if causes_match:
            pattern.common_causes = self._extract_list_items_markdown(causes_match.group(1))
        
        # 提取潛在干擾
        interference_match = re.search(
            r'\*\*潛在干擾[：:]\*\*(.*?)(?=\*\*|$)', 
            section_text, 
            re.DOTALL
        )
        if interference_match:
            pattern.interfering_factors = self._extract_nested_items_markdown(interference_match.group(1))
        
        # 提取其他可能性
        other_match = re.search(
            r'\*\*其他可能性[：:]\*\*(.*?)(?=\*\*|$)', 
            section_text, 
            re.DOTALL
        )
        if other_match:
            pattern.differential_diagnosis = self._extract_nested_items_markdown(other_match.group(1))
        
        # 提取藥物影響
        drug_match = re.search(
            r'\*\*藥物影響[：:]\*\*(.*?)(?=\*\*|$)', 
            section_text, 
            re.DOTALL
        )
        if drug_match:
            drugs = self._extract_list_items_markdown(drug_match.group(1))
            pattern.interfering_factors.extend([f"藥物影響: {drug}" for drug in drugs])
        
        # 提取案例
        case_matches = re.findall(
            r'\*\*案例[一二三四五六七八九十\d]+[：:]\*\*(.*?)(?=\*\*案例|_診斷[：:]_|$)',
            section_text,
            re.DOTALL
        )
        
        for case_text in case_matches:
            diagnosis_match = re.search(r'_診斷[：:]_\s*(.*?)(?=\n|$)', case_text)
            if diagnosis_match:
                pattern.case_examples.append({
                    "description": case_text.strip(),
                    "diagnosis": diagnosis_match.group(1).strip()
                })
        
        # 提取評估流程
        eval_match = re.search(
            r'\*\*.*?評估流程[：:]\*\*(.*?)(?=\*\*\d+\.|$)',
            section_text,
            re.DOTALL
        )
        if eval_match:
            pattern.recommendations = self._extract_evaluation_steps(eval_match.group(1))
        
        # 特殊處理 TSH 無法抑制模式
        if section_num == "2.2.7":
            pattern.tsh_status = "無法抑制"
            pattern.ft4_status = "高或正常"
            
            # 提取鑑別診斷流程
            diff_match = re.search(
                r'\*\*鑑別診斷流程[：:]\*\*(.*?)(?=\*\*TSH|$)',
                section_text,
                re.DOTALL
            )
            if diff_match:
                pattern.additional_tests = self._extract_nested_items_markdown(diff_match.group(1))
        
        return pattern
    
    def _extract_list_items_markdown(self, text: str) -> List[str]:
        """從 Markdown 文本中提取列表項目"""
        items = []
        
        # 清理文本
        text = text.strip()
        
        # 匹配 Markdown 列表格式
        # - 項目
        # * 項目
        # 1. 項目
        patterns = [
            r'^[-\*]\s+(.+?)(?=^[-\*]|\Z)',  # 無序列表
            r'^\d+\.\s+(.+?)(?=^\d+\.|\Z)',  # 有序列表
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                # 清理並添加項目
                item = match.strip()
                if item and len(item) > 5:  # 過濾太短的項目
                    items.append(item)
        
        # 如果沒有找到列表，嘗試按句號分割
        if not items:
            sentences = re.split(r'。', text)
            items = [s.strip() + '。' for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return items
    
    def _extract_nested_items_markdown(self, text: str) -> List[str]:
        """提取嵌套的 Markdown 項目（包含子項目）"""
        items = []
        
        # 先提取主要項目
        main_items = re.findall(r'^[-\*]\s+\*\*(.*?)\*\*[：:]?(.*?)(?=^[-\*]|\Z)', text, re.MULTILINE | re.DOTALL)
        
        for title, content in main_items:
            # 組合標題和內容
            full_item = f"{title.strip()}: {content.strip()}"
            items.append(full_item)
            
            # 提取子項目
            sub_items = re.findall(r'^\s+[-\*]\s+\*\*(.*?)\*\*[：:]?\s*(.*?)(?=^\s+[-\*]|^[-\*]|\Z)', content, re.MULTILINE | re.DOTALL)
            for sub_title, sub_content in sub_items:
                items.append(f"  - {sub_title.strip()}: {sub_content.strip()}")
        
        # 如果沒有找到嵌套格式，使用簡單提取
        if not items:
            items = self._extract_list_items_markdown(text)
        
        return items
    
    def _extract_evaluation_steps(self, text: str) -> List[str]:
        """提取評估步驟"""
        steps = []
        
        # 提取帶有條件的步驟
        # 格式: **條件：** 動作
        condition_steps = re.findall(
            r'\*\*(.*?)[：:]\*\*\s*(.*?)(?=\*\*|$)',
            text,
            re.DOTALL
        )
        
        for condition, action in condition_steps:
            step = f"{condition.strip()}: {action.strip()}"
            steps.append(step)
        
        # 如果沒有找到條件格式，使用列表提取
        if not steps:
            steps = self._extract_list_items_markdown(text)
        
        return steps
    
    def _extract_qa_pairs_from_markdown(self, sections: Dict[str, str]) -> List[Dict[str, str]]:
        """從 Markdown 提取問答對"""
        qa_pairs = []
        
        if "qa_section" in sections:
            qa_text = sections["qa_section"]
            
            # 匹配 **Q1：** ... **A1：** ... 格式
            qa_pattern = re.compile(
                r'\*\*Q(\d+)[：:]\*\*\s*(.*?)\s*\*\*A\1[：:]\*\*\s*(.*?)(?=\*\*Q\d+[：:]|$)', 
                re.DOTALL
            )
            
            matches = qa_pattern.findall(qa_text)
            for match in matches:
                qa_num, question, answer = match
                qa_pairs.append({
                    "id": f"Q{qa_num}",
                    "question": question.strip(),
                    "answer": answer.strip()
                })
        
        return qa_pairs
    
    def _extract_reference_ranges(self, content: str) -> Dict[str, Dict[str, Any]]:
        """提取參考值範圍"""
        reference_ranges = {}
        
        # 從文本中提取提到的參考值
        # TSH: 0.4-4.0 μIU/mL
        tsh_range = re.search(r'TSH[^0-9]*([0-9.]+)[^0-9]+([0-9.]+)\s*μIU/mL', content)
        if tsh_range:
            reference_ranges["TSH"] = {
                "min": float(tsh_range.group(1)),
                "max": float(tsh_range.group(2)),
                "unit": "μIU/mL"
            }
        
        # Free T4: 0.8-1.8 ng/dL
        ft4_range = re.search(r'Free T4[^0-9]*([0-9.]+)[^0-9]+([0-9.]+)\s*ng/dL', content)
        if ft4_range:
            reference_ranges["Free_T4"] = {
                "min": float(ft4_range.group(1)),
                "max": float(ft4_range.group(2)),
                "unit": "ng/dL"
            }
        
        # Free T3: 2.3-4.2 pg/mL
        ft3_range = re.search(r'Free T3[^0-9]*([0-9.]+)[^0-9]+([0-9.]+)\s*pg/mL', content)
        if ft3_range:
            reference_ranges["Free_T3"] = {
                "min": float(ft3_range.group(1)),
                "max": float(ft3_range.group(2)),
                "unit": "pg/mL"
            }
        
        # 抗體參考值（通常只有上限）
        antibody_patterns = [
            (r'Anti-TPO[^0-9]*<\s*([0-9.]+)\s*IU/mL', "Anti_TPO"),
            (r'Anti-Tg[^0-9]*<\s*([0-9.]+)\s*IU/mL', "Anti_Tg"),
            (r'TSH[^受體]*受體抗體[^0-9]*<\s*([0-9.]+)\s*IU/L', "TSH_receptor_Ab")
        ]
        
        for pattern, name in antibody_patterns:
            match = re.search(pattern, content)
            if match:
                reference_ranges[name] = {
                    "max": float(match.group(1)),
                    "unit": "IU/mL" if name != "TSH_receptor_Ab" else "IU/L"
                }
        
        return reference_ranges
    
    def save_parsed_knowledge(self, parsed_data: Dict[str, Any], output_path: str):
        """保存解析後的知識庫"""
        # 轉換為可序列化的格式
        serializable_data = {
            "patterns": [self._pattern_to_dict(p) for p in parsed_data["patterns"]],
            "qa_pairs": parsed_data["qa_pairs"],
            "reference_ranges": parsed_data.get("reference_ranges", {})
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
    
    def _pattern_to_dict(self, pattern: ThyroidPattern) -> Dict[str, Any]:
        """將 ThyroidPattern 轉換為字典"""
        return {
            "pattern_id": pattern.pattern_id,
            "tsh_status": pattern.tsh_status,
            "ft4_status": pattern.ft4_status,
            "ft3_status": pattern.ft3_status,
            "common_causes": pattern.common_causes or [],
            "interfering_factors": pattern.interfering_factors or [],
            "differential_diagnosis": pattern.differential_diagnosis or [],
            "recommendations": pattern.recommendations or [],
            "additional_tests": pattern.additional_tests or [],
            "case_examples": pattern.case_examples or [],
            "notes": pattern.notes
        } 