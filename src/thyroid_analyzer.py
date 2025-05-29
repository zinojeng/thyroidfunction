"""
甲狀腺功能分析器
提供檢驗結果解讀和診斷建議
"""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from config import Config

class ThyroidStatus(Enum):
    """甲狀腺功能狀態"""
    NORMAL = "正常"
    HYPERTHYROID = "甲狀腺功能亢進"
    HYPOTHYROID = "甲狀腺功能低下"
    SUBCLINICAL_HYPER = "亞臨床甲狀腺功能亢進"
    SUBCLINICAL_HYPO = "亞臨床甲狀腺功能低下"
    CENTRAL_HYPOTHYROID = "中樞性甲狀腺功能低下"

@dataclass
class LabResult:
    """檢驗結果"""
    name: str
    value: float
    unit: str
    status: str  # 正常/偏高/偏低/陽性/陰性
    reference_range: str

@dataclass
class DiagnosisResult:
    """診斷結果"""
    thyroid_status: ThyroidStatus
    confidence: float  # 診斷信心度 0-1
    differential_diagnosis: List[Tuple[str, float]]  # (診斷, 可能性)
    recommendations: List[str]  # 建議事項
    additional_tests: List[str]  # 建議的額外檢查

class ThyroidAnalyzer:
    def __init__(self):
        """初始化甲狀腺分析器"""
        self.normal_ranges = Config.NORMAL_RANGES
    
    def analyze(self, lab_data: Dict[str, float], 
                symptoms: List[str] = [],
                medical_history: Dict[str, Any] = {}) -> DiagnosisResult:
        """
        分析甲狀腺功能
        
        Args:
            lab_data: 檢驗數據 {"TSH": 5.2, "Free_T4": 0.9, ...}
            symptoms: 症狀列表
            medical_history: 病史資訊
            
        Returns:
            DiagnosisResult: 診斷結果
        """
        # 解讀檢驗數值
        lab_results = self._parse_lab_results(lab_data)
        
        # 判斷甲狀腺功能狀態
        thyroid_status = self._determine_thyroid_status(lab_results)
        
        # 生成鑑別診斷
        differential = self._generate_differential_diagnosis(
            lab_results, thyroid_status, symptoms, medical_history
        )
        
        # 生成建議
        recommendations = self._generate_recommendations(
            thyroid_status, lab_results, symptoms
        )
        
        # 建議的額外檢查
        additional_tests = self._suggest_additional_tests(
            thyroid_status, lab_results
        )
        
        # 計算診斷信心度
        confidence = self._calculate_confidence(lab_results, symptoms)
        
        return DiagnosisResult(
            thyroid_status=thyroid_status,
            confidence=confidence,
            differential_diagnosis=differential,
            recommendations=recommendations,
            additional_tests=additional_tests
        )
    
    def _parse_lab_results(self, lab_data: Dict[str, float]) -> Dict[str, LabResult]:
        """解析檢驗結果"""
        results = {}
        
        for test_name, value in lab_data.items():
            if test_name in self.normal_ranges:
                normal_range = self.normal_ranges[test_name]
                unit = normal_range.get("unit", "")
                
                # 判斷狀態
                if "min" in normal_range and "max" in normal_range:
                    if value < normal_range["min"]:
                        status = "偏低"
                    elif value > normal_range["max"]:
                        status = "偏高"
                    else:
                        status = "正常"
                    ref_range = f"{normal_range['min']}-{normal_range['max']} {unit}"
                else:
                    # 抗體檢測
                    if value > normal_range["max"]:
                        status = "陽性"
                    else:
                        status = "陰性"
                    ref_range = f"< {normal_range['max']} {unit}"
                
                results[test_name] = LabResult(
                    name=test_name,
                    value=value,
                    unit=unit,
                    status=status,
                    reference_range=ref_range
                )
        
        return results
    
    def _determine_thyroid_status(self, lab_results: Dict[str, LabResult]) -> ThyroidStatus:
        """判斷甲狀腺功能狀態"""
        tsh = lab_results.get("TSH")
        ft4 = lab_results.get("Free_T4")
        ft3 = lab_results.get("Free_T3")
        
        if not tsh:
            return ThyroidStatus.NORMAL
        
        # 甲狀腺功能亢進
        if tsh.status == "偏低":
            if ft4 and ft4.status == "偏高":
                return ThyroidStatus.HYPERTHYROID
            elif ft3 and ft3.status == "偏高":
                return ThyroidStatus.HYPERTHYROID
            else:
                return ThyroidStatus.SUBCLINICAL_HYPER
        
        # 甲狀腺功能低下
        elif tsh.status == "偏高":
            if ft4 and ft4.status == "偏低":
                return ThyroidStatus.HYPOTHYROID
            elif ft4 and ft4.status == "正常":
                # TSH 輕度升高 (4-10)
                if tsh.value <= 10:
                    return ThyroidStatus.SUBCLINICAL_HYPO
                else:
                    return ThyroidStatus.HYPOTHYROID
            else:
                return ThyroidStatus.SUBCLINICAL_HYPO
        
        # 中樞性甲狀腺功能低下（罕見）
        elif tsh.status == "正常" or tsh.status == "偏低":
            if ft4 and ft4.status == "偏低":
                return ThyroidStatus.CENTRAL_HYPOTHYROID
        
        return ThyroidStatus.NORMAL
    
    def _generate_differential_diagnosis(
        self, 
        lab_results: Dict[str, LabResult],
        thyroid_status: ThyroidStatus,
        symptoms: List[str] = [],
        medical_history: Dict[str, Any] = {}
    ) -> List[Tuple[str, float]]:
        """生成鑑別診斷"""
        differential = []
        
        if thyroid_status == ThyroidStatus.HYPERTHYROID:
            # 檢查抗體
            trab = lab_results.get("TSH_receptor_Ab")
            if trab and trab.status == "陽性":
                differential.append(("Graves' disease", 0.8))
            else:
                differential.append(("毒性多結節性甲狀腺腫", 0.4))
                differential.append(("毒性腺瘤", 0.3))
                differential.append(("亞急性甲狀腺炎", 0.2))
        
        elif thyroid_status == ThyroidStatus.HYPOTHYROID:
            # 檢查抗體
            anti_tpo = lab_results.get("Anti_TPO")
            anti_tg = lab_results.get("Anti_Tg")
            
            if (anti_tpo and anti_tpo.status == "陽性") or \
               (anti_tg and anti_tg.status == "陽性"):
                differential.append(("橋本氏甲狀腺炎", 0.7))
            else:
                differential.append(("原發性甲狀腺功能低下", 0.5))
                differential.append(("碘缺乏", 0.2))
                differential.append(("藥物引起", 0.2))
        
        elif thyroid_status == ThyroidStatus.SUBCLINICAL_HYPO:
            anti_tpo = lab_results.get("Anti_TPO")
            if anti_tpo and anti_tpo.status == "陽性":
                differential.append(("早期橋本氏甲狀腺炎", 0.6))
            else:
                differential.append(("亞臨床甲狀腺功能低下", 0.7))
        
        return sorted(differential, key=lambda x: x[1], reverse=True)
    
    def _generate_recommendations(
        self,
        thyroid_status: ThyroidStatus,
        lab_results: Dict[str, LabResult],
        symptoms: List[str] = []
    ) -> List[str]:
        """生成建議事項"""
        recommendations = []
        
        if thyroid_status == ThyroidStatus.HYPERTHYROID:
            recommendations.extend([
                "建議儘快就診內分泌科",
                "可能需要抗甲狀腺藥物治療",
                "避免含碘食物和藥物",
                "監測心率和血壓",
                "如有眼部症狀，需眼科評估"
            ])
        
        elif thyroid_status == ThyroidStatus.HYPOTHYROID:
            recommendations.extend([
                "建議開始甲狀腺素補充治療",
                "定期監測TSH水平（初期每6-8週）",
                "注意藥物服用時間（空腹）",
                "評估心血管風險",
                "如懷孕需立即調整劑量"
            ])
        
        elif thyroid_status == ThyroidStatus.SUBCLINICAL_HYPO:
            tsh = lab_results.get("TSH")
            if tsh and tsh.value > 7:
                recommendations.append("TSH > 7，建議考慮治療")
            else:
                recommendations.append("定期追蹤（3-6個月）")
            
            if symptoms:
                recommendations.append("有症狀者可考慮試驗性治療")
        
        return recommendations
    
    def _suggest_additional_tests(
        self,
        thyroid_status: ThyroidStatus,
        lab_results: Dict[str, LabResult]
    ) -> List[str]:
        """建議額外檢查"""
        tests = []
        
        # 如果沒有測抗體
        if "Anti_TPO" not in lab_results:
            tests.append("Anti-TPO 抗體")
        
        if thyroid_status == ThyroidStatus.HYPERTHYROID:
            if "TSH_receptor_Ab" not in lab_results:
                tests.append("TSH 受體抗體 (TRAb)")
            tests.extend([
                "甲狀腺超音波",
                "甲狀腺掃描（如需要）",
                "肝功能檢查",
                "全血球計數"
            ])
        
        elif thyroid_status in [ThyroidStatus.HYPOTHYROID, ThyroidStatus.SUBCLINICAL_HYPO]:
            tests.extend([
                "血脂肪檢查",
                "維生素 B12",
                "甲狀腺超音波"
            ])
        
        return tests
    
    def _calculate_confidence(
        self,
        lab_results: Dict[str, LabResult],
        symptoms: List[str] = []
    ) -> float:
        """計算診斷信心度"""
        confidence = 0.5
        
        # 基於檢驗完整度
        essential_tests = ["TSH", "Free_T4"]
        for test in essential_tests:
            if test in lab_results:
                confidence += 0.15
        
        # 有抗體結果增加信心度
        if any(test in lab_results for test in ["Anti_TPO", "Anti_Tg", "TSH_receptor_Ab"]):
            confidence += 0.1
        
        # 有症狀描述增加信心度
        if symptoms:
            confidence += 0.1
        
        return min(confidence, 0.95)
    
    def generate_report(self, diagnosis_result: DiagnosisResult, 
                       lab_data: Dict[str, float]) -> str:
        """生成診斷報告"""
        report = f"""
# 甲狀腺功能檢查報告

## 檢驗結果
"""
        # 檢驗數值表格
        for test_name, value in lab_data.items():
            if test_name in self.normal_ranges:
                normal_range = self.normal_ranges[test_name]
                unit = normal_range.get("unit", "")
                report += f"- **{test_name}**: {value} {unit}\n"
        
        report += f"""
## 診斷
**甲狀腺功能狀態**: {diagnosis_result.thyroid_status.value}
**診斷信心度**: {diagnosis_result.confidence:.0%}

## 鑑別診斷
"""
        for diagnosis, probability in diagnosis_result.differential_diagnosis:
            report += f"- {diagnosis} (可能性: {probability:.0%})\n"
        
        report += """
## 建議事項
"""
        for rec in diagnosis_result.recommendations:
            report += f"- {rec}\n"
        
        if diagnosis_result.additional_tests:
            report += """
## 建議額外檢查
"""
            for test in diagnosis_result.additional_tests:
                report += f"- {test}\n"
        
        return report
