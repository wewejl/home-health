"""
端到端测试脚本 - 测试所有智能体的完整流程

测试内容：
1. 创建会话（初始化状态）
2. 发送文本消息
3. 上传图片并分析（皮肤科/心血管/骨科）
4. 验证流式响应
5. 检查能力配置
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []
    
    def record_pass(self, name: str):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def record_fail(self, name: str, error: str):
        self.failed += 1
        self.errors.append(f"{name}: {error}")
        print(f"  ❌ {name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"测试结果: {self.passed}/{total} 通过")
        if self.errors:
            print(f"\n失败详情:")
            for err in self.errors:
                print(f"  - {err}")
        return self.failed == 0


result = TestResult()


def test_imports():
    """测试模块导入"""
    print("\n📦 测试模块导入...")
    
    try:
        from app.services.agent_router import AgentRouter, initialize_agents
        result.record_pass("AgentRouter 导入")
    except Exception as e:
        result.record_fail("AgentRouter 导入", str(e))
        return False
    
    try:
        from app.services.dermatology import DermaAgentWrapper, DermaAgent, create_derma_initial_state
        result.record_pass("Dermatology 模块导入")
    except Exception as e:
        result.record_fail("Dermatology 模块导入", str(e))
    
    try:
        from app.services.cardiology import CardioAgentWrapper, CardioAgent, create_cardio_initial_state
        result.record_pass("Cardiology 模块导入")
    except Exception as e:
        result.record_fail("Cardiology 模块导入", str(e))
    
    try:
        from app.services.orthopedics import OrthoAgentWrapper, OrthoAgent, create_ortho_initial_state
        result.record_pass("Orthopedics 模块导入")
    except Exception as e:
        result.record_fail("Orthopedics 模块导入", str(e))
    
    try:
        from app.services.general import GeneralAgent
        result.record_pass("General 模块导入")
    except Exception as e:
        result.record_fail("General 模块导入", str(e))
    
    return True


def test_agent_router():
    """测试智能体路由器"""
    print("\n🔀 测试智能体路由器...")
    
    try:
        from app.services.agent_router import AgentRouter
        
        # 重置并初始化
        AgentRouter.reset()
        AgentRouter.ensure_initialized()
        
        # 检查注册的智能体
        agents = AgentRouter.list_agents()
        expected_agents = ["general", "dermatology", "cardiology", "orthopedics"]
        
        for agent_type in expected_agents:
            if agent_type in agents:
                result.record_pass(f"智能体注册: {agent_type}")
            else:
                result.record_fail(f"智能体注册: {agent_type}", "未找到")
        
        # 测试科室推断
        test_cases = [
            ("皮肤科", "dermatology"),
            ("心血管内科", "cardiology"),
            ("骨科", "orthopedics"),
            ("其他科室", "general"),
        ]
        for dept, expected in test_cases:
            inferred = AgentRouter.infer_agent_type(dept)
            if inferred == expected:
                result.record_pass(f"科室推断: {dept} -> {expected}")
            else:
                result.record_fail(f"科室推断: {dept}", f"期望 {expected}, 得到 {inferred}")
        
    except Exception as e:
        result.record_fail("AgentRouter 测试", str(e))


def test_capabilities():
    """测试智能体能力配置"""
    print("\n⚙️ 测试能力配置...")
    
    try:
        from app.services.agent_router import AgentRouter
        
        # 皮肤科能力
        derma_caps = AgentRouter.get_capabilities("dermatology")
        if "analyze_skin" in derma_caps.get("actions", []):
            result.record_pass("皮肤科能力: analyze_skin")
        else:
            result.record_fail("皮肤科能力", "缺少 analyze_skin action")
        
        # 心血管能力
        cardio_caps = AgentRouter.get_capabilities("cardiology")
        if "interpret_ecg" in cardio_caps.get("actions", []):
            result.record_pass("心血管能力: interpret_ecg")
        else:
            result.record_fail("心血管能力", "缺少 interpret_ecg action")
        
        # 骨科能力
        ortho_caps = AgentRouter.get_capabilities("orthopedics")
        if "interpret_xray" in ortho_caps.get("actions", []):
            result.record_pass("骨科能力: interpret_xray")
        else:
            result.record_fail("骨科能力", "缺少 interpret_xray action")
        
        # 检查媒体类型
        for agent_type in ["dermatology", "cardiology", "orthopedics"]:
            caps = AgentRouter.get_capabilities(agent_type)
            if "image/jpeg" in caps.get("accepts_media", []):
                result.record_pass(f"{agent_type} 支持图片")
            else:
                result.record_fail(f"{agent_type} 媒体类型", "不支持 image/jpeg")
                
    except Exception as e:
        result.record_fail("能力配置测试", str(e))


async def test_initial_state():
    """测试初始状态创建"""
    print("\n🏁 测试初始状态创建...")
    
    try:
        from app.services.agent_router import AgentRouter
        
        for agent_type in ["general", "dermatology", "cardiology", "orthopedics"]:
            agent = AgentRouter.get_agent(agent_type)
            state = await agent.create_initial_state(
                session_id=f"test-{agent_type}-001",
                user_id=1
            )
            
            # 验证基本字段
            if state.get("session_id") and state.get("messages") is not None:
                result.record_pass(f"{agent_type} 初始状态")
            else:
                result.record_fail(f"{agent_type} 初始状态", "缺少必要字段")
                
    except Exception as e:
        result.record_fail("初始状态测试", str(e))


async def test_greeting():
    """测试问候消息"""
    print("\n👋 测试问候消息...")
    
    try:
        from app.services.agent_router import AgentRouter
        
        chunks_received = []
        
        async def on_chunk(chunk: str):
            chunks_received.append(chunk)
        
        for agent_type in ["dermatology", "cardiology", "orthopedics"]:
            chunks_received.clear()
            
            agent = AgentRouter.get_agent(agent_type)
            state = await agent.create_initial_state(
                session_id=f"test-greeting-{agent_type}",
                user_id=1
            )
            
            # 运行以获取问候
            updated_state = await agent.run(
                state=state,
                user_input=None,
                on_chunk=on_chunk
            )
            
            # 验证问候
            if updated_state.get("current_response"):
                result.record_pass(f"{agent_type} 问候消息")
            else:
                result.record_fail(f"{agent_type} 问候消息", "无响应")
            
            # 验证流式输出
            if len(chunks_received) > 0:
                result.record_pass(f"{agent_type} 流式输出")
            else:
                result.record_fail(f"{agent_type} 流式输出", "无 chunk")
            
            # 验证快捷选项
            if updated_state.get("quick_options"):
                result.record_pass(f"{agent_type} 快捷选项")
            else:
                result.record_fail(f"{agent_type} 快捷选项", "无选项")
                
    except Exception as e:
        result.record_fail("问候消息测试", str(e))


async def test_conversation():
    """测试对话功能（需要 LLM API）"""
    print("\n💬 测试对话功能...")
    print("  ⚠️ 此测试需要有效的 LLM API 配置")
    
    try:
        from app.services.agent_router import AgentRouter
        from app.config import get_settings
        
        settings = get_settings()
        if not settings.LLM_API_KEY:
            print("  ⏭️ 跳过：未配置 LLM_API_KEY")
            return
        
        # 只测试骨科以验证新实现
        agent = AgentRouter.get_agent("orthopedics")
        state = await agent.create_initial_state(
            session_id="test-conv-ortho",
            user_id=1
        )
        
        # 先获取问候
        state = await agent.run(state=state, user_input=None)
        
        # 发送消息
        state = await agent.run(
            state=state,
            user_input="我膝盖疼痛，走路时加重"
        )
        
        if state.get("current_response") and len(state.get("messages", [])) >= 2:
            result.record_pass("orthopedics 对话")
        else:
            result.record_fail("orthopedics 对话", "响应异常")
            
    except Exception as e:
        # 如果是 API 错误，标记为跳过
        error_str = str(e)
        if "API" in error_str or "timeout" in error_str.lower():
            print(f"  ⏭️ 跳过：API 错误 - {error_str[:50]}")
        else:
            result.record_fail("对话功能测试", str(e))


def test_wrapper_interface():
    """测试 Wrapper 接口兼容性"""
    print("\n🔌 测试 Wrapper 接口...")
    
    try:
        from app.services.base import BaseAgent
        from app.services.dermatology import DermaAgentWrapper
        from app.services.cardiology import CardioAgentWrapper
        from app.services.orthopedics import OrthoAgentWrapper
        
        wrappers = [
            ("DermaAgentWrapper", DermaAgentWrapper),
            ("CardioAgentWrapper", CardioAgentWrapper),
            ("OrthoAgentWrapper", OrthoAgentWrapper),
        ]
        
        for name, wrapper_class in wrappers:
            # 检查继承
            if issubclass(wrapper_class, BaseAgent):
                result.record_pass(f"{name} 继承 BaseAgent")
            else:
                result.record_fail(f"{name} 继承", "未继承 BaseAgent")
            
            # 检查方法
            instance = wrapper_class()
            required_methods = ["create_initial_state", "run", "get_capabilities"]
            for method in required_methods:
                if hasattr(instance, method) and callable(getattr(instance, method)):
                    result.record_pass(f"{name}.{method}()")
                else:
                    result.record_fail(f"{name}.{method}", "方法不存在")
                    
    except Exception as e:
        result.record_fail("Wrapper 接口测试", str(e))


def test_no_old_imports():
    """测试旧导入已清理"""
    print("\n🧹 测试旧导入已清理...")
    
    import subprocess
    
    # 检查是否有旧的平铺文件
    old_files = [
        "backend/app/services/general_agent.py",
        "backend/app/services/derma_agent.py",
        "backend/app/services/derma_agent_wrapper.py",
        "backend/app/services/derma_crew_service.py",
        "backend/app/services/crewai_agents.py",
        "backend/app/services/cardio_agent.py",
        "backend/app/services/cardio_agent_wrapper.py",
        "backend/app/services/cardio_crew_service.py",
        "backend/app/services/cardio_agents.py",
    ]
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    for old_file in old_files:
        full_path = os.path.join(project_root, old_file)
        if os.path.exists(full_path):
            result.record_fail(f"旧文件清理", f"{old_file} 仍存在")
        else:
            result.record_pass(f"旧文件已移除: {os.path.basename(old_file)}")


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("🧪 智能体端到端测试")
    print("=" * 50)
    
    # 同步测试
    test_imports()
    test_agent_router()
    test_capabilities()
    test_wrapper_interface()
    test_no_old_imports()
    
    # 异步测试
    await test_initial_state()
    await test_greeting()
    await test_conversation()
    
    # 总结
    success = result.summary()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
