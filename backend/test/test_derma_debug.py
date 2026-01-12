#!/usr/bin/env python3
"""
调试版本：打印详细请求信息
"""

import sys
import json
import base64
from pathlib import Path

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx")
    sys.exit(1)


BASE_URL = "http://localhost:8000"
TEST_PHONE = "13800138000"
TEST_CODE = "000000"
TEST_IMAGE_PATH = "/Users/zhuxinye/Desktop/project/home-health/images/2.jpg"


def load_image_as_base64(image_path: str) -> str:
    """加载图片为 base64（纯字符串，不带前缀）"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def main():
    client = httpx.Client(timeout=120.0)
    
    # 登录
    print("登录...")
    resp = client.post(f"{BASE_URL}/auth/login", json={"phone": TEST_PHONE, "code": TEST_CODE})
    token = resp.json()["token"]
    print(f"Token: {token[:30]}...\n")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 创建会话
    print("创建会话...")
    resp = client.post(f"{BASE_URL}/derma/start", headers=headers, json={})
    session_id = resp.json()["session_id"]
    print(f"Session ID: {session_id}\n")
    
    # 加载图片
    print(f"加载图片: {TEST_IMAGE_PATH}")
    image_base64 = load_image_as_base64(TEST_IMAGE_PATH)
    print(f"Base64 长度: {len(image_base64)}")
    print(f"Base64 前50字符: {image_base64[:50]}")
    print(f"Base64 是否包含 'data:': {'data:' in image_base64}\n")
    
    # 构建请求
    request_data = {
        "history": [],
        "current_input": {"message": "请分析这张皮肤照片"},
        "task_type": "skin_analysis",
        "image_base64": image_base64
    }
    
    print("发送皮肤分析请求...")
    print(f"task_type: {request_data['task_type']}")
    print(f"image_base64 长度: {len(request_data['image_base64'])}")
    print(f"message: {request_data['current_input']['message']}\n")
    
    resp = client.post(
        f"{BASE_URL}/derma/{session_id}/continue",
        headers=headers,
        json=request_data
    )
    
    print(f"响应状态码: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n响应类型: {data.get('type')}")
        print(f"awaiting_image: {data.get('awaiting_image')}")
        print(f"skin_analysis 是否存在: {data.get('skin_analysis') is not None}")
        print(f"\n助手消息:\n{data.get('message')}\n")
        
        if data.get('skin_analysis'):
            print("✅ 皮肤分析成功!")
            analysis = data['skin_analysis']
            print(f"皮损描述: {analysis.get('lesion_description', '')[:100]}")
        else:
            print("❌ 未返回皮肤分析结果")
            print(f"\n完整响应:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"请求失败: {resp.text}")
    
    client.close()


if __name__ == "__main__":
    main()
