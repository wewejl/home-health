"""快捷选项生成调试测试"""
import asyncio
from app.services.dermatology.quick_options import generate_quick_options
from app.services.dermatology import DermaAgentWrapper


def test_quick_options_generation():
    """测试快捷选项生成"""
    test_response = "请问您的皮肤问题出现在哪个部位？是面部、手臂还是其他地方？"
    
    print(f"测试回复: {test_response}")
    options = generate_quick_options(test_response)
    print(f"生成的快捷选项: {options}")
    
    assert len(options) > 0, "应该生成快捷选项"
    print("✅ 快捷选项生成成功")


def test_e2e_with_quick_options():
    """端到端测试快捷选项"""
    agent = DermaAgentWrapper()
    
    # 创建初始状态
    state = asyncio.get_event_loop().run_until_complete(
        agent.create_initial_state("test-quick-opt", 1)
    )
    
    # 发送消息
    state = asyncio.get_event_loop().run_until_complete(
        agent.run(state=state, user_input="我脸上长痘痘了")
    )
    
    print(f"\n=== 端到端测试结果 ===")
    print(f"AI 回复: {state['current_response']}")
    print(f"快捷选项数量: {len(state.get('quick_options', []))}")
    print(f"快捷选项内容: {state.get('quick_options', [])}")
    
    assert state['current_response'], "应该有 AI 回复"
    assert 'quick_options' in state, "状态中应该有 quick_options 字段"
    
    if len(state.get('quick_options', [])) == 0:
        print("⚠️  警告: 快捷选项为空")
    else:
        print("✅ 快捷选项生成成功")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 1: 快捷选项生成函数")
    print("=" * 60)
    try:
        test_quick_options_generation()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试 2: 端到端快捷选项")
    print("=" * 60)
    try:
        test_e2e_with_quick_options()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
