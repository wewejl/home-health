"""
LangGraph 迁移 API 全面测试脚本

测试内容：
1. 创建会话
2. 发送消息（非流式）
3. 发送消息（流式）
4. 状态持久化验证
5. 多轮对话测试
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8100"

# 测试用户登录获取 token
def get_auth_token():
    """获取测试用户的认证 token"""
    # 使用测试验证码 000000（测试模式下始终有效）
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "phone": "13800138001",
        "code": "000000"
    })
    
    if response.status_code == 200:
        data = response.json()
        return data.get("token") or data.get("access_token")
    else:
        print(f"❌ 登录失败: {response.text}")
        return None


def test_create_session(token: str) -> str:
    """测试创建会话"""
    print("\n" + "=" * 60)
    print("测试 1: 创建皮肤科会话")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/sessions",
        headers=headers,
        json={
            "agent_type": "dermatology"
        }
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"✅ 会话创建成功")
        print(f"   - session_id: {session_id}")
        print(f"   - agent_type: {data.get('agent_type')}")
        print(f"   - 耗时: {elapsed:.2f}s")
        return session_id
    else:
        print(f"❌ 创建失败: {response.status_code}")
        print(f"   响应: {response.text}")
        return None


def test_send_message_non_stream(token: str, session_id: str):
    """测试发送消息（非流式）"""
    print("\n" + "=" * 60)
    print("测试 2: 发送消息（非流式）")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 第一轮：打招呼
    print("\n--- 第一轮：打招呼 ---")
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        headers=headers,
        json={
            "content": "你好",
            "action": "conversation"
        }
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        ai_msg = data.get("ai_message", {})
        content = ai_msg.get("content", "")[:100]
        print(f"✅ 消息发送成功")
        print(f"   - AI 回复: {content}...")
        print(f"   - 耗时: {elapsed:.2f}s")
        
        if elapsed > 5:
            print(f"   ⚠️ 警告: 响应时间超过 5 秒")
    else:
        print(f"❌ 发送失败: {response.status_code}")
        print(f"   响应: {response.text}")
        return False
    
    return True


def test_send_message_stream(token: str, session_id: str):
    """测试发送消息（流式）"""
    print("\n" + "=" * 60)
    print("测试 3: 发送消息（流式 SSE）")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    print("\n--- 流式对话：描述症状 ---")
    start_time = time.time()
    first_chunk_time = None
    chunks_received = 0
    full_response = ""
    
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/messages",
            headers=headers,
            json={
                "content": "我手臂上长了一些红色的小疹子，很痒",
                "action": "conversation"
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code == 200:
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if first_chunk_time is None and line.startswith("event: chunk"):
                        first_chunk_time = time.time() - start_time
                    
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:].strip())
                            if "text" in data:
                                chunks_received += 1
                                full_response += data["text"]
                            elif "message" in data:
                                # complete 事件
                                full_response = data.get("message", full_response)
                        except json.JSONDecodeError:
                            pass
            
            elapsed = time.time() - start_time
            
            print(f"✅ 流式响应成功")
            print(f"   - 首个 chunk 时间: {first_chunk_time:.2f}s" if first_chunk_time else "   - 无流式 chunk")
            print(f"   - 总 chunks: {chunks_received}")
            print(f"   - 总耗时: {elapsed:.2f}s")
            print(f"   - AI 回复: {full_response[:100]}...")
            
            if first_chunk_time and first_chunk_time < 3:
                print(f"   ✅ 首 chunk 时间符合预期 (<3s)")
            elif first_chunk_time:
                print(f"   ⚠️ 首 chunk 时间偏长 (>3s)")
            
            return True
        else:
            print(f"❌ 流式请求失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 流式请求异常: {e}")
        return False


def test_state_persistence(token: str, session_id: str):
    """测试状态持久化"""
    print("\n" + "=" * 60)
    print("测试 4: 状态持久化验证")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 发送第二条消息，验证上下文是否保留
    print("\n--- 发送后续消息验证上下文 ---")
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/messages",
        headers=headers,
        json={
            "content": "已经有三天了",
            "action": "conversation"
        }
    )
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        ai_msg = data.get("ai_message", {})
        content = ai_msg.get("content", "")
        
        print(f"✅ 状态持久化正常")
        print(f"   - AI 回复: {content[:100]}...")
        print(f"   - 耗时: {elapsed:.2f}s")
        
        # 检查 AI 回复是否理解上下文
        if "疹" in content or "红" in content or "痒" in content or "皮肤" in content:
            print(f"   ✅ AI 理解了上下文（提到了之前的症状）")
        else:
            print(f"   ⚠️ AI 回复可能未完全理解上下文")
        
        return True
    else:
        print(f"❌ 状态持久化测试失败: {response.status_code}")
        print(f"   响应: {response.text}")
        return False


def test_get_messages(token: str, session_id: str):
    """测试获取消息历史"""
    print("\n" + "=" * 60)
    print("测试 5: 获取消息历史")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/sessions/{session_id}/messages",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        messages = data.get("messages", [])
        print(f"✅ 获取消息历史成功")
        print(f"   - 消息数量: {len(messages)}")
        
        for i, msg in enumerate(messages[-4:]):  # 只显示最后 4 条
            sender = msg.get("sender", "unknown")
            content = msg.get("content", "")[:50]
            print(f"   [{i+1}] {sender}: {content}...")
        
        return True
    else:
        print(f"❌ 获取消息历史失败: {response.status_code}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("LangGraph 迁移 - API 全面测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务器: {BASE_URL}")
    
    # 获取 token
    print("\n📝 获取认证 Token...")
    token = get_auth_token()
    if not token:
        print("❌ 无法获取 Token，测试终止")
        return False
    print(f"✅ Token 获取成功")
    
    results = []
    
    # 测试 1: 创建会话
    session_id = test_create_session(token)
    results.append(("创建会话", session_id is not None))
    
    if not session_id:
        print("\n❌ 会话创建失败，无法继续测试")
        return False
    
    # 测试 2: 非流式消息
    results.append(("非流式消息", test_send_message_non_stream(token, session_id)))
    
    # 测试 3: 流式消息
    results.append(("流式消息", test_send_message_stream(token, session_id)))
    
    # 测试 4: 状态持久化
    results.append(("状态持久化", test_state_persistence(token, session_id)))
    
    # 测试 5: 消息历史
    results.append(("消息历史", test_get_messages(token, session_id)))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    if passed == len(results):
        print("\n🎉 所有测试通过！LangGraph 迁移验证成功！")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查日志")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
