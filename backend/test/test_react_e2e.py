"""ReAct Agent 端到端测试"""
import asyncio
import pytest
from app.services.dermatology import DermaAgentWrapper, DermaReActWrapper


class TestReActE2E:
    """端到端测试"""
    
    def test_simple_conversation(self):
        """测试简单对话"""
        agent = DermaReActWrapper()
        
        # 创建初始状态
        state = asyncio.get_event_loop().run_until_complete(
            agent.create_initial_state("e2e-test", 1)
        )
        
        # 发送第一条消息
        state = asyncio.get_event_loop().run_until_complete(
            agent.run(
                state=state,
                user_input="我脸上长痘痘了"
            )
        )
        
        # 验证有回复
        assert state["current_response"]
        assert len(state["current_response"]) > 10
        
        # 验证有快捷选项
        assert isinstance(state["quick_options"], list)
    
    def test_multi_turn_conversation(self):
        """测试多轮对话"""
        agent = DermaReActWrapper()
        
        state = asyncio.get_event_loop().run_until_complete(
            agent.create_initial_state("e2e-test-2", 1)
        )
        
        # 第一轮
        state = asyncio.get_event_loop().run_until_complete(
            agent.run(state=state, user_input="皮肤很痒")
        )
        assert state["current_response"]
        
        # 第二轮
        state = asyncio.get_event_loop().run_until_complete(
            agent.run(state=state, user_input="手臂上")
        )
        assert state["current_response"]
        
        # 验证消息历史
        assert len(state["messages"]) >= 4  # user + ai + user + ai
    
    def test_module_import(self):
        """测试模块导入正确"""
        # 验证默认导出是 ReAct 实现
        assert DermaAgentWrapper is DermaReActWrapper
        
        # 验证可以创建实例
        agent = DermaAgentWrapper()
        assert agent is not None
        
        # 验证能力配置
        caps = agent.get_capabilities()
        assert "conversation" in caps["actions"]
