"""
StateAdapter - 状态适配器
负责 CrewAI 结果与 DermaState 之间的转换
确保与前端、数据库的兼容性
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class DermaTaskType(str, Enum):
    """皮肤科任务类型"""
    CONVERSATION = "conversation"
    SKIN_ANALYSIS = "skin_analysis"
    REPORT_INTERPRET = "report_interpret"


class StateAdapter:
    """
    状态适配器
    
    负责：
    1. CrewAI 结果 → DermaState 更新
    2. DermaState → DermaResponse Pydantic 对象
    3. 确保数据格式与现有 DB schema 兼容
    """
    
    @staticmethod
    def create_initial_state(session_id: str, user_id: int) -> Dict[str, Any]:
        """创建皮肤科问诊初始状态"""
        return {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "chief_complaint": "",
            "symptoms": [],
            "symptom_details": {},
            "skin_location": "",
            "duration": "",
            "skin_analyses": [],
            "latest_analysis": None,
            "report_interpretations": [],
            "latest_interpretation": None,
            "stage": "greeting",
            "progress": 0,
            "questions_asked": 0,
            "current_response": "",
            "quick_options": [],
            "possible_conditions": [],
            "risk_level": "low",
            "care_advice": "",
            "need_offline_visit": False,
            "current_task": DermaTaskType.CONVERSATION,
            "awaiting_image": False
        }
    
    @staticmethod
    def apply_conversation_result(
        state: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用对话 Agent 结果到状态
        
        Args:
            state: 当前状态
            result: CrewAI 对话结果
            
        Returns:
            更新后的状态
        """
        # 更新回复
        if result.get("message"):
            state["current_response"] = result["message"]
            state["messages"].append({
                "role": "assistant",
                "content": result["message"],
                "timestamp": datetime.now().isoformat()
            })
        
        # 更新阶段
        if result.get("stage"):
            state["stage"] = result["stage"]
        
        # 更新等待图片标志
        state["awaiting_image"] = result.get("awaiting_image", False)
        
        # 更新快捷选项
        if result.get("quick_options"):
            state["quick_options"] = result["quick_options"]
        
        # 应用提取的信息
        extracted = result.get("extracted_info", {})
        if extracted:
            if extracted.get("chief_complaint") and not state.get("chief_complaint"):
                state["chief_complaint"] = extracted["chief_complaint"]
            if extracted.get("skin_location"):
                state["skin_location"] = extracted["skin_location"]
            if extracted.get("duration"):
                state["duration"] = extracted["duration"]
            if extracted.get("symptoms"):
                for symptom in extracted["symptoms"]:
                    if symptom not in state.get("symptoms", []):
                        state.setdefault("symptoms", []).append(symptom)
        
        # 更新问诊计数
        state["questions_asked"] = state.get("questions_asked", 0) + 1
        
        return state
    
    @staticmethod
    def apply_skin_analysis_result(
        state: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用皮肤分析结果到状态
        
        Args:
            state: 当前状态
            analysis: 皮肤分析结果
            
        Returns:
            更新后的状态
        """
        state["latest_analysis"] = analysis
        state.setdefault("skin_analyses", []).append({
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        })
        
        # 更新诊断相关字段
        if analysis.get("possible_conditions"):
            state["possible_conditions"] = analysis["possible_conditions"]
        
        state["risk_level"] = analysis.get("risk_level", "medium")
        state["care_advice"] = analysis.get("care_advice", "")
        state["need_offline_visit"] = analysis.get("need_offline_visit", True)
        
        # 更新任务状态
        state["current_task"] = DermaTaskType.SKIN_ANALYSIS
        state["stage"] = "analyzing"
        state["awaiting_image"] = False
        
        return state
    
    @staticmethod
    def apply_report_interpret_result(
        state: Dict[str, Any],
        interpretation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用报告解读结果到状态
        
        Args:
            state: 当前状态
            interpretation: 报告解读结果
            
        Returns:
            更新后的状态
        """
        state["latest_interpretation"] = interpretation
        state.setdefault("report_interpretations", []).append({
            "timestamp": datetime.now().isoformat(),
            "interpretation": interpretation
        })
        
        # 更新任务状态
        state["current_task"] = DermaTaskType.REPORT_INTERPRET
        state["awaiting_image"] = False
        
        return state
    
    @staticmethod
    def apply_safety_check_result(
        state: Dict[str, Any],
        safety_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用安全审查结果到状态
        
        Args:
            state: 当前状态
            safety_result: 安全审查结果
            
        Returns:
            更新后的状态
        """
        # 如果有修改后的消息，替换当前回复
        if safety_result.get("modified_message"):
            state["current_response"] = safety_result["modified_message"]
            
            # 更新最后一条 assistant 消息
            for i in range(len(state.get("messages", [])) - 1, -1, -1):
                if state["messages"][i].get("role") == "assistant":
                    state["messages"][i]["content"] = safety_result["modified_message"]
                    break
        
        # 添加警告到响应
        warnings = safety_result.get("warnings", [])
        if warnings and state.get("current_response"):
            warning_text = "\n\n" + "\n".join(f"⚠️ {w}" for w in warnings)
            if warning_text not in state["current_response"]:
                state["current_response"] += warning_text
        
        return state
    
    @staticmethod
    def validate_state(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证并规范化状态
        
        确保所有必需字段存在且格式正确
        """
        defaults = {
            "messages": [],
            "chief_complaint": "",
            "symptoms": [],
            "symptom_details": {},
            "skin_location": "",
            "duration": "",
            "skin_analyses": [],
            "latest_analysis": None,
            "report_interpretations": [],
            "latest_interpretation": None,
            "stage": "greeting",
            "progress": 0,
            "questions_asked": 0,
            "current_response": "",
            "quick_options": [],
            "possible_conditions": [],
            "risk_level": "low",
            "care_advice": "",
            "need_offline_visit": False,
            "current_task": DermaTaskType.CONVERSATION,
            "awaiting_image": False
        }
        
        for key, default_value in defaults.items():
            if key not in state or state[key] is None:
                state[key] = default_value
        
        # 确保 current_task 是正确的类型
        if isinstance(state.get("current_task"), str):
            try:
                state["current_task"] = DermaTaskType(state["current_task"])
            except ValueError:
                state["current_task"] = DermaTaskType.CONVERSATION
        
        return state
    
    @staticmethod
    def calculate_progress(state: Dict[str, Any]) -> int:
        """
        计算问诊进度
        
        基于收集的信息量计算 0-100 的进度值
        """
        progress = 0
        
        # 基础信息
        if state.get("chief_complaint"):
            progress += 15
        if state.get("skin_location"):
            progress += 10
        if state.get("duration"):
            progress += 10
        if state.get("symptoms"):
            progress += min(len(state["symptoms"]) * 5, 15)
        
        # 图像分析
        if state.get("skin_analyses"):
            progress += 25
        
        # 报告解读
        if state.get("report_interpretations"):
            progress += 15
        
        # 问诊深度
        questions = state.get("questions_asked", 0)
        progress += min(questions * 2, 10)
        
        return min(progress, 100)


# 全局实例
state_adapter = StateAdapter()
