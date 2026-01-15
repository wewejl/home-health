"""测试 API 响应格式"""
import asyncio
import json
from app.services.dermatology import DermaAgentWrapper
from app.routes.derma import build_response


def test_api_response_format():
    """测试 API 响应格式是否包含 quick_options"""
    agent = DermaAgentWrapper()
    
    # 创建初始状态
    state = asyncio.get_event_loop().run_until_complete(
        agent.create_initial_state("test-api-format", 1)
    )
    
    # 发送消息
    state = asyncio.get_event_loop().run_until_complete(
        agent.run(state=state, user_input="我皮肤过敏了")
    )
    
    # 构建 API 响应
    response = build_response(state)
    response_dict = response.model_dump()
    
    print("\n" + "=" * 60)
    print("API 响应格式检查")
    print("=" * 60)
    print(json.dumps(response_dict, ensure_ascii=False, indent=2))
    
    # 验证关键字段
    assert "quick_options" in response_dict, "响应中应该有 quick_options 字段"
    assert response_dict["quick_options"] is not None, "quick_options 不应该为 None"
    assert isinstance(response_dict["quick_options"], list), "quick_options 应该是列表"
    
    if len(response_dict["quick_options"]) > 0:
        print(f"\n✅ 快捷选项字段存在且有 {len(response_dict['quick_options'])} 个选项")
        print("\n快捷选项详情:")
        for i, opt in enumerate(response_dict["quick_options"], 1):
            print(f"  {i}. text: {opt['text']}, value: {opt['value']}, category: {opt['category']}")
    else:
        print("\n⚠️  警告: quick_options 字段存在但为空列表")
    
    # 检查 Schema 结构
    print("\n" + "=" * 60)
    print("Schema 验证")
    print("=" * 60)
    print(f"类型: {response.__class__.__name__}")
    print(f"字段: {list(response_dict.keys())}")


if __name__ == "__main__":
    test_api_response_format()
