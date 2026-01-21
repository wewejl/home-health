"""
病历分析服务 - 从病历文件中提取医生诊疗特征
"""
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
from io import BytesIO
import PyPDF2.errors


class RecordAnalysisService:
    """病历分析服务"""

    # AI 分析提示词模板
    ANALYSIS_PROMPT = """你是医疗专家分析助手。请分析以下病历内容，提取该医生的诊疗特征。

病历内容：
{medical_records}

请以 JSON 格式返回：
{{
  "diagnostic_style": "诊断思路描述",
  "prescription_habits": "处方习惯描述",
  "follow_up_pattern": "随访习惯描述",
  "communication_style": "沟通风格描述",
  "specialty_focus": "专科关注点"
}}

要求：
1. 总结要简洁准确
2. 从病历中提取真实的诊疗模式
3. 避免编造信息
4. 如果某方面信息不足，填写"信息不足"
"""

    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> str:
        """
        解析上传文件，提取文本内容

        Args:
            file_content: 文件内容（字节）
            filename: 文件名

        Returns:
            提取的文本内容
        """
        file_ext = Path(filename).suffix.lower()

        if file_ext == '.pdf':
            return RecordAnalysisService._parse_pdf(file_content)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
            # 图片文件暂时返回占位符，需要 OCR 服务
            return "[图片内容 - 需要OCR识别]"
        elif file_ext == '.txt':
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

    @staticmethod
    def _parse_pdf(file_content: bytes) -> str:
        """解析 PDF 文件"""
        try:
            pdf_file = BytesIO(file_content)
            reader = PyPDF2.PdfReader(pdf_file)

            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            return "\n".join(text_parts)
        except PyPDF2.errors.PdfReadError:
            raise ValueError("PDF 文件损坏或格式不支持")
        except Exception:
            raise ValueError("PDF 解析失败，请检查文件格式")

    @staticmethod
    def extract_features(text: str) -> Dict[str, str]:
        """
        从病历文本中提取诊疗特征

        Args:
            text: 病历文本内容

        Returns:
            提取的特征字典
        """
        # 这里使用规则提取一些基本特征
        # 实际项目中应该调用 LLM 进行更精确的分析

        features = {
            "diagnostic_style": "",
            "prescription_habits": "",
            "follow_up_pattern": "",
            "communication_style": "",
            "specialty_focus": ""
        }

        # 分析诊断思路 - 寻找关键词
        if "主诉" in text or "现病史" in text:
            features["diagnostic_style"] = "善于从主诉和现病史入手，系统性地收集病史信息"

        # 分析处方习惯
        if "阿司匹林" in text or "降压" in text or "降糖" in text:
            features["prescription_habits"] = "注重慢性病管理，倾向使用规范化治疗方案"

        # 分析随访习惯
        if "复查" in text or "随访" in text or "复诊" in text:
            features["follow_up_pattern"] = "重视复查时间节点，强调规律随访"

        # 分析沟通风格
        if "建议" in text or "指导" in text:
            features["communication_style"] = "注重患者教育，提供详细的生活和用药指导"

        # 专科关注点
        specialty_keywords = {
            "心血管": ["心脏", "血压", "心律", "心绞痛", "心衰"],
            "内分泌": ["糖尿病", "甲状腺", "血糖", "胰岛素"],
            "呼吸": ["咳嗽", "哮喘", "肺炎", "肺功能"],
            "消化": ["胃", "肠", "肝", "消化", "腹痛"],
            "神经": ["头痛", "头晕", "中风", "癫痫"],
            "骨科": ["骨折", "关节", "脊柱", "骨质疏松"]
        }

        for specialty, keywords in specialty_keywords.items():
            if any(kw in text for kw in keywords):
                features["specialty_focus"] = f"专科关注点包括{specialty}系统相关疾病"
                break

        # 如果没有提取到信息，设置默认值
        for key, value in features.items():
            if not value:
                features[key] = "信息不足，需要更多病历数据"

        return features

    @staticmethod
    def generate_persona_prompt(features: Dict[str, str], doctor_name: str) -> str:
        """
        根据提取的特征生成 AI 人设 Prompt

        Args:
            features: 提取的特征字典
            doctor_name: 医生姓名

        Returns:
            生成的 prompt
        """
        prompt = f"""你是 {doctor_name} 医生的 AI 分身。

## 诊疗风格

{features.get('diagnostic_style', '注重全面分析，系统性地收集患者信息')}

## 处方习惯

{features.get('prescription_habits', '遵循循证医学原则，个体化制定治疗方案')}

## 随访管理

{features.get('follow_up_pattern', '重视患者依从性，定期随访评估治疗效果')}

## 沟通方式

{features.get('communication_style', '用通俗易懂的语言解释病情，耐心回答患者疑问')}

## 专长领域

{features.get('specialty_focus', '全科医学，常见病多发病诊治')}

请根据以上特点，以 {doctor_name} 医生的口吻回答患者问题。
"""
        return prompt

    @staticmethod
    async def analyze_records(
        files: List[tuple[str, bytes]]
    ) -> Dict[str, Any]:
        """
        分析病历文件，提取诊疗特征并生成 prompt

        Args:
            files: 文件列表 [(filename, content), ...]

        Returns:
            分析结果
        """
        all_text = []
        parsed_results = []

        # 解析所有文件
        for filename, content in files:
            try:
                text = RecordAnalysisService.parse_file(content, filename)
                all_text.append(text)
                parsed_results.append({
                    "filename": filename,
                    "status": "success",
                    "length": len(text)
                })
            except Exception as e:
                parsed_results.append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })

        combined_text = "\n\n".join(all_text)

        # 提取特征
        features = RecordAnalysisService.extract_features(combined_text)

        # 生成 prompt
        prompt = RecordAnalysisService.generate_persona_prompt(features, "医生")

        return {
            "parsed_files": parsed_results,
            "total_text_length": len(combined_text),
            "features": features,
            "generated_prompt": prompt
        }
