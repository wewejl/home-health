#!/usr/bin/env python3
"""
皮肤智能体接口系统测试脚本
测试皮肤分析功能是否正常工作
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
    """加载图片为 base64"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')


def test_derma_workflow():
    """测试完整的皮肤科智能体工作流"""
    
    print("=" * 60)
    print("皮肤科智能体接口系统测试")
    print("=" * 60)
    
    client = httpx.Client(timeout=120.0)
    
    # 步骤 1: 登录
    print("\n[步骤 1] 登录获取 Token...")
    try:
        resp = client.post(
            f"{BASE_URL}/auth/login",
            json={"phone": TEST_PHONE, "code": TEST_CODE}
        )
        if resp.status_code != 200:
            print(f"❌ 登录失败: {resp.status_code}")
            print(resp.text)
            return
        
        data = resp.json()
        token = data.get("token")
        print(f"✅ 登录成功，Token: {token[:20]}...")
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 步骤 2: 开始会话
    print("\n[步骤 2] 开始皮肤科问诊会话...")
    try:
        resp = client.post(
            f"{BASE_URL}/derma/start",
            headers=headers,
            json={"chief_complaint": "皮肤瘙痒"}
        )
        if resp.status_code != 200:
            print(f"❌ 创建会话失败: {resp.status_code}")
            print(resp.text)
            return
        
        data = resp.json()
        session_id = data.get("session_id")
        print(f"✅ 会话已创建，ID: {session_id}")
        print(f"   助手回复: {data.get('message', '')[:100]}...")
    except Exception as e:
        print(f"❌ 创建会话异常: {e}")
        return
    
    # 步骤 3: 对话交互
    print("\n[步骤 3] 发送对话消息...")
    try:
        resp = client.post(
            f"{BASE_URL}/derma/{session_id}/continue",
            headers=headers,
            json={
                "history": [],
                "current_input": {"message": "手臂上起了红疹，很痒"},
                "task_type": "conversation"
            }
        )
        if resp.status_code != 200:
            print(f"❌ 对话失败: {resp.status_code}")
            print(resp.text)
            return
        
        data = resp.json()
        print(f"✅ 对话成功")
        print(f"   助手回复: {data.get('message', '')[:150]}...")
        print(f"   awaiting_image: {data.get('awaiting_image', False)}")
    except Exception as e:
        print(f"❌ 对话异常: {e}")
        return
    
    # 步骤 4: 上传皮肤照片进行分析
    print(f"\n[步骤 4] 上传皮肤照片进行分析...")
    print(f"   图片路径: {TEST_IMAGE_PATH}")
    
    if not Path(TEST_IMAGE_PATH).exists():
        print(f"❌ 图片文件不存在: {TEST_IMAGE_PATH}")
        return
    
    try:
        # 加载图片
        image_base64 = load_image_as_base64(TEST_IMAGE_PATH)
        print(f"   图片大小: {len(image_base64)} 字符")
        
        # 发送皮肤分析请求
        resp = client.post(
            f"{BASE_URL}/derma/{session_id}/continue",
            headers=headers,
            json={
                "history": [],
                "current_input": {"message": "请帮我分析这张皮肤照片"},
                "task_type": "skin_analysis",
                "image_base64": image_base64
            }
        )
        
        if resp.status_code != 200:
            print(f"❌ 皮肤分析失败: {resp.status_code}")
            print(resp.text)
            return
        
        data = resp.json()
        print(f"✅ 皮肤分析成功")
        print(f"\n   类型: {data.get('type')}")
        print(f"   助手回复: {data.get('message', '')[:200]}...")
        
        # 检查分析结果
        skin_analysis = data.get("skin_analysis")
        if skin_analysis:
            print(f"\n   📊 皮肤分析结果:")
            print(f"      皮损描述: {skin_analysis.get('lesion_description', '')[:100]}...")
            print(f"      风险等级: {skin_analysis.get('risk_level')}")
            print(f"      需要就医: {skin_analysis.get('need_offline_visit')}")
            
            conditions = skin_analysis.get("possible_conditions", [])
            if conditions:
                print(f"      可能情况:")
                for c in conditions[:3]:
                    print(f"        - {c.get('name')}: {c.get('description', '')[:50]}...")
        else:
            print(f"\n   ⚠️  未返回 skin_analysis 字段")
            print(f"   完整响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ 皮肤分析异常: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 步骤 5: 获取会话状态
    print(f"\n[步骤 5] 获取会话状态...")
    try:
        resp = client.get(
            f"{BASE_URL}/derma/{session_id}",
            headers=headers
        )
        if resp.status_code != 200:
            print(f"❌ 获取会话失败: {resp.status_code}")
            return
        
        data = resp.json()
        print(f"✅ 会话状态:")
        print(f"   stage: {data.get('stage')}")
        print(f"   progress: {data.get('progress')}%")
        print(f"   awaiting_image: {data.get('awaiting_image')}")
    except Exception as e:
        print(f"❌ 获取会话异常: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    client.close()


if __name__ == "__main__":
    test_derma_workflow()
