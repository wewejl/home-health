"""
AI 算法服务测试脚本

测试：
- AI 摘要服务
- 智能事件聚合服务
- 语音转写服务

使用方法：
    python -m pytest test/test_ai_services.py -v
    或
    python test/test_ai_services.py
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ai.summary_service import AISummaryService, get_summary_service
from app.services.ai.aggregation_service import EventAggregationService, get_aggregation_service
from app.services.ai.transcription_service import SpeechTranscriptionService, get_transcription_service


class TestAISummaryService:
    """AI 摘要服务测试"""
    
    def setup_method(self):
        self.service = get_summary_service()
    
    async def test_generate_summary_basic(self):
        """测试基础摘要生成"""
        result = await self.service.generate_summary(
            chief_complaint="头痛，持续2天",
            department="神经内科",
            sessions=[
                {
                    "session_id": "test-001",
                    "session_type": "diagnosis",
                    "timestamp": "2026-01-14T10:00:00",
                    "summary": "患者描述头痛症状，持续2天，伴有轻微恶心"
                }
            ],
            attachments=[],
            notes=[]
        )
        
        assert result is not None
        assert result.summary != ""
        print(f"✅ 摘要生成成功: {result.summary[:100]}...")
        print(f"   症状: {result.symptoms}")
        print(f"   风险等级: {result.risk_level}")
        print(f"   置信度: {result.confidence}")
    
    async def test_extract_symptoms(self):
        """测试症状提取"""
        conversation = """
        患者: 我最近头痛得厉害，已经持续3天了。
        医生: 是什么样的头痛？是胀痛还是刺痛？
        患者: 主要是胀痛，在太阳穴附近，还有点恶心。
        医生: 有没有发烧或者视力模糊的情况？
        患者: 没有发烧，但是看东西有时候会有点花。
        """
        
        result = await self.service.extract_symptoms(conversation)
        
        assert "symptoms" in result
        print(f"✅ 症状提取成功: {result}")
    
    async def test_generate_timeline(self):
        """测试时间轴生成"""
        timeline = await self.service.generate_timeline(
            chief_complaint="皮肤红疹",
            sessions=[
                {
                    "session_id": "s1",
                    "timestamp": "2026-01-10T08:00:00",
                    "summary": "首次发现红疹"
                },
                {
                    "session_id": "s2",
                    "timestamp": "2026-01-12T10:00:00",
                    "summary": "红疹扩散，用药后有所缓解"
                }
            ],
            attachments=[
                {
                    "type": "image",
                    "upload_time": "2026-01-10T08:30:00",
                    "description": "红疹照片"
                }
            ],
            notes=[
                {
                    "content": "已按建议涂抹药膏",
                    "is_important": True,
                    "created_at": "2026-01-11T15:00:00"
                }
            ]
        )
        
        assert len(timeline) > 0
        print(f"✅ 时间轴生成成功: {len(timeline)} 个事件")
        for event in timeline:
            print(f"   - {event.timestamp}: {event.title}")


class TestEventAggregationService:
    """智能事件聚合服务测试"""
    
    def setup_method(self):
        self.service = get_aggregation_service()
    
    async def test_analyze_relation_same_day(self):
        """测试同一天事件关联分析"""
        event_a = {
            "id": "event-001",
            "title": "皮肤科 2026-01-14",
            "department": "皮肤科",
            "chief_complaint": "皮肤红疹",
            "symptoms": ["红疹", "瘙痒"],
            "start_time": "2026-01-14T08:00:00",
            "summary": "皮肤出现红疹，伴有瘙痒"
        }
        
        event_b = {
            "id": "event-002",
            "title": "皮肤科 2026-01-14",
            "department": "皮肤科",
            "chief_complaint": "皮肤红疹加重",
            "symptoms": ["红疹", "脱皮"],
            "start_time": "2026-01-14T14:00:00",
            "summary": "红疹范围扩大"
        }
        
        result = await self.service.analyze_relation(event_a, event_b)
        
        assert result["is_related"] == True
        assert result["confidence"] >= 0.9
        print(f"✅ 同天事件关联分析: {result}")
    
    async def test_smart_aggregate(self):
        """测试智能聚合"""
        session_info = {
            "session_id": "new-session",
            "session_type": "derma",
            "department": "皮肤科",
            "chief_complaint": "皮肤红疹",
            "timestamp": "2026-01-14T10:00:00"
        }
        
        existing_events = [
            {
                "id": "existing-001",
                "title": "皮肤科 2026-01-14",
                "department": "皮肤科",
                "chief_complaint": "皮肤问题",
                "start_time": "2026-01-14T08:00:00",
                "status": "active"
            },
            {
                "id": "existing-002",
                "title": "骨科 2026-01-13",
                "department": "骨科",
                "chief_complaint": "腰痛",
                "start_time": "2026-01-13T09:00:00",
                "status": "active"
            }
        ]
        
        result = await self.service.smart_aggregate(session_info, existing_events)
        
        assert result.suggested_action == "add_to_existing"
        assert result.target_event_id == "existing-001"
        print(f"✅ 智能聚合: action={result.suggested_action}, target={result.target_event_id}")
    
    async def test_generate_merged_summary(self):
        """测试合并摘要生成"""
        events = [
            {
                "id": "e1",
                "title": "皮肤红疹 Day1",
                "department": "皮肤科",
                "chief_complaint": "发现皮肤红疹",
                "start_time": "2026-01-10T08:00:00",
                "summary": "首次发现红疹",
                "risk_level": "low"
            },
            {
                "id": "e2",
                "title": "皮肤红疹 Day3",
                "department": "皮肤科",
                "chief_complaint": "红疹加重",
                "start_time": "2026-01-12T10:00:00",
                "summary": "红疹范围扩大，开始用药",
                "risk_level": "medium"
            }
        ]
        
        result = await self.service.generate_merged_summary(events)
        
        assert result.merged_title != ""
        assert result.summary != ""
        print(f"✅ 合并摘要: {result.merged_title}")
        print(f"   摘要: {result.summary[:100]}...")


class TestSpeechTranscriptionService:
    """语音转写服务测试"""
    
    def setup_method(self):
        self.service = get_transcription_service()
    
    def test_validate_audio_file(self):
        """测试音频文件验证"""
        # 有效文件
        is_valid, msg = self.service.validate_audio_file("test.mp3", 1024 * 1024)
        assert is_valid == True
        
        # 无效格式
        is_valid, msg = self.service.validate_audio_file("test.exe", 1024)
        assert is_valid == False
        print(f"✅ 无效格式检测: {msg}")
        
        # 文件过大
        is_valid, msg = self.service.validate_audio_file("test.mp3", 100 * 1024 * 1024)
        assert is_valid == False
        print(f"✅ 文件过大检测: {msg}")
    
    async def test_transcribe_with_llm_processing(self):
        """测试 LLM 后处理"""
        text = "我最近头疼，已经持续三天了，还有点恶心想吐"
        
        result = await self.service.transcribe_with_llm(text)
        
        assert "cleaned_text" in result
        assert "symptoms" in result
        print(f"✅ LLM 后处理: {result}")


async def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("AI 算法服务测试")
    print("=" * 60 + "\n")
    
    # 测试 AI 摘要服务
    print("\n📝 测试 AI 摘要服务\n" + "-" * 40)
    summary_tests = TestAISummaryService()
    summary_tests.setup_method()
    await summary_tests.test_generate_summary_basic()
    await summary_tests.test_extract_symptoms()
    await summary_tests.test_generate_timeline()
    
    # 测试智能聚合服务
    print("\n🔗 测试智能事件聚合服务\n" + "-" * 40)
    agg_tests = TestEventAggregationService()
    agg_tests.setup_method()
    await agg_tests.test_analyze_relation_same_day()
    await agg_tests.test_smart_aggregate()
    await agg_tests.test_generate_merged_summary()
    
    # 测试语音转写服务
    print("\n🎤 测试语音转写服务\n" + "-" * 40)
    trans_tests = TestSpeechTranscriptionService()
    trans_tests.setup_method()
    trans_tests.test_validate_audio_file()
    await trans_tests.test_transcribe_with_llm_processing()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
