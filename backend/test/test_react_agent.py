"""ReAct Agent 单元测试"""
import pytest
from app.services.dermatology.react_state import (
    DermaReActState,
    create_react_initial_state
)
from app.services.dermatology.react_tools import get_derma_tools
from app.services.dermatology.react_agent import (
    get_derma_react_graph,
    reset_derma_react_graph
)
from app.services.dermatology.quick_options import generate_quick_options
from app.services.dermatology.react_wrapper import DermaReActWrapper


class TestReActState:
    """状态定义测试"""
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        state = create_react_initial_state("test-session", 123)
        
        assert state["session_id"] == "test-session"
        assert state["user_id"] == 123
        assert state["messages"] == []
        assert state["chief_complaint"] == ""
        assert state["symptoms"] == []
        assert state["risk_level"] == "low"


class TestReActTools:
    """工具定义测试"""
    
    def test_tools_are_callable(self):
        """测试工具可调用"""
        tools = get_derma_tools()
        assert len(tools) == 2
        assert tools[0].name == "analyze_skin_image"
        assert tools[1].name == "generate_diagnosis"
    
    def test_tool_schemas(self):
        """测试工具 schema 正确"""
        tools = get_derma_tools()
        
        # 图片分析工具
        img_tool = tools[0]
        assert "image_base64" in str(img_tool.args_schema.schema())
        
        # 诊断工具
        diag_tool = tools[1]
        assert "symptoms" in str(diag_tool.args_schema.schema())


class TestReActAgent:
    """Agent 核心测试"""
    
    def test_graph_builds(self):
        """测试图可以构建"""
        reset_derma_react_graph()
        graph = get_derma_react_graph()
        
        assert graph is not None
    
    def test_graph_singleton(self):
        """测试图是单例"""
        graph1 = get_derma_react_graph()
        graph2 = get_derma_react_graph()
        
        assert graph1 is graph2


class TestQuickOptions:
    """快捷选项测试"""
    
    def test_empty_response(self):
        """测试空回复返回空列表"""
        result = generate_quick_options("")
        assert result == []
    
    def test_short_response(self):
        """测试过短回复返回空列表"""
        result = generate_quick_options("你好")
        assert result == []


class TestReActWrapper:
    """适配器测试"""
    
    def test_create_initial_state(self):
        """测试创建初始状态"""
        import asyncio
        wrapper = DermaReActWrapper()
        state = asyncio.get_event_loop().run_until_complete(
            wrapper.create_initial_state("test-session", 123)
        )
        
        assert state["session_id"] == "test-session"
        assert state["user_id"] == 123
        assert isinstance(state["messages"], list)
    
    def test_get_capabilities(self):
        """测试获取能力"""
        wrapper = DermaReActWrapper()
        caps = wrapper.get_capabilities()
        
        assert "conversation" in caps["actions"]
        assert "image/jpeg" in caps["accepts_media"]
