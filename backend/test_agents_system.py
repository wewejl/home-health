#!/usr/bin/env python3
"""
智能体系统测试脚本
全面测试所有 13 个医疗专科智能体的功能
"""
import requests
import json
import time
from typing import Dict, List, Any

BASE_URL = "http://localhost:8100"
HEADERS = {
    "Authorization": "Bearer test_1",
    "Content-Type": "application/json"
}


class AgentTestResult:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.create_session_ok = False
        self.conversation_ok = False
        self.special_action_ok = None  # None表示不适用, True/False表示结果
        self.error = None
        self.response_time = 0
        self.ai_response = ""
        self.session_id = ""

    def to_dict(self) -> Dict:
        return {
            "agent_type": self.agent_type,
            "create_session": "✓" if self.create_session_ok else "✗",
            "conversation": "✓" if self.conversation_ok else "✗",
            "special_action": "N/A" if self.special_action_ok is None else ("✓" if self.special_action_ok else "✗"),
            "response_time_ms": self.response_time,
            "error": self.error or ""
        }


def create_session(agent_type: str) -> tuple[bool, str, str]:
    """创建会话，返回 (成功, session_id, 错误信息)"""
    try:
        start = time.time()
        response = requests.post(
            f"{BASE_URL}/sessions",
            headers=HEADERS,
            json={"agent_type": agent_type},
            timeout=10
        )
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            return True, data.get("session_id", ""), ""
        else:
            return False, "", f"HTTP {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, "", str(e)


def send_message(session_id: str, content: str, action: str = "conversation",
                attachments: List = None) -> tuple[bool, str, str, float]:
    """发送消息，返回 (成功, AI回复, 错误信息, 响应时间ms)"""
    try:
        start = time.time()
        payload = {"content": content, "action": action}
        if attachments:
            payload["attachments"] = attachments

        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/messages",
            headers=HEADERS,
            json=payload,
            timeout=60  # AI 响应可能需要较长时间
        )
        elapsed = (time.time() - start) * 1000

        if response.status_code == 200:
            data = response.json()
            ai_message = data.get("ai_message", {})
            ai_content = ai_message.get("content", "")
            return True, ai_content, "", elapsed
        else:
            return False, "", f"HTTP {response.status_code}: {response.text[:100]}", elapsed
    except Exception as e:
        return False, "", str(e), 0


def test_agent_capabilities(agent_type: str, capabilities: Dict) -> AgentTestResult:
    """测试单个智能体的所有功能"""
    result = AgentTestResult(agent_type)

    # 1. 测试会话创建
    ok, session_id, error = create_session(agent_type)
    result.create_session_ok = ok
    result.session_id = session_id
    if not ok:
        result.error = error
        return result

    # 2. 测试基础对话
    test_questions = {
        "general": "我最近感觉头痛，请问我应该怎么做？",
        "dermatology": "我手臂上有个红疹，有点痒，请问是什么？",
        "cardiology": "我最近经常感到心慌，需要检查什么？",
        "orthopedics": "我膝盖疼，尤其是上下楼梯时，怎么办？",
        "pediatrics": "我家孩子3岁，最近不爱吃饭，怎么办？",
        "obstetrics_gynecology": "我月经不规律，可能是什么原因？",
        "gastroenterology": "我最近胃胀，消化不良，怎么办？",
        "respiratory": "我最近咳嗽不止，有痰，怎么办？",
        "endocrinology": "我最近体重增加明显，容易疲劳，怎么办？",
        "neurology": "我最近经常失眠，还伴有头晕，怎么办？",
        "ophthalmology": "我最近眼睛干涩，看久了屏幕会疼，怎么办？",
        "otorhinolaryngology": "我最近经常鼻塞，嗅觉下降，怎么办？",
        "stomatology": "我牙龈经常出血，怎么办？",
    }

    question = test_questions.get(agent_type, "你好，我有些不舒服")
    ok, response, error, elapsed = send_message(session_id, question)
    result.conversation_ok = ok
    result.response_time = elapsed
    result.ai_response = response[:200] if response else ""

    if not ok:
        result.error = error
        return result

    # 3. 测试特殊功能
    actions = capabilities.get("actions", [])

    if "analyze_skin" in actions and agent_type == "dermatology":
        # 测试皮肤图像分析
        ok, response, error, _ = send_message(
            session_id,
            "请帮我分析这张皮肤的图片",
            action="analyze_skin",
            attachments=[{"type": "image", "url": "https://picsum.photos/300/300"}]
        )
        result.special_action_ok = ok
        if error:
            result.error = error

    elif "interpret_ecg" in actions and agent_type == "cardiology":
        # 测试心电图解读
        ok, response, error, _ = send_message(
            session_id,
            "请帮我分析这份心电图",
            action="interpret_ecg",
            attachments=[{"type": "image", "url": "https://picsum.photos/400/200"}]
        )
        result.special_action_ok = ok
        if error:
            result.error = error

    elif "interpret_xray" in actions and agent_type == "orthopedics":
        # 测试X光片解读
        ok, response, error, _ = send_message(
            session_id,
            "请帮我分析这张X光片",
            action="interpret_xray",
            attachments=[{"type": "image", "url": "https://picsum.photos/400/300"}]
        )
        result.special_action_ok = ok
        if error:
            result.error = error

    elif "interpret_report" in actions:
        # 测试报告解读
        ok, response, error, _ = send_message(
            session_id,
            "请帮我解读这份检查报告",
            action="interpret_report",
            attachments=[{"type": "image", "url": "https://picsum.photos/300/400"}]
        )
        result.special_action_ok = ok
        if error:
            result.error = error

    return result


def test_streaming_response() -> tuple[bool, str]:
    """测试流式响应"""
    try:
        # 创建会话
        response = requests.post(
            f"{BASE_URL}/sessions",
            headers=HEADERS,
            json={"agent_type": "general"},
            timeout=10
        )
        if response.status_code != 200:
            return False, f"会话创建失败: {response.status_code}"

        session_id = response.json().get("session_id")
        if not session_id:
            return False, "未获取到 session_id"

        # 发送流式请求
        headers_stream = HEADERS.copy()
        headers_stream["Accept"] = "text/event-stream"

        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/messages",
            headers=headers_stream,
            json={"content": "你好，请做一个简短的自我介绍"},
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            return False, f"流式请求失败: {response.status_code}"

        # 读取 SSE 事件
        events = []
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('event:'):
                    events.append(line)

        has_chunk = any('chunk' in e for e in events)
        has_complete = any('complete' in e for e in events)

        if has_chunk and has_complete:
            return True, f"收到 {len(events)} 个 SSE 事件"
        else:
            return False, f"SSE 事件不完整: {events}"

    except Exception as e:
        return False, str(e)


def test_state_management() -> tuple[bool, str]:
    """测试状态管理（多轮对话）"""
    try:
        # 创建会话
        response = requests.post(
            f"{BASE_URL}/sessions",
            headers=HEADERS,
            json={"agent_type": "dermatology"},
            timeout=10
        )
        session_id = response.json().get("session_id")

        # 第一轮对话
        ok1, resp1, err1, _ = send_message(session_id, "我脸上有皮疹")
        if not ok1:
            return False, f"第一轮对话失败: {err1}"

        # 第二轮对话（检查AI是否记住上下文）
        ok2, resp2, err2, _ = send_message(session_id, "我刚才说的是哪个部位？")
        if not ok2:
            return False, f"第二轮对话失败: {err2}"

        # 检查AI是否记住了"脸"这个信息
        if "脸" in resp2 or "面部" in resp2:
            return True, "状态管理正常，AI记住上下文"
        else:
            return False, f"状态管理可能有问题，AI回复: {resp2[:100]}"

    except Exception as e:
        return False, str(e)


def test_error_handling() -> List[tuple[str, bool, str]]:
    """测试错误处理"""
    tests = []

    # 1. 无效的 agent_type
    response = requests.post(
        f"{BASE_URL}/sessions",
        headers=HEADERS,
        json={"agent_type": "invalid_specialty"},
        timeout=10
    )
    tests.append((
        "无效 agent_type",
        response.status_code == 400,
        f"返回状态码 {response.status_code} (期望 400)"
    ))

    # 2. 无效的 session_id
    response = requests.post(
        f"{BASE_URL}/sessions/invalid-session-id/messages",
        headers=HEADERS,
        json={"content": "测试"},
        timeout=10
    )
    tests.append((
        "无效 session_id",
        response.status_code == 404,
        f"返回状态码 {response.status_code} (期望 404)"
    ))

    # 3. 无效的 Bearer token
    headers_invalid = HEADERS.copy()
    headers_invalid["Authorization"] = "Bearer invalid_token"
    response = requests.post(
        f"{BASE_URL}/sessions",
        headers=headers_invalid,
        json={"agent_type": "general"},
        timeout=10
    )
    tests.append((
        "无效认证 token",
        response.status_code == 401,
        f"返回状态码 {response.status_code} (期望 401)"
    ))

    return tests


def print_header(text: str):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_table(results: List[AgentTestResult]):
    """打印测试结果表格"""
    print("\n┌────────────────────────┬──────┬─────────────┬─────────────┬──────────┐")
    print("│ 智能体                │ 会话 │ 对话        │ 特殊功能    │ 响应时间 │")
    print("├────────────────────────┼──────┼─────────────┼─────────────┼──────────┤")

    for r in results:
        special = r.special_action_ok if r.special_action_ok is not None else "N/A"
        special_str = "✓" if special is True else ("✗" if special is False else "—")
        time_str = f"{r.response_time:.0f}ms" if r.response_time > 0 else "—"

        # 中文名称映射
        names = {
            "general": "全科",
            "dermatology": "皮肤科",
            "cardiology": "心血管科",
            "orthopedics": "骨科",
            "pediatrics": "儿科",
            "obstetrics_gynecology": "妇产科",
            "gastroenterology": "消化内科",
            "respiratory": "呼吸内科",
            "endocrinology": "内分泌科",
            "neurology": "神经内科",
            "ophthalmology": "眼科",
            "otorhinolaryngology": "耳鼻喉科",
            "stomatology": "口腔科",
        }

        name = names.get(r.agent_type, r.agent_type)[:20]
        print(f"│ {name:<22} │ {r.create_session_ok and '✓' or '✗':<4} │ "
              f"{r.conversation_ok and '✓' or '✗':<11} │ {special_str:<11} │ {time_str:<8} │")

    print("└────────────────────────┴──────┴─────────────┴─────────────┴──────────┘")


def main():
    print_header("🏥 鑫琳医生智能体系统测试")

    # 获取所有智能体列表
    print("\n[1/6] 获取智能体列表...")
    response = requests.get(f"{BASE_URL}/sessions/agents", timeout=10)
    if response.status_code != 200:
        print(f"❌ 无法获取智能体列表: {response.status_code}")
        return

    agents = response.json()
    print(f"✓ 找到 {len(agents)} 个智能体")

    # 测试每个智能体
    print_header("[2/6] 测试各智能体基础功能")
    results = []
    for agent_type, capabilities in agents.items():
        print(f"\n测试 {agent_type}...", end=" ", flush=True)
        result = test_agent_capabilities(agent_type, capabilities)
        results.append(result)
        status = "✓" if result.create_session_ok and result.conversation_ok else "✗"
        print(f"{status} ({result.response_time:.0f}ms)")

    print_table(results)

    # 测试流式响应
    print_header("[3/6] 测试流式响应 (SSE)")
    ok, msg = test_streaming_response()
    print(f"{'✓' if ok else '✗'} {msg}")

    # 测试状态管理
    print_header("[4/6] 测试状态管理（多轮对话）")
    ok, msg = test_state_management()
    print(f"{'✓' if ok else '✗'} {msg}")

    # 测试错误处理
    print_header("[5/6] 测试错误处理")
    error_tests = test_error_handling()
    for name, ok, msg in error_tests:
        print(f"{'✓' if ok else '✗'} {name}: {msg}")

    # 生成总结
    print_header("[6/6] 测试总结")

    total = len(results)
    session_ok = sum(1 for r in results if r.create_session_ok)
    conv_ok = sum(1 for r in results if r.conversation_ok)
    special_ok = sum(1 for r in results if r.special_action_ok is True)
    special_total = sum(1 for r in results if r.special_action_ok is not None)

    print(f"\n📊 测试统计:")
    print(f"  • 智能体总数: {total}")
    print(f"  • 会话创建成功: {session_ok}/{total}")
    print(f"  • 对话功能成功: {conv_ok}/{total}")
    print(f"  • 特殊功能成功: {special_ok}/{special_total}")

    # 显示AI回复示例
    print(f"\n💬 AI 回复示例:")
    for r in results[:3]:
        if r.ai_response:
            print(f"  • {r.agent_type}: {r.ai_response[:80]}...")

    # 错误汇总
    errors = [r for r in results if r.error]
    if errors:
        print(f"\n⚠️  错误汇总:")
        for e in errors:
            print(f"  • {e.agent_type}: {e.error[:100]}")

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
