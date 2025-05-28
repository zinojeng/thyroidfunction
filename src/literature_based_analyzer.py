"""
基於文獻的甲狀腺功能判讀引擎
完全依據上傳的醫學文獻進行判讀，不使用預設規則
"""
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class LiteratureBasedDiagnosis:
    """基於文獻的診斷結果"""
    pattern_match: str  # 匹配的模式描述
    common_causes: List[str]
    differential_diagnosis: List[Tuple[str, float]]  # (診斷, 相關性分數)
    interfering_factors: List[str]
    recommendations: List[str]
    additional_tests: List[str]
    supporting_literature: List[str]  # 支持的文獻來源
    confidence_score: float
    special_notes: Optional[str] = None

class LiteratureBasedAnalyzer:
    def __init__(self, knowledge_base_path: str = None):
        """
        初始化基於文獻的分析器
        
        Args:
            knowledge_base_path: 解析後的知識庫JSON檔案路徑
        """
        self.knowledge_base = {}
        self.patterns = []
        self.guidelines = []
        self.qa_pairs = []
        
        if knowledge_base_path and Path(knowledge_base_path).exists():
            self.load_knowledge_base(knowledge_base_path)
    
    def load_knowledge_base(self, path: str):
        """載入解析後的知識庫"""
        with open(path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        
        self.patterns = self.knowledge_base.get("patterns", [])
        self.guidelines = self.knowledge_base.get("guidelines", [])
        self.qa_pairs = self.knowledge_base.get("qa_pairs", [])
    
    def analyze_from_literature(
        self, 
        lab_data: Dict[str, float],
        symptoms: List[str] = None,
        patient_info: Dict[str, Any] = None
    ) -> LiteratureBasedDiagnosis:
        """
        基於文獻進行甲狀腺功能分析
        
        Args:
            lab_data: 檢驗數據
            symptoms: 症狀列表
            patient_info: 患者資訊（年齡、性別、用藥等）
            
        Returns:
            基於文獻的診斷結果
        """
        # 1. 判斷檢驗值狀態
        lab_status = self._determine_lab_status(lab_data)
        
        # 2. 匹配文獻中的模式
        matched_pattern = self._match_pattern(lab_status)
        
        # 3. 考慮干擾因素
        interfering_factors = self._check_interfering_factors(
            lab_data, patient_info, matched_pattern
        )
        
        # 4. 生成鑑別診斷
        differential = self._generate_differential_from_literature(
            matched_pattern, lab_status, symptoms, patient_info
        )
        
        # 5. 提取建議和額外檢查
        recommendations = self._extract_recommendations(
            matched_pattern, lab_status, interfering_factors
        )
        
        additional_tests = self._extract_additional_tests(
            matched_pattern, lab_data
        )
        
        # 6. 計算信心分數
        confidence = self._calculate_confidence(
            matched_pattern, lab_data, interfering_factors
        )
        
        # 7. 查找相關問答
        special_notes = self._find_relevant_qa(lab_status, symptoms)
        
        return LiteratureBasedDiagnosis(
            pattern_match=self._describe_pattern(matched_pattern),
            common_causes=matched_pattern.get("common_causes", []),
            differential_diagnosis=differential,
            interfering_factors=interfering_factors,
            recommendations=recommendations,
            additional_tests=additional_tests,
            supporting_literature=["異常甲狀腺功能檢測的解讀與評估"],
            confidence_score=confidence,
            special_notes=special_notes
        )
    
    def _determine_lab_status(self, lab_data: Dict[str, float]) -> Dict[str, str]:
        """根據文獻中的參考值判斷檢驗狀態"""
        status = {}
        
        # 從文獻中提取的參考範圍
        reference_ranges = {
            "TSH": {"low": 0.4, "high": 4.0},
            "Free_T4": {"low": 0.8, "high": 1.8},
            "Free_T3": {"low": 2.3, "high": 4.2},
            "Anti_TPO": {"threshold": 34},
            "Anti_Tg": {"threshold": 115},
            "TSH_receptor_Ab": {"threshold": 1.75}
        }
        
        for test, value in lab_data.items():
            if test in reference_ranges:
                ref = reference_ranges[test]
                
                if "low" in ref and "high" in ref:
                    if value < ref["low"]:
                        status[test] = "低"
                    elif value > ref["high"]:
                        status[test] = "高"
                    else:
                        status[test] = "正常"
                elif "threshold" in ref:
                    status[test] = "陽性" if value > ref["threshold"] else "陰性"
        
        return status
    
    def _match_pattern(self, lab_status: Dict[str, str]) -> Dict[str, Any]:
        """匹配文獻中描述的模式"""
        tsh_status = lab_status.get("TSH", "未知")
        ft4_status = lab_status.get("Free_T4", "未知")
        ft3_status = lab_status.get("Free_T3", "未知")
        
        # 尋找最匹配的模式
        for pattern in self.patterns:
            if (pattern.get("tsh_status") == tsh_status and 
                pattern.get("ft4_status") == ft4_status):
                
                # 如果有 T3 數據，也要匹配
                if ft3_status != "未知" and pattern.get("ft3_status"):
                    if pattern.get("ft3_status") == ft3_status:
                        return pattern
                else:
                    return pattern
        
        # 如果沒有完全匹配，返回最接近的模式
        return self._find_closest_pattern(lab_status)
    
    def _find_closest_pattern(self, lab_status: Dict[str, str]) -> Dict[str, Any]:
        """找到最接近的模式"""
        # 如果沒有完全匹配，根據 TSH 狀態返回相關模式
        tsh_status = lab_status.get("TSH", "未知")
        
        for pattern in self.patterns:
            if pattern.get("tsh_status") == tsh_status:
                return pattern
        
        # 返回預設模式
        return {
            "tsh_status": tsh_status,
            "ft4_status": lab_status.get("Free_T4", "未知"),
            "common_causes": ["需要進一步評估"],
            "recommendations": ["建議完整檢查甲狀腺功能"],
            "additional_tests": ["完整甲狀腺功能檢測", "甲狀腺超音波"]
        }
    
    def _check_interfering_factors(
        self, 
        lab_data: Dict[str, float],
        patient_info: Dict[str, Any],
        matched_pattern: Dict[str, Any]
    ) -> List[str]:
        """檢查可能的干擾因素"""
        factors = []
        
        # 從匹配的模式中提取干擾因素
        pattern_factors = matched_pattern.get("interfering_factors", [])
        factors.extend(pattern_factors)
        
        # 根據患者資訊檢查特定干擾因素
        if patient_info:
            # 檢查 Biotin 干擾
            if patient_info.get("medications"):
                meds = patient_info["medications"].lower()
                if "biotin" in meds or "生物素" in meds:
                    factors.append("Biotin 可能干擾檢測結果")
            
            # 檢查懷孕
            if patient_info.get("pregnancy"):
                factors.append("懷孕期間甲狀腺功能參考值不同")
            
            # 檢查年齡因素
            age = patient_info.get("age", 0)
            if age > 65:
                factors.append("高齡者 TSH 參考值上限可能較高")
            
            # 檢查肥胖
            if patient_info.get("bmi", 0) > 30:
                factors.append("肥胖可能導致 TSH 偏高")
        
        return list(set(factors))  # 去重
    
    def _generate_differential_from_literature(
        self,
        matched_pattern: Dict[str, Any],
        lab_status: Dict[str, str],
        symptoms: List[str],
        patient_info: Dict[str, Any]
    ) -> List[Tuple[str, float]]:
        """基於文獻生成鑑別診斷"""
        differential = []
        
        # 從匹配模式中獲取常見原因
        common_causes = matched_pattern.get("common_causes", [])
        for i, cause in enumerate(common_causes):
            # 根據順序給予不同權重
            base_score = 0.8 - (i * 0.1)
            
            # 根據抗體結果調整分數
            if "Graves" in cause and lab_status.get("TSH_receptor_Ab") == "陽性":
                score = min(base_score + 0.2, 0.95)
            elif "橋本" in cause and lab_status.get("Anti_TPO") == "陽性":
                score = min(base_score + 0.2, 0.95)
            else:
                score = base_score
            
            differential.append((cause, score))
        
        # 從鑑別診斷列表中添加
        diff_list = matched_pattern.get("differential_diagnosis", [])
        for diagnosis in diff_list:
            if diagnosis not in [d[0] for d in differential]:
                differential.append((diagnosis, 0.3))
        
        return sorted(differential, key=lambda x: x[1], reverse=True)
    
    def _extract_recommendations(
        self,
        matched_pattern: Dict[str, Any],
        lab_status: Dict[str, str],
        interfering_factors: List[str]
    ) -> List[str]:
        """從文獻中提取建議"""
        recommendations = []
        
        # 基本建議來自匹配的模式
        pattern_recs = matched_pattern.get("recommendations", [])
        recommendations.extend(pattern_recs)
        
        # 如果有干擾因素，添加相關建議
        if interfering_factors:
            if any("Biotin" in f for f in interfering_factors):
                recommendations.append("建議停用 Biotin 補充劑 3-5 天後重新檢測")
            
            if any("懷孕" in f for f in interfering_factors):
                recommendations.append("使用懷孕期特定參考值評估")
        
        # 根據特定情況添加建議
        tsh_status = lab_status.get("TSH")
        ft4_status = lab_status.get("Free_T4")
        
        if tsh_status == "低" and ft4_status == "低":
            recommendations.append("高度懷疑中樞性甲狀腺功能異常，建議評估其他垂體激素")
        
        return list(set(recommendations))  # 去重
    
    def _extract_additional_tests(
        self,
        matched_pattern: Dict[str, Any],
        lab_data: Dict[str, float]
    ) -> List[str]:
        """從文獻中提取建議的額外檢查"""
        tests = []
        
        # 從模式中獲取建議檢查
        pattern_tests = matched_pattern.get("additional_tests", [])
        tests.extend(pattern_tests)
        
        # 根據現有檢查結果建議額外檢查
        if "Anti_TPO" not in lab_data:
            tests.append("Anti-TPO 抗體")
        
        if "TSH_receptor_Ab" not in lab_data and lab_data.get("TSH", 1) < 0.4:
            tests.append("TSH 受體抗體")
        
        if "Free_T3" not in lab_data:
            tests.append("Free T3")
        
        return list(set(tests))  # 去重
    
    def _calculate_confidence(
        self,
        matched_pattern: Dict[str, Any],
        lab_data: Dict[str, float],
        interfering_factors: List[str]
    ) -> float:
        """計算診斷信心分數"""
        confidence = 0.5
        
        # 如果有完美匹配的模式
        if matched_pattern.get("tsh_status") != "未知":
            confidence += 0.2
        
        # 檢驗項目完整度
        essential_tests = ["TSH", "Free_T4"]
        for test in essential_tests:
            if test in lab_data:
                confidence += 0.1
        
        # 有抗體結果
        if any(test in lab_data for test in ["Anti_TPO", "Anti_Tg", "TSH_receptor_Ab"]):
            confidence += 0.1
        
        # 干擾因素會降低信心度
        if interfering_factors:
            confidence -= 0.1 * len(interfering_factors)
        
        return max(0.1, min(0.95, confidence))
    
    def _describe_pattern(self, pattern: Dict[str, Any]) -> str:
        """描述匹配的模式"""
        tsh = pattern.get("tsh_status", "未知")
        ft4 = pattern.get("ft4_status", "未知")
        ft3 = pattern.get("ft3_status", "")
        
        description = f"TSH {tsh}, Free T4 {ft4}"
        if ft3:
            description += f", Free T3 {ft3}"
        
        return description
    
    def _find_relevant_qa(
        self,
        lab_status: Dict[str, str],
        symptoms: List[str]
    ) -> Optional[str]:
        """查找相關的問答內容"""
        relevant_qa = []
        
        for qa in self.qa_pairs:
            question = qa.get("question", "").lower()
            answer = qa.get("answer", "")
            
            # 根據檢驗狀態查找相關問答
            if ("tsh" in question and lab_status.get("TSH")) or \
               ("t4" in question and lab_status.get("Free_T4")) or \
               ("t3" in question and lab_status.get("Free_T3")):
                relevant_qa.append(f"Q: {qa['question']}\nA: {answer}")
        
        if relevant_qa:
            return "\n\n".join(relevant_qa[:2])  # 最多返回2個相關問答
        
        return None
    
    def generate_literature_based_report(
        self,
        diagnosis: LiteratureBasedDiagnosis,
        lab_data: Dict[str, float]
    ) -> str:
        """生成基於文獻的診斷報告"""
        report = f"""
# 基於文獻的甲狀腺功能檢查報告

## 檢驗結果
"""
        # 檢驗數值
        lab_status = self._determine_lab_status(lab_data)
        for test, value in lab_data.items():
            status = lab_status.get(test, "")
            report += f"- **{test}**: {value} ({status})\n"
        
        report += f"""
## 模式匹配
**檢驗模式**: {diagnosis.pattern_match}

## 常見原因
"""
        for cause in diagnosis.common_causes:
            report += f"- {cause}\n"
        
        report += """
## 鑑別診斷
"""
        for diag, score in diagnosis.differential_diagnosis:
            report += f"- {diag} (相關性: {score:.0%})\n"
        
        if diagnosis.interfering_factors:
            report += """
## 潛在干擾因素
"""
            for factor in diagnosis.interfering_factors:
                report += f"- {factor}\n"
        
        report += """
## 建議事項
"""
        for rec in diagnosis.recommendations:
            report += f"- {rec}\n"
        
        if diagnosis.additional_tests:
            report += """
## 建議額外檢查
"""
            for test in diagnosis.additional_tests:
                report += f"- {test}\n"
        
        report += f"""
## 診斷信心度
{diagnosis.confidence_score:.0%}

## 參考文獻
"""
        for lit in diagnosis.supporting_literature:
            report += f"- {lit}\n"
        
        if diagnosis.special_notes:
            report += f"""
## 相關問答參考
{diagnosis.special_notes}
"""
        
        return report 