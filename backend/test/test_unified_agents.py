#!/usr/bin/env python3
"""
统一智能体架构测试脚本
测试 /sessions/* 接口的智能体功能
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8100"

def get_token():
    """获取测试用户的 token"""
    # 尝试使用测试账号登录获取 token
    # 如果需要，可以手动替换为有效的 token
    return None

def test_list_agents():
    """测试获取智能体列表"""
    print("\n=== 测试: 获取智能体列表 ===")
    try:
        resp = requests.get(f"{BASE_URL}/sessions/agents")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"可用智能体: {list(data.keys())}")
            for agent_type, caps in data.items():
                print(f"\n  [{agent_type}]")
                print(f"    描述: {caps.get('description', 'N/A')}")
                print(f"    动作: {caps.get('actions', [])}")
                print(f"    支持媒体: {caps.get('accepts_media', [])}")
            return True
        else:
            print(f"错误: {resp.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_agent_capabilities(agent_type: str):
    """测试获取单个智能体能力"""
    print(f"\n=== 测试: 获取 {agent_type} 智能体能力 ===")
    try:
        resp = requests.get(f"{BASE_URL}/sessions/agents/{agent_type}/capabilities")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"能力配置: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {resp.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_create_session_with_agent(token: str, agent_type: str = "dermatology"):
    """测试创建指定智能体类型的会话"""
    print(f"\n=== 测试: 创建 {agent_type} 会话 ===")
    if not token:
        print("跳过: 需要登录 token")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {"agent_type": agent_type}
        resp = requests.post(f"{BASE_URL}/sessions", headers=headers, json=body)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"会话ID: {data.get('session_id')}")
            print(f"智能体类型: {data.get('agent_type')}")
            return data.get('session_id')
        else:
            print(f"错误: {resp.text}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_send_message(token: str, session_id: str, content: str, action: str = "conversation"):
    """测试发送消息"""
    print(f"\n=== 测试: 发送消息 (action={action}) ===")
    if not token or not session_id:
        print("跳过: 需要 token 和 session_id")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {"content": content, "action": action}
        resp = requests.post(f"{BASE_URL}/sessions/{session_id}/messages", headers=headers, json=body)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            ai_msg = data.get('ai_message', {})
            print(f"AI回复: {ai_msg.get('content', '')[:200]}...")
            if ai_msg.get('structured_data'):
                print(f"结构化数据: {ai_msg.get('structured_data')}")
            return True
        else:
            print(f"错误: {resp.text}")
            return False
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    print("=" * 60)
    print("统一智能体架构测试")
    print("=" * 60)
    
    # 测试智能体列表接口（不需要认证）
    test_list_agents()
    
    # 测试智能体能力接口
    test_agent_capabilities("general")
    test_agent_capabilities("dermatology")
    
    # 需要登录才能测试的接口
    token = get_token()
    if token:
        # 创建皮肤科会话
        session_id = test_create_session_with_agent(token, "dermatology")
        if session_id:
            # 发送普通对话
            test_send_message(token, session_id, "我的皮肤最近有点红")
    else:
        print("\n[提示] 如需测试会话接口，请手动设置 token")
        print("可以通过以下方式获取 token:")
        print("  1. 在 iOS 模拟器中登录后查看控制台日志")
        print("  2. 使用 curl 调用 /auth/login 接口")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
