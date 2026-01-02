"""
AI诊室智能体服务 - 基于LangGraph实现医疗问诊流程
"""
import json
import httpx
from typing import TypedDict, List, Optional, Literal, Callable, Awaitable, AsyncIterator
from datetime import datetime
from ..config import get_settings

settings = get_settings()


class QuickOption(TypedDict):
    """快捷选项"""
    text: str
    value: str
    category: str


class DiagnosisState(TypedDict):
    """问诊状态"""
    consultation_id: str
    user_id: int
    
    # 对话历史
    messages: List[dict]
    
    # 收集的症状信息
    chief_complaint: str
    symptoms: List[str]
    symptom_details: dict
    
    # 问诊进度
    stage: Literal["greeting", "collecting", "deep_inquiry", "diagnosis", "completed"]
    progress: int
    questions_asked: int
    
    # AI生成内容
    current_question: str
    quick_options: List[QuickOption]
    reasoning: str
    
    # 诊断结果
    possible_diseases: List[dict]
    risk_level: Literal["low", "medium", "high", "emergency"]
    recommendations: dict
    
    # 控制标志
    can_conclude: bool
    force_conclude: bool
    
    # AI评估字段（新增）
    should_diagnose: bool
    confidence: int
    missing_info: List[str]


class DiagnosisAgent:
    """AI诊室智能体"""
    
    SYSTEM_PROMPT = """你是一位专业的AI医生助手，正在进行智能问诊。你的任务是通过对话收集患者的症状信息，并给出初步诊断建议。

问诊原则：
1. 一次只问一个问题，问题要简洁明了
2. 从主诉开始，逐步深入了解症状细节
3. 关注症状的持续时间、严重程度、伴随症状
4. 注意识别危险信号（红旗症状）
5. 态度专业、温和、耐心

注意：你的回答仅供参考，不能替代专业医生的诊断。"""

    QUESTION_PROMPT = """基于以下对话历史，生成下一个问诊问题。

当前收集的信息：
- 主诉：{chief_complaint}
- 已收集症状：{symptoms}
- 症状详情：{symptom_details}
- 已提问次数：{questions_asked}

对话历史：
{messages}

要求：
1. 根据已有信息，提出下一个最相关的问题
2. 问题要具体、有针对性
3. 如果信息足够，可以开始总结

请直接输出问题，不要有多余的前缀。"""

    QUICK_OPTIONS_PROMPT = """你刚刚向患者提出了以下问题：
"{question}"

基于这个问题，预测患者最可能的3-5个回答选项。

要求：
1. 选项要覆盖常见情况（肯定/否定/具体描述）
2. 选项要简洁明了，便于点击
3. 必须包含"没有"或"都不符合"这类否定选项
4. 如果是症状描述类问题，提供具体的症状选项
5. **重要：text 和 value 都必须使用中文，不要使用英文或拼音**

请严格按照以下JSON格式返回，不要有其他内容：
{{"options": [{{"text": "选项文本", "value": "选项值", "category": "症状类别"}}]}}

示例：{{"options": [{{"text": "持续2-3天", "value": "持续2-3天", "category": "时间"}}]}}"""

    ASSESSMENT_PROMPT = """评估当前收集的信息是否足够做出初步诊断。

已收集信息：
- 主诉：{chief_complaint}
- 症状列表：{symptoms}
- 症状详情：{symptom_details}
- 已提问次数：{questions_asked}

对话历史：
{messages}

评估标准：
1. 是否收集了主要症状的持续时间、严重程度
2. 是否排除了危险信号（红旗症状）
3. 是否了解了伴随症状
4. 信息是否足够做出初步判断

请综合判断问诊进度和是否应该结束问诊进入诊断阶段。

请严格按照以下JSON格式返回：
{{
    "progress": 0到100的数字（表示问诊完成度，百分比）,
    "should_diagnose": true或false（是否应立即进入诊断阶段）,
    "can_conclude": true或false（当前信息是否足够出诊断）,
    "confidence": 0到100的数字（诊断置信度）,
    "missing_info": ["缺失的关键信息1", "缺失的关键信息2"],
    "reasoning": "评估理由"
}}"""

    INITIAL_OPTIONS_PROMPT = """根据患者的主诉或常见就诊场景，生成4-5个初始快捷选项供患者选择。

当前主诉：{chief_complaint}

要求：
1. 选项应覆盖常见的症状类别
2. 选项要简洁明了，便于点击
3. 必须包含一个"其他症状"或"不确定"类的选项
4. 如果有主诉，选项应与主诉相关；如果没有主诉，提供常见症状类别
5. **重要：text 和 value 都必须使用中文，不要使用英文或拼音**

请严格按照以下JSON格式返回，不要有其他内容：
{{"options": [{{"text": "选项文本", "value": "选项值", "category": "症状类别"}}]}}

示例：{{"options": [{{"text": "咳嗽发烧", "value": "咳嗽发烧", "category": "呼吸系统"}}]}}"""

    DIAGNOSIS_PROMPT = """基于以下患者信息，生成完整的诊断报告。

主诉：{chief_complaint}
症状详情：{symptom_details}
对话历史：{messages}

生成内容包括：
1. 症状总结
2. 可能的疾病（按可能性排序，最多3个）
3. 风险等级评估（low/medium/high/emergency）
4. 就诊建议（科室、紧急程度）
5. 生活建议

请严格按照以下JSON格式返回：
{{
    "summary": "症状总结",
    "diseases": [
        {{"name": "疾病名称", "probability": "可能性描述", "description": "简要说明"}}
    ],
    "risk_level": "low/medium/high/emergency",
    "risk_warning": "风险提示（如果是high或emergency）",
    "recommendations": {{
        "department": "建议就诊科室",
        "urgency": "就诊紧急程度",
        "lifestyle": ["生活建议1", "生活建议2"]
    }}
}}"""

    def __init__(self):
        self.api_url = f"{settings.LLM_BASE_URL}/chat/completions"
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL

    async def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """调用LLM（非流式）"""
        if not self.api_key:
            return ""
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"LLM调用异常: {e}")
        
        return ""

    async def _stream_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> str:
        """
        流式调用LLM，每收到一个token chunk就调用on_chunk回调
        返回完整的累积文本
        """
        if not self.api_key:
            return ""
        
        full_content = ""
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": 1000,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        print(f"LLM流式调用失败: {response.status_code}")
                        return ""
                    
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        full_content += content
                                        if on_chunk:
                                            await on_chunk(content)
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            print(f"LLM流式调用异常: {e}")
        
        return full_content

    def _format_messages(self, messages: List[dict]) -> str:
        """格式化对话历史"""
        formatted = []
        for msg in messages[-10:]:  # 只取最近10条
            role = "患者" if msg.get("role") == "user" else "医生"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n".join(formatted)

    async def generate_initial_options(self, chief_complaint: str = "") -> List[QuickOption]:
        """生成首轮快捷选项 - 由 AI 生成"""
        prompt = self.INITIAL_OPTIONS_PROMPT.format(
            chief_complaint=chief_complaint or "无（用户刚开始问诊）"
        )
        
        response = await self._call_llm(self.SYSTEM_PROMPT, prompt, temperature=0.5)
        
        default_options = [
            {"text": "头痛头晕", "value": "头痛头晕", "category": "神经系统"},
            {"text": "咳嗽发烧", "value": "咳嗽发烧", "category": "呼吸系统"},
            {"text": "胃痛腹泻", "value": "胃痛腹泻", "category": "消化系统"},
            {"text": "皮肤问题", "value": "皮肤问题", "category": "皮肤科"},
            {"text": "其他症状", "value": "其他症状", "category": "其他"}
        ]
        
        try:
            # 处理可能的markdown代码块
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            raw_options = data.get("options", [])
            
            # 确保有"其他/不确定"类选项
            has_other = any(
                "其他" in opt.get("text", "") or "不确定" in opt.get("text", "") 
                for opt in raw_options
            )
            if not has_other:
                raw_options.append({"text": "其他症状", "value": "其他症状", "category": "其他"})
            
            # 强制将 value 设为中文 text，防止 LLM 返回英文 value
            formatted_options = []
            for opt in raw_options:
                text = opt.get("text") or opt.get("value") or ""
                if not text:
                    continue
                formatted_options.append({
                    "text": text,
                    "value": text,  # 强制使用中文 text 作为 value
                    "category": opt.get("category") or "其他"
                })
            
            return formatted_options[:5]  # 最多5个选项
        except (json.JSONDecodeError, KeyError):
            # 解析失败，使用默认选项
            return default_options

    async def greet(self, state: DiagnosisState) -> DiagnosisState:
        """问候患者，开始问诊"""
        greeting = "你好~我是你的AI医生，我将通过深度问诊了解你的健康状况，并提供明确的诊疗建议。\n\n好的，现在请描述病情，你输入的信息越详细，我的回答越精准哦~"
        
        state["current_question"] = greeting
        state["stage"] = "collecting"
        state["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        # 由 AI 生成首轮快捷选项
        state["quick_options"] = await self.generate_initial_options(state.get("chief_complaint", ""))
        
        return state

    async def analyze_input(self, state: DiagnosisState, user_input: str) -> DiagnosisState:
        """分析患者输入"""
        # 记录用户消息
        state["messages"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 更新主诉（如果是第一次输入）
        if not state["chief_complaint"]:
            state["chief_complaint"] = user_input
        
        # 添加到症状列表
        if user_input not in state["symptoms"]:
            state["symptoms"].append(user_input)
        
        state["questions_asked"] += 1
        
        return state

    async def generate_question(
        self,
        state: DiagnosisState,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DiagnosisState:
        """生成下一个问诊问题（支持流式输出）"""
        prompt = self.QUESTION_PROMPT.format(
            chief_complaint=state["chief_complaint"] or "未知",
            symptoms=", ".join(state["symptoms"]) if state["symptoms"] else "无",
            symptom_details=json.dumps(state["symptom_details"], ensure_ascii=False) if state["symptom_details"] else "无",
            questions_asked=state["questions_asked"],
            messages=self._format_messages(state["messages"])
        )
        
        if on_chunk:
            question = await self._stream_llm(self.SYSTEM_PROMPT, prompt, on_chunk=on_chunk)
        else:
            question = await self._call_llm(self.SYSTEM_PROMPT, prompt)
        
        if not question:
            question = "能否详细描述一下您的症状？比如持续时间、严重程度等。"
            if on_chunk:
                await on_chunk(question)
        
        state["current_question"] = question
        state["messages"].append({
            "role": "assistant",
            "content": question,
            "timestamp": datetime.now().isoformat()
        })
        
        return state

    async def generate_quick_options(self, state: DiagnosisState) -> DiagnosisState:
        """生成快捷选项"""
        prompt = self.QUICK_OPTIONS_PROMPT.format(question=state["current_question"])
        
        response = await self._call_llm(self.SYSTEM_PROMPT, prompt, temperature=0.5)
        
        try:
            # 尝试解析JSON
            # 处理可能的markdown代码块
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response.strip())
            raw_options = data.get("options", [])
            
            # 确保有默认选项
            has_negative = any("没有" in opt.get("text", "") or "不" in opt.get("text", "") for opt in raw_options)
            if not has_negative:
                raw_options.append({"text": "都不符合", "value": "都不符合", "category": "其他"})
            
            formatted_options = []
            for opt in raw_options:
                text = opt.get("text") or opt.get("value") or ""
                if not text:
                    continue
                formatted_options.append({
                    "text": text,
                    "value": text,
                    "category": opt.get("category") or "其他"
                })
            
            state["quick_options"] = formatted_options[:5]  # 最多5个选项
        except (json.JSONDecodeError, KeyError):
            # 解析失败，使用默认选项
            state["quick_options"] = [
                {"text": "是的", "value": "是的", "category": "确认"},
                {"text": "没有", "value": "没有", "category": "否定"},
                {"text": "不确定", "value": "不确定", "category": "不确定"},
                {"text": "还有其他", "value": "还有其他", "category": "补充"}
            ]
        
        return state

    async def assess_progress(self, state: DiagnosisState) -> DiagnosisState:
        """评估问诊进度 - 由 AI 驱动评估"""
        prompt = self.ASSESSMENT_PROMPT.format(
            chief_complaint=state["chief_complaint"] or "未知",
            symptoms=", ".join(state["symptoms"]) if state["symptoms"] else "无",
            symptom_details=json.dumps(state["symptom_details"], ensure_ascii=False) if state["symptom_details"] else "无",
            questions_asked=state["questions_asked"],
            messages=self._format_messages(state["messages"])
        )
        
        response = await self._call_llm(self.SYSTEM_PROMPT, prompt, temperature=0.3)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            assessment = json.loads(response.strip())
            
            # 解析 AI 评估的完整字段
            state["progress"] = assessment.get("progress", 0)
            state["should_diagnose"] = assessment.get("should_diagnose", False)
            state["can_conclude"] = assessment.get("can_conclude", False)
            state["confidence"] = assessment.get("confidence", 0)
            state["missing_info"] = assessment.get("missing_info", [])
            state["reasoning"] = assessment.get("reasoning", "")
            
        except (json.JSONDecodeError, KeyError):
            # Fallback: 使用简单策略评估
            questions_asked = state["questions_asked"]
            symptoms_count = len(state["symptoms"])
            
            # 简单进度计算
            state["progress"] = min(20 + questions_asked * 15, 90)
            # 简单诊断触发判断
            state["should_diagnose"] = questions_asked >= 5 and symptoms_count >= 2
            state["can_conclude"] = questions_asked >= 3 and symptoms_count >= 2
            state["confidence"] = min(30 + questions_asked * 10, 70)
            state["missing_info"] = []
            state["reasoning"] = "基于已收集信息进行评估（fallback策略）"
        
        return state

    async def generate_diagnosis(
        self,
        state: DiagnosisState,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DiagnosisState:
        """生成诊断报告（支持流式输出）"""
        prompt = self.DIAGNOSIS_PROMPT.format(
            chief_complaint=state["chief_complaint"] or "未知",
            symptom_details=json.dumps(state["symptom_details"], ensure_ascii=False) if state["symptom_details"] else json.dumps({"symptoms": state["symptoms"]}, ensure_ascii=False),
            messages=self._format_messages(state["messages"])
        )
        
        # 诊断报告需要完整 JSON，不做流式输出，但生成诊断消息时可以流式
        response = await self._call_llm(self.SYSTEM_PROMPT, prompt, temperature=0.5)
        
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            diagnosis = json.loads(response.strip())
            
            state["possible_diseases"] = diagnosis.get("diseases", [])
            state["risk_level"] = diagnosis.get("risk_level", "low")
            state["recommendations"] = {
                "summary": diagnosis.get("summary", ""),
                "risk_warning": diagnosis.get("risk_warning", ""),
                **diagnosis.get("recommendations", {})
            }
        except (json.JSONDecodeError, KeyError) as e:
            print(f"诊断报告解析失败: {e}")
            # 使用默认诊断
            state["possible_diseases"] = [
                {"name": "需要进一步检查", "probability": "待定", "description": "建议前往医院进行详细检查"}
            ]
            state["risk_level"] = "medium"
            state["recommendations"] = {
                "summary": f"根据您描述的症状（{', '.join(state['symptoms'][:3])}），建议尽快就医。",
                "department": "全科/相关专科",
                "urgency": "建议尽快就诊",
                "lifestyle": ["注意休息", "保持良好作息", "如症状加重请立即就医"]
            }
        
        state["stage"] = "completed"
        state["progress"] = 100
        
        # 生成诊断消息
        diagnosis_msg = self._format_diagnosis_message(state)
        
        # 如果有流式回调，逐字符输出诊断消息
        if on_chunk:
            for char in diagnosis_msg:
                await on_chunk(char)
        
        state["messages"].append({
            "role": "assistant",
            "content": diagnosis_msg,
            "timestamp": datetime.now().isoformat(),
            "is_diagnosis": True
        })
        state["current_question"] = diagnosis_msg
        
        return state

    def _format_diagnosis_message(self, state: DiagnosisState) -> str:
        """格式化诊断消息"""
        recommendations = state.get("recommendations", {})
        diseases = state.get("possible_diseases", [])
        
        msg = f"【诊断报告】\n\n"
        msg += f"📋 症状总结：\n{recommendations.get('summary', '已收集您的症状信息')}\n\n"
        
        if diseases:
            msg += "🔍 可能的情况：\n"
            for d in diseases[:3]:
                msg += f"• {d.get('name', '未知')}：{d.get('description', '')}\n"
            msg += "\n"
        
        risk_level = state.get("risk_level", "low")
        if risk_level in ["high", "emergency"]:
            msg += f"⚠️ 风险提示：\n{recommendations.get('risk_warning', '请尽快就医')}\n\n"
        
        msg += f"🏥 就诊建议：\n"
        msg += f"• 建议科室：{recommendations.get('department', '相关专科')}\n"
        msg += f"• 紧急程度：{recommendations.get('urgency', '建议就诊')}\n\n"
        
        lifestyle = recommendations.get("lifestyle", [])
        if lifestyle:
            msg += "💡 生活建议：\n"
            for tip in lifestyle[:3]:
                msg += f"• {tip}\n"
        
        msg += "\n⚕️ 以上内容仅供参考，不能替代专业医生的诊断，如有不适请及时就医。"
        
        return msg

    def should_continue(self, state: DiagnosisState) -> str:
        """判断下一步流程 - 基于 AI 评估结果"""
        # 强制出结论（用户点击"直接出结论"按钮）
        if state.get("force_conclude", False):
            return "diagnose"
        
        # AI 判断应该进入诊断阶段
        if state.get("should_diagnose", False):
            return "diagnose"
        
        # 继续问诊
        return "continue"

    async def run(
        self,
        state: DiagnosisState,
        user_input: str = None,
        force_conclude: bool = False,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> DiagnosisState:
        """运行问诊流程（支持流式输出）"""
        state["force_conclude"] = force_conclude
        
        # 判断是否是真正的新会话（没有任何对话历史）
        has_assistant_history = any(msg.get("role") == "assistant" for msg in state.get("messages", []))
        
        # 只在完全新会话时才问候
        if state["stage"] == "greeting" and not has_assistant_history:
            state = await self.greet(state)
            # 问候语也可以流式输出
            if on_chunk:
                for char in state["current_question"]:
                    await on_chunk(char)
            return state
        
        # 如果 stage 还是 greeting 但已有对话历史，说明是数据库状态未更新，强制切换到 collecting
        if state["stage"] == "greeting":
            state["stage"] = "collecting"
        
        # 分析用户输入
        if user_input:
            state = await self.analyze_input(state, user_input)
        
        # 评估进度
        state = await self.assess_progress(state)
        
        # 判断下一步
        next_step = self.should_continue(state)
        
        if next_step == "diagnose":
            # 生成诊断
            state = await self.generate_diagnosis(state, on_chunk=on_chunk)
        else:
            # 继续问诊
            state = await self.generate_question(state, on_chunk=on_chunk)
            state = await self.generate_quick_options(state)
        
        return state


def create_initial_state(consultation_id: str, user_id: int, chief_complaint: str = "") -> DiagnosisState:
    """创建初始问诊状态"""
    return DiagnosisState(
        consultation_id=consultation_id,
        user_id=user_id,
        messages=[],
        chief_complaint=chief_complaint,
        symptoms=[],
        symptom_details={},
        stage="greeting",
        progress=0,
        questions_asked=0,
        current_question="",
        quick_options=[],
        reasoning="",
        possible_diseases=[],
        risk_level="low",
        recommendations={},
        can_conclude=False,
        force_conclude=False,
        # AI评估字段（新增）
        should_diagnose=False,
        confidence=0,
        missing_info=[]
    )
