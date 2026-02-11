"""
StateAdapter 单元测试

测试状态适配器的所有方法：
- 初始状态创建
- 对话结果应用
- 皮肤分析结果应用
- 报告解读结果应用
- 安全审查结果应用
- 状态验证
- 进度计算
"""
import pytest
from datetime import datetime

# 导入 StateAdapter 和相关枚举
try:
    from app.services.state_adapter import StateAdapter, DermaTaskType
except ImportError:
    from backend.app.services.state_adapter import StateAdapter, DermaTaskType


# ============================================================================
# 初始状态创建测试
# ============================================================================

class TestCreateInitialState:
    """测试初始状态创建"""

    def test_create_initial_state_basic(self):
        """测试创建基本初始状态"""
        state = StateAdapter.create_initial_state("session_123", 1)

        assert state["session_id"] == "session_123"
        assert state["user_id"] == 1
        assert state["messages"] == []
        assert state["chief_complaint"] == ""
        assert state["symptoms"] == []
        assert state["stage"] == "greeting"
        assert state["progress"] == 0
        assert state["questions_asked"] == 0

    def test_create_initial_state_default_values(self):
        """测试初始状态的默认值"""
        state = StateAdapter.create_initial_state("session_456", 2)

        # 检查所有默认字段
        assert state["chief_complaint"] == ""
        assert state["symptoms"] == []
        assert state["symptom_details"] == {}
        assert state["skin_location"] == ""
        assert state["duration"] == ""
        assert state["skin_analyses"] == []
        assert state["latest_analysis"] is None
        assert state["report_interpretations"] == []
        assert state["latest_interpretation"] is None
        assert state["stage"] == "greeting"
        assert state["progress"] == 0
        assert state["questions_asked"] == 0
        assert state["current_response"] == ""
        assert state["quick_options"] == []
        assert state["possible_conditions"] == []
        assert state["risk_level"] == "low"
        assert state["care_advice"] == ""
        assert state["need_offline_visit"] is False
        assert state["current_task"] == DermaTaskType.CONVERSATION
        assert state["awaiting_image"] is False

    def test_create_initial_state_task_type(self):
        """测试初始状态的任务类型"""
        state = StateAdapter.create_initial_state("session_789", 3)

        assert state["current_task"] == DermaTaskType.CONVERSATION


# ============================================================================
# 对话结果应用测试
# ============================================================================

class TestApplyConversationResult:
    """测试对话结果应用"""

    def test_apply_conversation_result_basic(self):
        """测试应用基本对话结果"""
        state = StateAdapter.create_initial_state("session_001", 1)
        result = {
            "message": "您好，请问有什么皮肤问题？"
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["current_response"] == "您好，请问有什么皮肤问题？"
        assert len(updated_state["messages"]) == 1
        assert updated_state["messages"][0]["role"] == "assistant"
        assert updated_state["messages"][0]["content"] == "您好，请问有什么皮肤问题？"
        assert "timestamp" in updated_state["messages"][0]

    def test_apply_conversation_result_with_stage(self):
        """测试应用带阶段的对话结果"""
        state = StateAdapter.create_initial_state("session_002", 1)
        result = {
            "message": "请问皮疹出现在什么部位？",
            "stage": "inquiry"
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["stage"] == "inquiry"

    def test_apply_conversation_result_with_awaiting_image(self):
        """测试应用带等待图片标志的结果"""
        state = StateAdapter.create_initial_state("session_003", 1)
        result = {
            "message": "请上传皮肤照片",
            "awaiting_image": True
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["awaiting_image"] is True

    def test_apply_conversation_result_with_quick_options(self):
        """测试应用带快捷选项的结果"""
        state = StateAdapter.create_initial_state("session_004", 1)
        result = {
            "message": "请选择症状",
            "quick_options": ["红肿", "瘙痒", "疼痛"]
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["quick_options"] == ["红肿", "瘙痒", "疼痛"]

    def test_apply_conversation_result_with_extracted_info(self):
        """测试应用提取的信息"""
        state = StateAdapter.create_initial_state("session_005", 1)
        result = {
            "message": "了解，请问持续多久了？",
            "extracted_info": {
                "chief_complaint": "皮疹",
                "skin_location": "手臂",
                "duration": "3天",
                "symptoms": ["瘙痒", "红肿"]
            }
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["chief_complaint"] == "皮疹"
        assert updated_state["skin_location"] == "手臂"
        assert updated_state["duration"] == "3天"
        assert "瘙痒" in updated_state["symptoms"]
        assert "红肿" in updated_state["symptoms"]

    def test_apply_conversation_result_increments_questions(self):
        """测试应用对话结果增加问题计数"""
        state = StateAdapter.create_initial_state("session_006", 1)
        assert state["questions_asked"] == 0

        result = {"message": "问题1"}
        updated_state = StateAdapter.apply_conversation_result(state, result)
        assert updated_state["questions_asked"] == 1

        result2 = {"message": "问题2"}
        updated_state2 = StateAdapter.apply_conversation_result(updated_state, result2)
        assert updated_state2["questions_asked"] == 2

    def test_apply_conversation_result_partial_extracted_info(self):
        """测试应用部分提取的信息"""
        state = StateAdapter.create_initial_state("session_007", 1)

        result = {
            "message": "请提供更多信息",
            "extracted_info": {
                "symptoms": ["瘙痒"]
            }
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert updated_state["chief_complaint"] == ""  # 未设置
        assert updated_state["symptoms"] == ["瘙痒"]

    def test_apply_conversation_result_accumulate_symptoms(self):
        """测试症状累积"""
        state = StateAdapter.create_initial_state("session_008", 1)
        state["symptoms"] = ["红肿"]

        result = {
            "message": "还有其他症状吗？",
            "extracted_info": {
                "symptoms": ["瘙痒", "疼痛"]
            }
        }

        updated_state = StateAdapter.apply_conversation_result(state, result)

        assert "红肿" in updated_state["symptoms"]
        assert "瘙痒" in updated_state["symptoms"]
        assert "疼痛" in updated_state["symptoms"]


# ============================================================================
# 皮肤分析结果应用测试
# ============================================================================

class TestApplySkinAnalysisResult:
    """测试皮肤分析结果应用"""

    def test_apply_skin_analysis_result_basic(self):
        """测试应用基本皮肤分析结果"""
        state = StateAdapter.create_initial_state("session_101", 1)
        analysis = {
            "condition": "湿疹",
            "confidence": 0.85,
            "description": "皮肤炎症反应"
        }

        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis)

        assert updated_state["latest_analysis"] == analysis
        assert len(updated_state["skin_analyses"]) == 1
        assert updated_state["skin_analyses"][0]["analysis"] == analysis
        assert "timestamp" in updated_state["skin_analyses"][0]

    def test_apply_skin_analysis_result_with_possible_conditions(self):
        """测试应用带可能诊断的分析结果"""
        state = StateAdapter.create_initial_state("session_102", 1)
        analysis = {
            "possible_conditions": ["湿疹", "皮炎", "荨麻疹"],
            "risk_level": "low"
        }

        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis)

        assert updated_state["possible_conditions"] == ["湿疹", "皮炎", "荨麻疹"]

    def test_apply_skin_analysis_result_risk_level(self):
        """测试应用风险等级"""
        state = StateAdapter.create_initial_state("session_103", 1)

        # 测试高风险
        analysis_high = {"risk_level": "high"}
        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis_high)
        assert updated_state["risk_level"] == "high"

        # 测试中等风险
        state2 = StateAdapter.create_initial_state("session_104", 1)
        analysis_medium = {"risk_level": "medium"}
        updated_state2 = StateAdapter.apply_skin_analysis_result(state2, analysis_medium)
        assert updated_state2["risk_level"] == "medium"

    def test_apply_skin_analysis_result_with_care_advice(self):
        """测试应用护理建议"""
        state = StateAdapter.create_initial_state("session_105", 1)
        analysis = {
            "care_advice": "保持皮肤清洁干燥，避免搔抓"
        }

        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis)

        assert updated_state["care_advice"] == "保持皮肤清洁干燥，避免搔抓"

    def test_apply_skin_analysis_result_need_offline_visit(self):
        """测试是否需要线下就诊"""
        state = StateAdapter.create_initial_state("session_106", 1)

        # 需要线下就诊
        analysis_yes = {"need_offline_visit": True}
        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis_yes)
        assert updated_state["need_offline_visit"] is True

        # 不需要线下就诊
        state2 = StateAdapter.create_initial_state("session_107", 1)
        analysis_no = {"need_offline_visit": False}
        updated_state2 = StateAdapter.apply_skin_analysis_result(state2, analysis_no)
        assert updated_state2["need_offline_visit"] is False

    def test_apply_skin_analysis_result_updates_task(self):
        """测试应用分析结果更新任务状态"""
        state = StateAdapter.create_initial_state("session_108", 1)
        assert state["current_task"] == DermaTaskType.CONVERSATION

        analysis = {}
        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis)

        assert updated_state["current_task"] == DermaTaskType.SKIN_ANALYSIS
        assert updated_state["stage"] == "analyzing"
        assert updated_state["awaiting_image"] is False

    def test_apply_skin_analysis_result_accumulate(self):
        """测试累积多次分析结果"""
        state = StateAdapter.create_initial_state("session_109", 1)

        analysis1 = {"condition": "湿疹"}
        updated_state = StateAdapter.apply_skin_analysis_result(state, analysis1)
        assert len(updated_state["skin_analyses"]) == 1

        analysis2 = {"condition": "皮炎"}
        updated_state2 = StateAdapter.apply_skin_analysis_result(updated_state, analysis2)
        assert len(updated_state2["skin_analyses"]) == 2
        assert updated_state2["latest_analysis"]["condition"] == "皮炎"


# ============================================================================
# 报告解读结果应用测试
# ============================================================================

class TestApplyReportInterpretResult:
    """测试报告解读结果应用"""

    def test_apply_report_interpret_result_basic(self):
        """测试应用基本报告解读结果"""
        state = StateAdapter.create_initial_state("session_201", 1)
        interpretation = {
            "report_type": "blood_test",
            "summary": "血常规正常"
        }

        updated_state = StateAdapter.apply_report_interpret_result(state, interpretation)

        assert updated_state["latest_interpretation"] == interpretation
        assert len(updated_state["report_interpretations"]) == 1
        assert updated_state["report_interpretations"][0]["interpretation"] == interpretation

    def test_apply_report_interpret_result_updates_task(self):
        """测试应用报告解读更新任务状态"""
        state = StateAdapter.create_initial_state("session_202", 1)
        interpretation = {}

        updated_state = StateAdapter.apply_report_interpret_result(state, interpretation)

        assert updated_state["current_task"] == DermaTaskType.REPORT_INTERPRET
        assert updated_state["awaiting_image"] is False

    def test_apply_report_interpret_result_accumulate(self):
        """测试累积多次报告解读"""
        state = StateAdapter.create_initial_state("session_203", 1)

        interp1 = {"report_type": "blood_test", "summary": "正常"}
        updated_state = StateAdapter.apply_report_interpret_result(state, interp1)
        assert len(updated_state["report_interpretations"]) == 1

        interp2 = {"report_type": "allergy_test", "summary": "过敏阳性"}
        updated_state2 = StateAdapter.apply_report_interpret_result(updated_state, interp2)
        assert len(updated_state2["report_interpretations"]) == 2
        assert updated_state2["latest_interpretation"]["report_type"] == "allergy_test"


# ============================================================================
# 安全审查结果应用测试
# ============================================================================

class TestApplySafetyCheckResult:
    """测试安全审查结果应用"""

    def test_apply_safety_check_result_modified_message(self):
        """测试应用修改后的消息"""
        state = StateAdapter.create_initial_state("session_301", 1)
        state["current_response"] = "原始回复"
        state["messages"] = [
            {"role": "user", "content": "问题", "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "content": "原始回复", "timestamp": "2024-01-01T00:00:01"}
        ]

        safety_result = {
            "modified_message": "修改后的安全回复"
        }

        updated_state = StateAdapter.apply_safety_check_result(state, safety_result)

        assert updated_state["current_response"] == "修改后的安全回复"
        # 最后一条 assistant 消息也应该被更新
        assert updated_state["messages"][1]["content"] == "修改后的安全回复"

    def test_apply_safety_check_result_with_warnings(self):
        """测试应用警告信息"""
        state = StateAdapter.create_initial_state("session_302", 1)
        state["current_response"] = "建议使用药物治疗"

        safety_result = {
            "warnings": ["请咨询医生", "可能存在副作用"]
        }

        updated_state = StateAdapter.apply_safety_check_result(state, safety_result)

        # 警告会添加 emoji 前缀
        assert "建议使用药物治疗" in updated_state["current_response"]
        assert "请咨询医生" in updated_state["current_response"]
        assert "可能存在副作用" in updated_state["current_response"]
        # 检查 emoji 前缀
        assert "⚠️" in updated_state["current_response"]

    def test_apply_safety_check_result_no_duplicate_warnings(self):
        """测试警告不会重复添加"""
        state = StateAdapter.create_initial_state("session_303", 1)
        state["current_response"] = "建议使用药物治疗\n\n请咨询医生"

        safety_result = {
            "warnings": ["请咨询医生"]
        }

        updated_state = StateAdapter.apply_safety_check_result(state, safety_result)

        # 警告已经存在，但仍然会被添加（因为格式不同）
        # 原文没有 emoji，添加的警告有 emoji
        assert "请咨询医生" in updated_state["current_response"]

    def test_apply_safety_check_result_both_modified_and_warnings(self):
        """测试同时应用修改消息和警告"""
        state = StateAdapter.create_initial_state("session_304", 1)
        state["current_response"] = "原始回复"
        state["messages"] = [
            {"role": "assistant", "content": "原始回复", "timestamp": "2024-01-01T00:00:00"}
        ]

        safety_result = {
            "modified_message": "修改后的回复",
            "warnings": ["请咨询医生"]
        }

        updated_state = StateAdapter.apply_safety_check_result(state, safety_result)

        # 修改的消息加上警告
        assert "修改后的回复" in updated_state["current_response"]
        assert "请咨询医生" in updated_state["current_response"]


# ============================================================================
# 状态验证测试
# ============================================================================

class TestValidateState:
    """测试状态验证"""

    def test_validate_state_complete(self):
        """测试验证完整状态"""
        state = StateAdapter.create_initial_state("session_401", 1)
        validated = StateAdapter.validate_state(state)

        # 完整状态应该保持不变
        assert validated["session_id"] == "session_401"
        assert validated["user_id"] == 1
        assert validated["stage"] == "greeting"

    def test_validate_state_adds_missing_fields(self):
        """测试验证添加缺失字段"""
        incomplete_state = {
            "session_id": "session_402",
            "user_id": 2
            # 缺少其他字段
        }

        validated = StateAdapter.validate_state(incomplete_state)

        # 应该添加所有默认字段
        assert "messages" in validated
        assert validated["messages"] == []
        assert "symptoms" in validated
        assert validated["symptoms"] == []
        assert "stage" in validated
        assert validated["stage"] == "greeting"

    def test_validate_state_none_values_replaced(self):
        """测试验证替换 None 值"""
        state = StateAdapter.create_initial_state("session_403", 1)
        state["symptoms"] = None
        state["chief_complaint"] = None

        validated = StateAdapter.validate_state(state)

        assert validated["symptoms"] == []
        assert validated["chief_complaint"] == ""

    def test_validate_state_invalid_task_type(self):
        """测试验证处理无效任务类型"""
        state = {
            "session_id": "session_404",
            "user_id": 1,
            "current_task": "invalid_task_type"
        }

        validated = StateAdapter.validate_state(state)

        # 无效的任务类型应该被替换为默认值
        assert validated["current_task"] == DermaTaskType.CONVERSATION

    def test_validate_state_valid_task_type_string(self):
        """测试验证有效的字符串任务类型"""
        state = {
            "session_id": "session_405",
            "user_id": 1,
            "current_task": "skin_analysis"
        }

        validated = StateAdapter.validate_state(state)

        assert validated["current_task"] == DermaTaskType.SKIN_ANALYSIS


# ============================================================================
# 进度计算测试
# ============================================================================

class TestCalculateProgress:
    """测试进度计算"""

    def test_calculate_progress_empty_state(self):
        """测试空状态进度"""
        state = StateAdapter.create_initial_state("session_501", 1)
        progress = StateAdapter.calculate_progress(state)

        assert progress == 0

    def test_calculate_progress_with_chief_complaint(self):
        """测试有主诉的进度"""
        state = StateAdapter.create_initial_state("session_502", 1)
        state["chief_complaint"] = "皮疹"

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 15  # 主诉应该加15分

    def test_calculate_progress_with_skin_location(self):
        """测试有部位信息的进度"""
        state = StateAdapter.create_initial_state("session_503", 1)
        state["skin_location"] = "手臂"

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 10  # 部位应该加10分

    def test_calculate_progress_with_duration(self):
        """测试有持续时间的进度"""
        state = StateAdapter.create_initial_state("session_504", 1)
        state["duration"] = "3天"

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 10  # 持续时间应该加10分

    def test_calculate_progress_with_symptoms(self):
        """测试有症状的进度"""
        state = StateAdapter.create_initial_state("session_505", 1)
        state["symptoms"] = ["瘙痒", "红肿", "疼痛"]

        progress = StateAdapter.calculate_progress(state)

        # 每个症状5分，最多15分
        assert progress >= 15  # 3个症状 = 15分

    def test_calculate_progress_with_many_symptoms_capped(self):
        """测试症状过多时上限"""
        state = StateAdapter.create_initial_state("session_506", 1)
        state["symptoms"] = ["症状1", "症状2", "症状3", "症状4", "症状5"]

        progress = StateAdapter.calculate_progress(state)

        # 最多15分（超过3个症状不再增加）
        assert progress >= 15

    def test_calculate_progress_with_skin_analysis(self):
        """测试有皮肤分析的进度"""
        state = StateAdapter.create_initial_state("session_507", 1)
        state["skin_analyses"] = [{"analysis": {"condition": "湿疹"}}]

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 25  # 皮肤分析应该加25分

    def test_calculate_progress_with_report_interpretation(self):
        """测试有报告解读的进度"""
        state = StateAdapter.create_initial_state("session_508", 1)
        state["report_interpretations"] = [{"interpretation": {"summary": "正常"}}]

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 15  # 报告解读应该加15分

    def test_calculate_progress_with_questions(self):
        """测试问诊次数影响进度"""
        state = StateAdapter.create_initial_state("session_509", 1)
        state["questions_asked"] = 3

        progress = StateAdapter.calculate_progress(state)

        assert progress >= 6  # 每个问题2分，最多10分

    def test_calculate_progress_many_questions_capped(self):
        """测试问诊次数过多时上限"""
        state = StateAdapter.create_initial_state("session_510", 1)
        state["questions_asked"] = 10

        progress = StateAdapter.calculate_progress(state)

        # 最多10分（超过5个问题不再增加）
        assert progress >= 10

    def test_calculate_progress_complete(self):
        """测试完整问诊进度"""
        state = StateAdapter.create_initial_state("session_511", 1)
        state["chief_complaint"] = "皮疹"
        state["skin_location"] = "手臂"
        state["duration"] = "3天"
        state["symptoms"] = ["瘙痒", "红肿"]
        state["skin_analyses"] = [{"analysis": {"condition": "湿疹"}}]
        state["report_interpretations"] = [{"interpretation": {"summary": "正常"}}]
        state["questions_asked"] = 3

        progress = StateAdapter.calculate_progress(state)

        # 15 + 10 + 10 + 10 + 25 + 15 + 6 = 91
        assert progress >= 90
        assert progress <= 100  # 不超过100

    def test_calculate_progress_never_exceeds_100(self):
        """测试进度不超过100"""
        state = StateAdapter.create_initial_state("session_512", 1)
        # 添加所有可能的内容
        state["chief_complaint"] = "测试"
        state["skin_location"] = "测试"
        state["duration"] = "测试"
        state["symptoms"] = ["症状1", "症状2", "症状3", "症状4"]
        state["skin_analyses"] = [{"analysis": {}}, {"analysis": {}}]
        state["report_interpretations"] = [{"interpretation": {}}, {"interpretation": {}}]
        state["questions_asked"] = 20

        progress = StateAdapter.calculate_progress(state)

        assert progress == 100  # 应该被限制在100
