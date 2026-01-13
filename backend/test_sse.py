#!/usr/bin/env python3
"""
测试 SSE 流式输出
"""
import requests
import json

API_BASE = "http://localhost:8000"

# 1. 登录获取 token
print("1. 登录...")
login_response = requests.post(
    f"{API_BASE}/admin/auth/login",
    json={"username": "admin", "password": "admin123"}
)
if login_response.status_code != 200:
    print(f"登录失败: {login_response.status_code}")
    print(login_response.text)
    exit(1)

token = login_response.json()["access_token"]
print(f"✓ 登录成功，token: {token[:20]}...")

# 2. 创建会话
print("\n2. 创建会话...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

session_response = requests.post(
    f"{API_BASE}/derma/start",
    headers=headers,
    json={"chief_complaint": ""}
)

if session_response.status_code != 200:
    print(f"创建会话失败: {session_response.status_code}")
    print(session_response.text)
    exit(1)

session_data = session_response.json()
session_id = session_data["session_id"]
print(f"✓ 会话创建成功，ID: {session_id}")
print(f"  初始消息: {session_data.get('message', '')[:50]}...")

# 3. 测试流式请求
print("\n3. 测试流式请求...")
stream_headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

stream_body = {
    "history": [
        {
            "role": "assistant",
            "message": session_data.get("message", ""),
            "timestamp": "2026-01-13T11:00:00"
        }
    ],
    "current_input": {
        "message": "手上起了红疹，很痒"
    },
    "task_type": "conversation"
}

print(f"  发送消息: {stream_body['current_input']['message']}")
print("  等待流式响应...\n")

try:
    response = requests.post(
        f"{API_BASE}/derma/{session_id}/continue",
        headers=stream_headers,
        json=stream_body,
        stream=True,
        timeout=60
    )
    
    print(f"  响应状态: {response.status_code}")
    print(f"  响应头: {dict(response.headers)}\n")
    
    if response.status_code != 200:
        print(f"错误响应: {response.text}")
        exit(1)
    
    event_count = 0
    for line in response.iter_lines(decode_unicode=True):
        if line:
            print(f"  [{event_count}] {line}")
            event_count += 1
            
            # 限制输出行数
            if event_count > 100:
                print("  ... (输出过多，已截断)")
                break
    
    print(f"\n✓ 流式响应完成，共 {event_count} 行")

except requests.exceptions.Timeout:
    print("✗ 请求超时（60秒）")
except Exception as e:
    print(f"✗ 请求失败: {e}")
    import traceback
    traceback.print_exc()
