"""
数值抽取 Agent 测试

测试从语音识别文本中抽取医嘱相关数值
"""
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.value_extraction_agent import ValueExtractionAgent


@pytest.mark.asyncio
async def test_extract_blood_glucose_numeric():
    """测试血糖值抽取 - 数字格式"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_glucose("血糖8点5")
    assert result["value"] == 8.5
    assert result["unit"] == "mmol/L"

    result = await agent.extract_blood_glucose("血糖7.8")
    assert result["value"] == 7.8

    result = await agent.extract_blood_glucose("血糖6")
    assert result["value"] == 6.0


@pytest.mark.asyncio
async def test_extract_blood_glucose_chinese():
    """测试血糖值抽取 - 中文数字"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_glucose("血糖八")
    assert result["value"] == 8.0

    result = await agent.extract_blood_glucose("血糖七点五")
    assert result["value"] == 7.5


@pytest.mark.asyncio
async def test_extract_blood_glucose_with_context():
    """测试带上下文的血糖值抽取"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_glucose("今天早餐后血糖是8点5")
    assert result["value"] == 8.5

    result = await agent.extract_blood_glucose("刚才测的餐后血糖七点八，有点高")
    assert result["value"] == 7.8


@pytest.mark.asyncio
async def test_glucose_abnormal_detection():
    """测试血糖异常检测"""
    agent = ValueExtractionAgent()

    # 低血糖
    result = await agent.extract_blood_glucose("血糖3.2")
    assert result["value"] == 3.2
    assert result["is_low"] is True

    # 高血糖
    result = await agent.extract_blood_glucose("血糖12")
    assert result["value"] == 12.0
    assert result["is_high"] is True

    # 正常
    result = await agent.extract_blood_glucose("血糖6.5")
    assert result["value"] == 6.5
    assert result["is_low"] is False
    assert result["is_high"] is False


@pytest.mark.asyncio
async def test_extract_blood_pressure_standard():
    """测试血压值抽取 - 标准格式"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_pressure("血压135到85")
    assert result["systolic"] == 135
    assert result["diastolic"] == 85

    result = await agent.extract_blood_pressure("血压120/80")
    assert result["systolic"] == 120
    assert result["diastolic"] == 80


@pytest.mark.asyncio
async def test_extract_blood_pressure_chinese():
    """测试血压值抽取 - 中文描述"""
    agent = ValueExtractionAgent()

    result = await agent.extract_blood_pressure("高压150低压95")
    assert result["systolic"] == 150
    assert result["diastolic"] == 95


@pytest.mark.asyncio
async def test_blood_pressure_level():
    """测试血压等级判断"""
    agent = ValueExtractionAgent()

    # 正常
    result = await agent.extract_blood_pressure("血压115到75")
    assert result["level"] == "normal"

    # 高值
    result = await agent.extract_blood_pressure("血压125到78")
    assert result["level"] == "elevated"

    # 高血压1期
    result = await agent.extract_blood_pressure("血压135到85")
    assert result["level"] == "high_1"

    # 高血压2期
    result = await agent.extract_blood_pressure("血压150到95")
    assert result["level"] == "high_2"


@pytest.mark.asyncio
async def test_extract_temperature():
    """测试体温抽取"""
    agent = ValueExtractionAgent()

    result = await agent.extract_temperature("体温37度5")
    assert result["value"] == 37.5
    assert result["unit"] == "°C"

    result = await agent.extract_temperature("体温38.2，有点发烧")
    assert result["value"] == 38.2
    assert result["is_fever"] is True


@pytest.mark.asyncio
async def test_extract_weight():
    """测试体重抽取"""
    agent = ValueExtractionAgent()

    result = await agent.extract_weight("体重65公斤")
    assert result["value"] == 65
    assert result["unit"] == "kg"

    result = await agent.extract_weight("今天体重130斤")
    assert result["value"] == 65
    assert result["unit"] == "kg"


def test_regex_patterns():
    """测试正则表达式模式（同步测试）"""
    agent = ValueExtractionAgent()

    # 测试中文数字转换
    assert agent._cn_number_to_arabic("一") == 1
    assert agent._cn_number_to_arabic("八") == 8
    assert agent._cn_number_to_arabic("十") == 10
    assert agent._cn_number_to_arabic("十五") == 15


@pytest.mark.asyncio
async def test_invalid_input():
    """测试无效输入"""
    agent = ValueExtractionAgent()

    # 没有数值的输入
    result = await agent.extract_blood_glucose("今天感觉不错")
    assert result["value"] == 0

    result = await agent.extract_blood_pressure("没有测量血压")
    assert result["systolic"] == 0
    assert result["diastolic"] == 0
