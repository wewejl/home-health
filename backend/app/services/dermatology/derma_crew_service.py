"""
DermaCrewService - CrewAI 1.x 皮肤科问诊服务
支持多模态图片分析和对话编排
"""
import asyncio
import json
from typing import Dict, Any, Optional, Callable, Awaitable, List
from datetime import datetime

from crewai import Crew, Process
from openai import OpenAI

from ...config import get_settings
from .derma_agents import (
    create_conversation_orchestrator,
    create_conversation_task,
    create_llm,
    create_multimodal_llm,
)

settings = get_settings()


class DermaCrewService:
    """
    皮肤科 CrewAI 1.x 编排服务
    
    负责：
    1. 初始化对话 Agent（支持多模态）
    2. 调用 Crew 执行问诊任务
    3. 管理状态与流式输出
    """
    
    def __init__(self):
        self.llm = self._build_llm()
        self.multimodal_llm = self._build_multimodal_llm()
        self._conversation_agent = None
        self._multimodal_agent = None  # 多模态 Agent（支持图片分析）
    
    def _build_llm(self):
        """构建普通 LLM 实例"""
        return create_llm(multimodal=False)
    
    def _build_multimodal_llm(self):
        """构建多模态 LLM 实例（支持图片分析）"""
        return create_multimodal_llm()
    
    @property
    def conversation_agent(self):
        """获取普通对话 Agent"""
        if self._conversation_agent is None:
            self._conversation_agent = create_conversation_orchestrator(self.llm, multimodal=False)
        return self._conversation_agent
    
    @property
    def multimodal_agent(self):
        """获取多模态 Agent（支持图片分析）"""
        if self._multimodal_agent is None:
            self._multimodal_agent = create_conversation_orchestrator(self.multimodal_llm, multimodal=True)
        return self._multimodal_agent
    
    def get_agent(self, has_image: bool = False):
        """根据是否有图片选择合适的 Agent"""
        if has_image:
            print("[DermaCrewService] 使用多模态 Agent（支持图片分析）")
            return self.multimodal_agent
        return self.conversation_agent
    
    def _get_openai_client(self) -> OpenAI:
        """获取 OpenAI 客户端（用于多模态图片分析）"""
        return OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
    
    async def run(
        self,
        state: Dict[str, Any],
        user_input: str = None,
        image_url: str = None,
        image_base64: str = None,
        task_type: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str, str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        运行文本问诊任务
        """
        # 新会话问候（仅在没有用户输入时触发）
        has_assistant_history = any(msg.get("role") == "assistant" for msg in state.get("messages", []))
        if state.get("stage") == "greeting" and not has_assistant_history and not user_input:
            return await self._handle_greeting(state, on_chunk)
        
        # 如果 stage 还是 greeting 但已有历史，切换到 collecting
        if state.get("stage") == "greeting":
            state["stage"] = "collecting"
        
        # 处理文本输入
        if user_input:
            return await self._handle_conversation(
                state, 
                user_input, 
                image_base64=image_base64,
                on_chunk=on_chunk, 
                on_step=on_step
            )
        
        return state
    
    async def _handle_greeting(
        self,
        state: Dict[str, Any],
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理问候"""
        greeting = """你好~我是你的皮肤科AI助手，将通过文字方式了解你的皮肤困扰，并给出温和、专业的建议。
请直接描述你目前的症状或担心的问题，我会一步步和你沟通。"""
        
        state["current_response"] = greeting
        state["stage"] = "collecting"
        state["messages"].append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat()
        })
        
        state["quick_options"] = [
            {"text": "描述位置", "value": "出现在身体哪个部位", "category": "症状"},
            {"text": "持续时间", "value": "大概持续了多久", "category": "症状"},
            {"text": "伴随感觉", "value": "是否有瘙痒或疼痛", "category": "症状"},
            {"text": "日常护理", "value": "我做过哪些护理措施", "category": "其他"}
        ]
        
        if on_chunk:
            for char in greeting:
                await on_chunk(char)
        
        return state
    
    async def _handle_conversation(
        self,
        state: Dict[str, Any],
        user_input: str,
        image_base64: str = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_step: Optional[Callable[[str, str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """处理对话"""
        # 打印当前状态以便调试
        print(f"[DermaCrewService] 处理对话前的状态:")
        print(f"  - chief_complaint: {state.get('chief_complaint', '')}")
        print(f"  - skin_location: {state.get('skin_location', '')}")
        print(f"  - duration: {state.get('duration', '')}")
        print(f"  - symptoms: {state.get('symptoms', [])}")
        print(f"  - questions_asked: {state.get('questions_asked', 0)}")
        print(f"  - 收到图片: {'是' if image_base64 else '否'}")
        
        # 记录用户消息
        state["messages"].append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # 如果有图片，直接使用 OpenAI 客户端进行多模态分析（绕过 CrewAI AddImageTool）
        if image_base64:
            print("[DermaCrewService] 检测到图片，使用 OpenAI 客户端直接调用多模态模型")
            result = await self._analyze_with_multimodal(state, user_input, image_base64, on_chunk)
        else:
            # 无图片时使用 CrewAI 处理对话
            result = await self._run_conversation_crew(state, user_input, image_base64, on_step)
        
        # 更新状态
        response = result.get("message", "")
        if not response:
            raise ValueError("CrewAI 未返回有效的 message 字段，请检查 Agent 配置或模型输出")
        
        # 流式输出
        if on_chunk:
            for char in response:
                await on_chunk(char)
        
        # 更新提取的信息 - 改进逻辑，允许更新而不仅仅是首次设置
        extracted = result.get("extracted_info", {})
        print(f"[DermaCrewService] Agent 提取的信息: {extracted}")
        
        # 主诉：如果有新的且更具体的，则更新
        if extracted.get("chief_complaint"):
            new_complaint = extracted["chief_complaint"]
            if new_complaint and new_complaint != "未明确" and new_complaint != "":
                state["chief_complaint"] = new_complaint
        
        # 部位：如果有新的且更具体的，则更新
        if extracted.get("skin_location"):
            new_location = extracted["skin_location"]
            if new_location and new_location != "未明确具体部位" and new_location != "":
                state["skin_location"] = new_location
        
        # 持续时间：如果有新的且更具体的，则更新
        if extracted.get("duration"):
            new_duration = extracted["duration"]
            if new_duration and new_duration != "未明确持续时间" and new_duration != "":
                state["duration"] = new_duration
        
        # 症状：累积添加新症状
        if extracted.get("symptoms"):
            for symptom in extracted["symptoms"]:
                if symptom and symptom not in state.get("symptoms", []):
                    state.setdefault("symptoms", []).append(symptom)
        
        state["current_response"] = response
        state["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        state["quick_options"] = result.get("quick_options", self._default_quick_options(state))
        state["questions_asked"] = state.get("questions_asked", 0) + 1
        state["stage"] = result.get("stage", state.get("stage", "collecting"))
        
        print(f"[DermaCrewService] 处理对话后的状态:")
        print(f"  - chief_complaint: {state.get('chief_complaint', '')}")
        print(f"  - skin_location: {state.get('skin_location', '')}")
        print(f"  - duration: {state.get('duration', '')}")
        print(f"  - symptoms: {state.get('symptoms', [])}")
        print(f"  - questions_asked: {state.get('questions_asked', 0)}")
        print(f"  - stage: {state.get('stage', '')}")
        
        # 对话结束时自动聚合到病历事件
        if state.get("stage") == "completed":
            print(f"[DermaCrewService] 对话完成，准备自动聚合到病历事件...")
            state["should_show_dossier_prompt"] = True
            # event_id 和 is_new_event 将在路由层调用聚合接口后设置
        
        return state
    
    async def _analyze_with_multimodal(
        self,
        state: Dict[str, Any],
        user_input: str,
        image_base64: str,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """
        直接使用 OpenAI 客户端调用多模态模型分析图片
        绕过 CrewAI 的 AddImageTool，确保图片能被正确传递给模型
        """
        client = self._get_openai_client()
        
        # 构建历史消息（最近5条）
        messages = [
            {
                "role": "system",
                "content": """你是一位经验丰富的皮肤科专家医生，擅长通过皮肤影像学分析诊断各类皮肤疾病。

【皮肤影像分析规则】
1. **图片内容识别**
   - 首先判断图片是否为皮肤照片
   - 如果不是皮肤照片（如风景、物品、动物等），明确告知："这张图片不是皮肤照片，无法进行皮肤病分析。请上传清晰的皮肤患处照片。"
   - 只有确认是皮肤照片时，才进行专业分析

2. **专业的皮肤影像学分析**
   当图片为皮肤照片时，按照以下维度进行分析：
   - **皮损形态**：红斑、丘疹、水疱、脓疱、结节、斑块、鳞屑、糜烂、溃疡等
   - **颜色特征**：红色、粉红色、褐色、黑色、白色、紫色等
   - **分布特征**：局限性、泛发性、对称性、单侧性、线状、环状、带状等
   - **边界特征**：清楚、模糊、规则、不规则
   - **大小和数量**：单发、多发、融合、散在分布
   - **表面特征**：光滑、粗糙、有鳞屑、有渗液、有结痂等

3. **鉴别诊断思维**
   - 基于影像学特征，列出2-3个可能的诊断
   - 说明诊断依据："从图片可以看到[具体特征]，结合[症状描述]，初步考虑..."
   - 如果需要更多信息，明确指出需要了解的内容

4. **专业语言表达**
   - 使用规范的医学术语描述皮损特征
   - 同时用通俗语言解释，确保患者理解
   - 例如："图片显示皮损呈现红斑和丘疹（即红色的小凸起），分布在手背，边界较清楚。"

5. **安全性评估**
   - 如果发现危急征象（如大面积皮损、感染征象、恶性肿瘤特征），立即建议就医
   - 表达方式："从图片来看，这种情况需要尽快到医院皮肤科就诊，建议今天就去。"

【输出格式】
必须返回 JSON 格式：
{
    "message": "专业的皮肤影像分析和医学评估",
    "next_action": "continue（需要更多信息）或 complete（可以给出诊断建议）",
    "stage": "collecting（还在收集信息）或 summary（给出诊断）",
    "quick_options": [{"text": "选项", "value": "值", "category": "类别"}],
    "extracted_info": {"chief_complaint": "从图片提取的主诉", "skin_location": "皮损部位", "duration": "", "symptoms": ["从图片观察到的症状"]}
}"""
            }
        ]
        
        # 添加历史对话（最近5条）
        recent_messages = state.get("messages", [])[-5:]
        for msg in recent_messages:
            if msg.get("role") == "user":
                messages.append({"role": "user", "content": msg.get("content", "")})
            elif msg.get("role") == "assistant":
                messages.append({"role": "assistant", "content": msg.get("content", "")})
        
        # 构建当前消息（包含图片）
        # 处理 base64 格式
        if not image_base64.startswith("data:"):
            image_base64 = f"data:image/jpeg;base64,{image_base64}"
        
        current_message = {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_base64}
                },
                {
                    "type": "text",
                    "text": f"{user_input}\n\n请作为皮肤科专家，对这张图片进行详细的皮肤影像学分析：\n1. 首先判断是否为皮肤照片\n2. 如果是，请描述皮损的形态、颜色、分布、边界等特征\n3. 结合患者的文字描述，给出鉴别诊断\n4. 如果需要更多信息，请明确指出"
                }
            ]
        }
        messages.append(current_message)
        
        print(f"[DermaCrewService] 调用多模态模型: {settings.QWEN_VL_MODEL}")
        
        # 调用多模态模型
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=settings.QWEN_VL_MODEL,
                messages=messages,
                max_tokens=2000,
                temperature=0.6
            )
        )
        
        response_text = response.choices[0].message.content
        print(f"[DermaCrewService] 多模态模型原始回复: {response_text[:200]}...")
        
        # 解析 JSON 回复
        try:
            # 尝试提取 JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            elif "{" in response_text and "}" in response_text:
                # 查找第一个 { 和最后一个 }
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                json_str = response_text
            
            result = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            print(f"[DermaCrewService] JSON 解析失败，使用原始回复: {e}")
            # 如果解析失败，构造默认结构
            result = {
                "message": response_text,
                "next_action": "continue",
                "stage": "collecting",
                "quick_options": [
                    {"text": "继续描述", "value": "继续描述症状", "category": "其他"},
                    {"text": "上传皮肤照片", "value": "我想上传皮肤照片", "category": "其他"}
                ],
                "extracted_info": {}
            }
        
        print(f"[DermaCrewService] 多模态分析结果: {result.get('message', '')[:100]}...")
        return result
    
    async def _run_conversation_crew(
        self,
        state: Dict[str, Any],
        user_input: str,
        image_base64: str = None,
        on_step: Optional[Callable[[str, str], Awaitable[None]]] = None
    ) -> Dict[str, Any]:
        """运行对话 Crew - CrewAI 1.x 原生异步支持"""
        # 根据是否有图片选择合适的 Agent
        has_image = bool(image_base64)
        agent = self.get_agent(has_image=has_image)
        
        task = create_conversation_task(
            agent,
            state,
            user_input,
            image_base64
        )
        
        # 定义步骤回调函数
        step_callback_func = None
        if on_step:
            def step_callback(step_output):
                """CrewAI 步骤回调 - 捕获思考过程"""
                try:
                    # 判断步骤类型
                    if hasattr(step_output, 'description'):
                        step_type = 'thinking'
                        content = str(step_output.description)
                    elif hasattr(step_output, 'tool'):
                        step_type = 'tool'
                        content = f"使用工具: {step_output.tool}"
                    elif hasattr(step_output, 'thought'):
                        step_type = 'reasoning'
                        content = str(step_output.thought)
                    else:
                        step_type = 'step'
                        content = str(step_output)
                    
                    # 异步调用 on_step
                    asyncio.create_task(on_step(step_type, content))
                except Exception as e:
                    print(f"[DermaCrewService] step_callback error: {e}")
            
            step_callback_func = step_callback
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,  # 生产环境关闭详细日志
            step_callback=step_callback_func
        )
        
        # CrewAI 1.x 支持原生 async
        try:
            result = await crew.kickoff_async()
        except AttributeError:
            # 如果 kickoff_async 不可用，回退到线程池执行
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
        
        # 使用 CrewAI 官方结构化输出，直接返回字典
        # result 是 CrewOutput 对象，支持 .to_dict() 或 .pydantic 访问
        return result.to_dict()
    
    
    def _default_quick_options(self, state: Dict[str, Any]) -> List[Dict[str, str]]:
        """默认快捷选项"""
        return [
            {"text": "是的", "value": "是的", "category": "确认"},
            {"text": "没有", "value": "没有", "category": "否定"},
            {"text": "不确定", "value": "不确定", "category": "不确定"},
            {"text": "换个问法", "value": "能换一个角度问吗", "category": "其他"}
        ]


# 全局实例
derma_crew_service = DermaCrewService()
