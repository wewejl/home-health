"""
测试多模态图片分析
直接调用 qwen3-vl-plus 模型，验证模型是否能正确识别图片
"""
import os
import base64
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_direct_openai_call():
    """直接使用 OpenAI 客户端调用 qwen3-vl-plus"""
    print("=" * 50)
    print("测试1: 直接调用 OpenAI 客户端 (qwen3-vl-plus)")
    print("=" * 50)
    
    # 读取图片并转为 base64
    image_path = "/Users/zhuxinye/Desktop/project/home-health/image.png"
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # 初始化客户端
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # 调用多模态模型
    response = client.chat.completions.create(
        model="qwen3-vl-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "请描述这张图片的内容，这是什么图片？"
                    }
                ]
            }
        ],
        max_tokens=500
    )
    
    result = response.choices[0].message.content
    print(f"\n模型回复:\n{result}\n")
    
    # 检查是否正确识别
    if "风景" in result or "山" in result or "湖" in result or "自然" in result or "雪" in result:
        print("✅ 模型正确识别了风景图片!")
    elif "皮肤" in result or "红斑" in result:
        print("❌ 模型错误地识别为皮肤图片 - 模型有问题")
    else:
        print("⚠️ 模型回复未知内容，请检查")
    
    return result


def test_crewai_multimodal():
    """测试 CrewAI 多模态功能"""
    print("\n" + "=" * 50)
    print("测试2: CrewAI 多模态 Agent")
    print("=" * 50)
    
    from crewai import Agent, Task, Crew, Process, LLM
    from app.config import get_settings
    
    settings = get_settings()
    
    # 读取图片
    image_path = "/Users/zhuxinye/Desktop/project/home-health/image.png"
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # 保存到临时文件
    import tempfile
    temp_path = os.path.join(tempfile.gettempdir(), "test_image.png")
    with open(temp_path, "wb") as f:
        f.write(base64.b64decode(image_data))
    print(f"图片保存到: {temp_path}")
    
    # 创建多模态 LLM
    llm = LLM(
        model=f"openai/{settings.QWEN_VL_MODEL}",
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        temperature=0.6,
        max_tokens=500,
        timeout=120,
    )
    
    # 创建多模态 Agent
    agent = Agent(
        role="图片分析师",
        goal="准确描述图片内容",
        backstory="你是一个专业的图片分析师，能够准确识别和描述图片内容。",
        verbose=True,
        llm=llm,
        multimodal=True,  # 启用多模态
    )
    
    # 创建任务
    task = Task(
        description=f"""请分析这张图片并描述其内容。

📷 用户上传了一张图片
图片路径：{temp_path}

**重要**：请使用 AddImageTool 工具分析这张图片。
- 调用方式：使用 image_url 参数传入图片路径 "{temp_path}"
- 描述图片中的内容

请用 JSON 格式回复：
{{"description": "图片描述", "is_skin_image": true/false}}
""",
        expected_output="JSON格式的图片分析结果",
        agent=agent,
    )
    
    # 运行 Crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    
    result = crew.kickoff()
    print(f"\nCrewAI 结果:\n{result}\n")
    
    return result


def test_derma_service_multimodal():
    """测试 DermaCrewService 的多模态图片分析"""
    print("\n" + "=" * 50)
    print("测试3: DermaCrewService 多模态分析（修复后）")
    print("=" * 50)
    
    import asyncio
    from app.services.dermatology.derma_crew_service import DermaCrewService
    
    # 读取图片
    image_path = "/Users/zhuxinye/Desktop/project/home-health/image.png"
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    # 创建服务实例
    service = DermaCrewService()
    
    # 创建初始状态
    state = {
        "messages": [],
        "stage": "collecting",
        "chief_complaint": "",
        "skin_location": "",
        "duration": "",
        "symptoms": [],
        "questions_asked": 0
    }
    
    async def run_test():
        result = await service._analyze_with_multimodal(
            state=state,
            user_input="请分析这张照片",
            image_base64=image_data
        )
        return result
    
    result = asyncio.run(run_test())
    
    print(f"\n分析结果:")
    print(f"  - message: {result.get('message', '')[:200]}...")
    print(f"  - next_action: {result.get('next_action', '')}")
    print(f"  - stage: {result.get('stage', '')}")
    
    # 检查是否正确识别
    message = result.get("message", "").lower()
    if "风景" in message or "山" in message or "湖" in message or "瀑布" in message or "自然" in message or "不是皮肤" in message:
        print("\n✅ 模型正确识别了这不是皮肤图片!")
    elif "皮肤" in message and ("红斑" in message or "脱屑" in message):
        print("\n❌ 模型仍然错误地识别为皮肤问题")
    else:
        print(f"\n⚠️ 请检查模型回复")
    
    return result


if __name__ == "__main__":
    print("\n🧪 开始多模态测试...\n")
    
    # 测试1: 直接调用 OpenAI 客户端
    try:
        test_direct_openai_call()
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
    
    # 测试3: DermaCrewService 多模态分析（修复后）
    try:
        test_derma_service_multimodal()
    except Exception as e:
        print(f"❌ 测试3失败: {e}")
        import traceback
        traceback.print_exc()
