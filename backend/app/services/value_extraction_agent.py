"""
数值抽取 Agent

从语音识别文本中抽取医嘱相关数值：
- 血糖值（支持 mmol/L）
- 血压值（收缩压/舒张压）
- 体温
- 体重等

支持多种中文表达方式，优先使用正则匹配，失败时使用 LLM
"""
import re
import logging
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field

from .ai.base_ai_service import BaseAIService

logger = logging.getLogger(__name__)


# ========== Pydantic 模型 ==========

class BloodGlucoseResult(BaseModel):
    """血糖抽取结果"""
    value: float = Field(description="血糖数值")
    unit: str = Field(description="单位，默认mmol/L")
    is_low: bool = Field(description="是否低血糖 (<3.9)")
    is_high: bool = Field(description="是否高血糖 (>11.1)")


class BloodPressureResult(BaseModel):
    """血压抽取结果"""
    systolic: int = Field(description="收缩压（高压）")
    diastolic: int = Field(description="舒张压（低压）")
    level: str = Field(description="血压等级：normal/elevated/high_1/high_2")


class TemperatureResult(BaseModel):
    """体温抽取结果"""
    value: float = Field(description="体温数值")
    unit: str = Field(description="单位")
    is_fever: bool = Field(description="是否发烧 (>37.3)")


class WeightResult(BaseModel):
    """体重抽取结果"""
    value: float = Field(description="体重数值")
    unit: str = Field(description="单位，统一为kg")


# ========== 数值抽取 Agent ==========

class ValueExtractionAgent(BaseAIService):
    """
    数值抽取 Agent

    从语音识别文本中抽取医嘱相关的健康指标数值
    """

    def __init__(self):
        super().__init__(temperature=0.1, max_tokens=500)

        # 中文数字映射
        self.cn_numbers = {
            "零": 0, "〇": 0,
            "一": 1, "二": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
            "十": 10, "两": 2
        }

    # ========== 血糖抽取 ==========

    async def extract_blood_glucose(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取血糖值

        支持多种表达：
        - "血糖8点5"
        - "血糖八"
        - "餐后血糖7.8"
        - "低血糖3.2"
        """
        # 先尝试正则抽取
        result = self._extract_glucose_regex(text)
        if result and result.get("value", 0) > 0:
            return await self._normalize_glucose(result)

        # LLM 抽取（作为降级方案）
        try:
            result = await self._extract_glucose_llm(text)
            if result and result.get("value", 0) > 0:
                return result
        except Exception as e:
            logger.warning(f"LLM 血糖抽取失败: {e}")

        # 最终降级方案
        return self._extract_glucose_fallback(text)

    def _extract_glucose_regex(self, text: str) -> Optional[Dict]:
        """正则抽取血糖"""
        # 匹配模式列表 - 按优先级排序
        patterns = [
            # "8点5" 格式 (最优先)
            (r'(\d+)\s*点\s*(\d+)(?!\d)', "dian"),
            # "七点八" 格式
            (r'([一二三四五六七八九十零]+)\s*点\s*([一二三四五六七八九十零]+)', "chinese_dian"),
            # "血糖8.5" 或 "血糖7.8"
            (r'血糖?\s*(\d+(?:\.\d+)?)', "numeric"),
            # "血糖八" 中文数字
            (r'血糖?\s*([一二三四五六七八九十零百]+)(?!\s*点)', "chinese"),
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if ptype == "numeric":
                        value = float(match.group(1))
                    elif ptype == "dian":
                        value = float(f"{match.group(1)}.{match.group(2)}")
                    elif ptype == "chinese":
                        value = float(self._cn_number_to_arabic(match.group(1)))
                    elif ptype == "chinese_dian":
                        integer = self._cn_number_to_arabic(match.group(1))
                        decimal = self._cn_number_to_arabic(match.group(2))
                        value = float(f"{integer}.{decimal}")
                    else:
                        continue
                    return {"value": value, "unit": "mmol/L"}
                except (ValueError, IndexError):
                    continue
        return None

    async def _extract_glucose_llm(self, text: str) -> Optional[Dict]:
        """使用 LLM 抽取血糖"""
        system_prompt = """你是一个专业的医疗健康助手。请从用户的语音文本中抽取血糖值。

规则：
1. 单位默认为 mmol/L
2. 血糖 < 3.9 为低血糖 (is_low=true)
3. 空腹血糖 > 7.0 或餐后2h > 11.1 为高血糖 (is_high=true)
4. 只返回 JSON 格式，不要其他文字"""

        user_prompt = f"""请从以下文本中抽取血糖值：

"{text}"

返回格式：
{{"value": 数值, "unit": "mmol/L", "is_low": false, "is_high": false}}

如果没有血糖值，返回 value=0"""

        try:
            response = await self._call_llm(system_prompt, user_prompt, temperature=0)
            # 解析 JSON 响应
            json_str = self._parse_json(response)
            if json_str and "value" in json_str:
                return json_str
        except Exception as e:
            logger.warning(f"LLM 解析失败: {e}")
        return None

    async def _normalize_glucose(self, result: Dict) -> Dict:
        """标准化血糖结果"""
        value = result.get("value", 0)
        return {
            "value": round(value, 1),
            "unit": "mmol/L",
            "is_low": value < 3.9,
            "is_high": value > 11.1
        }

    def _extract_glucose_fallback(self, text: str) -> Dict:
        """降级抽取 - 提取所有数字"""
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            value = float(numbers[0])
            # 合理性检查：血糖通常在 1-30 之间
            if 0.5 <= value <= 30:
                return {
                    "value": round(value, 1),
                    "unit": "mmol/L",
                    "is_low": value < 3.9,
                    "is_high": value > 11.1
                }
        return {"value": 0, "unit": "mmol/L", "is_low": False, "is_high": False}

    # ========== 血压抽取 ==========

    async def extract_blood_pressure(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取血压值

        支持多种表达：
        - "血压135到85"
        - "血压135/85"
        - "高压150低压95"
        """
        # 先尝试正则抽取
        result = self._extract_pressure_regex(text)
        if result and result.get("systolic", 0) > 0:
            return await self._normalize_pressure(result)

        # LLM 抽取
        try:
            result = await self._extract_pressure_llm(text)
            if result and result.get("systolic", 0) > 0:
                return result
        except Exception as e:
            logger.warning(f"LLM 血压抽取失败: {e}")

        # 最终降级方案
        return self._extract_pressure_fallback(text)

    def _extract_pressure_regex(self, text: str) -> Optional[Dict]:
        """正则抽取血压"""
        patterns = [
            # "135/85" 格式
            r'(\d{2,3})\s*/\s*(\d{2,3})',
            # "135到85" 或 "135至85"
            r'(\d{2,3})\s*[到至]\s*(\d{2,3})',
            # "高压135低压85"
            r'高压\s*(\d{2,3})\s*(?:低压|低压是|的)\s*(\d{2,3})',
            # "收缩压135舒张压85"
            r'收缩压\s*(\d{2,3})\s*舒张压\s*(\d{2,3})',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    systolic = int(match.group(1))
                    diastolic = int(match.group(2))
                    # 合理性检查
                    if 50 <= systolic <= 300 and 30 <= diastolic <= 200:
                        return {"systolic": systolic, "diastolic": diastolic}
                except ValueError:
                    continue
        return None

    async def _extract_pressure_llm(self, text: str) -> Optional[Dict]:
        """使用 LLM 抽取血压"""
        system_prompt = """你是一个专业的医疗健康助手。请从用户的语音文本中抽取血压值。

血压等级标准：
- 正常 (normal): < 120/80
- 高值 (elevated): 收缩压 120-129 且 舒张压 < 80
- 高血压1期 (high_1): 收缩压 130-139 或 舒张压 80-89
- 高血压2期 (high_2): ≥ 140/90

只返回 JSON 格式，不要其他文字"""

        user_prompt = f"""请从以下文本中抽取血压值：

"{text}"

返回格式：
{{"systolic": 收缩压, "diastolic": 舒张压, "level": "normal|elevated|high_1|high_2"}}

如果没有血压值，返回 systolic=0, diastolic=0"""

        try:
            response = await self._call_llm(system_prompt, user_prompt, temperature=0)
            json_str = self._parse_json(response)
            if json_str and "systolic" in json_str:
                return json_str
        except Exception as e:
            logger.warning(f"LLM 血压解析失败: {e}")
        return None

    async def _normalize_pressure(self, result: Dict) -> Dict:
        """标准化血压结果"""
        systolic = result.get("systolic", 0)
        diastolic = result.get("diastolic", 0)

        # 判断等级
        if systolic < 120 and diastolic < 80:
            level = "normal"
        elif systolic < 130 and diastolic < 80:
            level = "elevated"
        elif systolic < 140 or diastolic < 90:
            level = "high_1"
        else:
            level = "high_2"

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "level": level
        }

    def _extract_pressure_fallback(self, text: str) -> Dict:
        """降级抽取"""
        numbers = re.findall(r'\d{2,3}', text)
        if len(numbers) >= 2:
            systolic = int(numbers[0])
            diastolic = int(numbers[1])
            if 50 <= systolic <= 300 and 30 <= diastolic <= 200:
                return {
                    "systolic": systolic,
                    "diastolic": diastolic,
                    "level": "unknown"
                }
        return {"systolic": 0, "diastolic": 0, "level": "unknown"}

    # ========== 体温抽取 ==========

    async def extract_temperature(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取体温

        支持多种表达：
        - "体温37度5"
        - "体温38.2"
        - "发烧39度"
        """
        # 正则抽取
        result = self._extract_temperature_regex(text)
        if result and result.get("value", 0) > 0:
            return self._normalize_temperature(result)

        # LLM 抽取
        try:
            result = await self._extract_temperature_llm(text)
            if result and result.get("value", 0) > 0:
                return result
        except Exception as e:
            logger.warning(f"LLM 体温抽取失败: {e}")

        return {"value": 0, "unit": "°C", "is_fever": False}

    def _extract_temperature_regex(self, text: str) -> Optional[Dict]:
        """正则抽取体温"""
        patterns = [
            # "37度5" 或 "37.5"
            (r'(\d{2})\s*度\s*(\d)', "dian_decimal"),
            # "37.5"
            (r'(\d{2}\.?\d*)\s*度', "decimal"),
            # 发烧相关数字
            (r'发烧\s*(\d{2})\s*度', "fever"),
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if ptype == "dian_decimal":
                        value = float(f"{match.group(1)}.{match.group(2)}")
                    else:
                        value = float(match.group(1))
                    # 合理性检查：体温通常在 35-42 之间
                    if 35 <= value <= 42:
                        return {"value": value, "unit": "°C"}
                except ValueError:
                    continue
        return None

    async def _extract_temperature_llm(self, text: str) -> Optional[Dict]:
        """使用 LLM 抽取体温"""
        system_prompt = """你是一个专业的医疗健康助手。请从用户的语音文本中抽取体温值。

规则：
- 体温 > 37.3 为发烧 (is_fever=true)
- 只返回 JSON 格式"""

        user_prompt = f"""请从以下文本中抽取体温值：

"{text}"

返回格式：
{{"value": 数值, "unit": "°C", "is_fever": false}}

如果没有体温值，返回 value=0"""

        try:
            response = await self._call_llm(system_prompt, user_prompt, temperature=0)
            json_str = self._parse_json(response)
            if json_str and "value" in json_str:
                return json_str
        except Exception as e:
            logger.warning(f"LLM 体温解析失败: {e}")
        return None

    def _normalize_temperature(self, result: Dict) -> Dict:
        """标准化体温结果"""
        value = result.get("value", 0)
        return {
            "value": round(value, 1),
            "unit": "°C",
            "is_fever": value > 37.3
        }

    # ========== 体重抽取 ==========

    async def extract_weight(self, text: str) -> Dict[str, Any]:
        """
        从语音文本中抽取体重

        支持多种表达：
        - "体重65公斤"
        - "体重130斤" (会转换为kg)
        - "体重70kg"
        """
        # 正则抽取
        result = self._extract_weight_regex(text)
        if result and result.get("value", 0) > 0:
            return self._normalize_weight(result)

        # LLM 抽取
        try:
            result = await self._extract_weight_llm(text)
            if result and result.get("value", 0) > 0:
                return result
        except Exception as e:
            logger.warning(f"LLM 体重抽取失败: {e}")

        return {"value": 0, "unit": "kg"}

    def _extract_weight_regex(self, text: str) -> Optional[Dict]:
        """正则抽取体重"""
        patterns = [
            # "65公斤" 或 "65kg"
            (r'体重\s*(\d+(?:\.\d+)?)\s*(?:公斤|kg|KG)', "kg"),
            # "130斤"
            (r'体重\s*(\d+(?:\.\d+)?)\s*斤', "jin"),
            # "130" 单独数字（需要上下文）
            (r'体重\s*(\d+(?:\.\d+)?)', "numeric"),
        ]

        for pattern, ptype in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1))
                    # 合理性检查：体重通常在 20-200 公斤
                    if ptype == "jin":
                        value = value / 2  # 斤转公斤
                    if 20 <= value <= 200:
                        return {"value": value, "unit": "kg"}
                except ValueError:
                    continue
        return None

    async def _extract_weight_llm(self, text: str) -> Optional[Dict]:
        """使用 LLM 抽取体重"""
        system_prompt = """你是一个专业的医疗健康助手。请从用户的语音文本中抽取体重值。

规则：
- 单位统一为 kg (公斤)
- 如果输入是斤，需要除以2转换为公斤
- 只返回 JSON 格式"""

        user_prompt = f"""请从以下文本中抽取体重值：

"{text}"

返回格式：
{{"value": 数值, "unit": "kg"}}

如果没有体重值，返回 value=0"""

        try:
            response = await self._call_llm(system_prompt, user_prompt, temperature=0)
            json_str = self._parse_json(response)
            if json_str and "value" in json_str:
                return json_str
        except Exception as e:
            logger.warning(f"LLM 体重解析失败: {e}")
        return None

    def _normalize_weight(self, result: Dict) -> Dict:
        """标准化体重结果"""
        value = result.get("value", 0)
        return {
            "value": round(value, 1),
            "unit": "kg"
        }

    # ========== 通用工具方法 ==========

    def _cn_number_to_arabic(self, cn: str) -> int:
        """中文数字转阿拉伯数字"""
        if cn in self.cn_numbers:
            return self.cn_numbers[cn]

        # 处理"十"开头的数字
        if cn.startswith("十"):
            if len(cn) == 1:
                return 10
            return 10 + self.cn_numbers.get(cn[1], 0)

        # 处理"二十"、"三十"等
        for cn_char, arabic in self.cn_numbers.items():
            if cn.startswith(cn_char) and cn.endswith("十"):
                if len(cn) == 1:
                    return arabic * 10
                remaining = cn[1:]
                if remaining in self.cn_numbers:
                    return arabic * 10 + self.cn_numbers[remaining]

        return 0

    def _parse_json(self, text: str) -> Optional[Dict]:
        """
        解析 JSON 响应

        处理可能的 markdown 代码块包装
        """
        import json

        if not text:
            return None

        # 移除 markdown 代码块
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) > 1:
                text = "\n".join(lines[1:-1]) if text.endswith("```") else "\n".join(lines[1:])
        text = text.strip()

        # 移除可能的 "json:" 前缀
        if text.startswith("json:"):
            text = text[5:].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试提取 JSON 对象
            match = re.search(r'\{[^{}]*\}', text)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    # ========== 批量抽取 ==========

    async def extract_all_values(self, text: str) -> Dict[str, Any]:
        """
        从文本中批量抽取所有健康指标

        返回：
        {
            "blood_glucose": {...} or None,
            "blood_pressure": {...} or None,
            "temperature": {...} or None,
            "weight": {...} or None
        }
        """
        results = {}

        # 血糖
        glucose = await self.extract_blood_glucose(text)
        if glucose.get("value", 0) > 0:
            results["blood_glucose"] = glucose

        # 血压
        pressure = await self.extract_blood_pressure(text)
        if pressure.get("systolic", 0) > 0:
            results["blood_pressure"] = pressure

        # 体温
        temp = await self.extract_temperature(text)
        if temp.get("value", 0) > 0:
            results["temperature"] = temp

        # 体重
        weight = await self.extract_weight(text)
        if weight.get("value", 0) > 0:
            results["weight"] = weight

        return results
