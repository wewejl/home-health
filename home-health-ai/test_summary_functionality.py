#!/usr/bin/env python3
"""测试主 Agent 总结功能"""
import asyncio
import httpx

async def test_summary():
    """测试病历创建后主 Agent 是否生成总结"""

    # 使用用户提供的长对话
    doctor_patient_dialogue = """
医生：您好，请问您哪里不舒服？

患者：唉，我头疼头晕有好几天了

医生：具体是哪个部位疼？是前额、太阳穴还是后脑勺？

患者：后脑勺这边，跳跳地疼

医生：持续多久了？

患者：大概一周了吧

医生：是一直疼，还是时有时无？

患者：时有时无，特别是下午的时候更严重

医生：还有其他不舒服吗？比如恶心、呕吐？

患者：有时候会恶心，没有吐过

医生：有没有视力模糊或者说话不清楚的情况？

患者：暂时没有

医生：以前有过类似的症状吗？或者有什么慢性病吗？

患者：我有高血压，大概5年了

医生：平时血压控制得怎么样？有吃降压药吗？

患者：有时候会忘记吃药，血压不太稳定

医生：平时生活习惯怎么样？抽烟喝酒吗？

患者：烟抽得挺多，每天一包，酒不常喝

医生：好的，我明白了。根据您的症状和病史，需要注意以下几点：
1. 高血压可能是头痛的主要原因
2. 下午血压容易升高，所以下午症状更明显
3. 抽烟会加重血管收缩，建议戒烟
4. 需要规律服药控制血压

患者：好的，谢谢医生
"""

    url = "http://localhost:8000/chat/stream"
    request_body = {
        "session_id": "test_summary_session",
        "his_user_id": "doctor_test_001",
        "his_patient_id": "P003",
        "message": doctor_patient_dialogue
    }

    print("📤 发送测试请求...")
    print(f"会话ID: {request_body['session_id']}")
    print(f"医生ID: {request_body['his_user_id']}")
    print(f"患者ID: {request_body['his_patient_id']}")
    print(f"对话内容: {doctor_patient_dialogue[:50]}...")
    print("\n" + "="*60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, json=request_body) as response:
            print(f"响应状态: {response.status_code}\n")

            final_content = ""
            record_created = False
            summary_found = False
            all_events = []

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    # Skip keep-alive and done messages
                    if not data or data == '{"event_type":"done"}':
                        continue

                    # Check for error
                    if '"event_type":"error"' in data:
                        print(f"❌ 错误: {data}")
                        break

                    all_events.append(data)

                    # Parse JSON to check event types
                    import json
                    try:
                        event = json.loads(data)
                        event_type = event.get('event_type', 'Unknown')

                        # Look for Response events (final messages)
                        if event_type == 'Response':
                            if 'data' in event and 'chat_message' in event['data']:
                                content = event['data']['chat_message'].get('content', '')
                                if content and content != final_content:
                                    final_content = content
                                    print(f"📝 [Response] Agent 回复:\n{content}\n")
                                    print("="*60 + "\n")

                                    # Check if medical record was created
                                    if 'MR' in content and '病历' in content:
                                        record_created = True

                                    # Check if there's a summary after record creation
                                    if record_created and ('主诉' in content or '建议' in content or '症状' in content or '提取' in content):
                                        summary_found = True
                                        print("✅ 发现总结内容！")

                        # Print other event types
                        elif event_type == 'ToolCallRequestEvent':
                            print(f"🔧 [{event_type}] 工具调用请求")
                        elif event_type == 'ToolCallExecutionEvent':
                            print(f"✅ [{event_type}] 工具执行完成")
                        elif event_type == 'ToolCallSummaryMessage':
                            print(f"📋 [{event_type}] 工具调用总结")
                        elif event_type == 'ThoughtEvent':
                            print(f"💭 [{event_type}] AI 思考中")

                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON 解析错误: {e}")

    print("\n" + "="*60)
    print("📊 测试结果:")
    print(f"  - 病历已创建: {'✅ 是' if record_created else '❌ 否'}")
    print(f"  - 主Agent总结: {'✅ 是' if summary_found else '❌ 否'}")
    print("="*60)

    if record_created and summary_found:
        print("\n🎉 测试通过！主 Agent 成功生成了总结")
    elif record_created and not summary_found:
        print("\n⚠️  病历已创建，但主 Agent 未生成总结")
        print("   需要检查 system_message 中的总结指令")
    else:
        print("\n❌ 测试失败")

if __name__ == "__main__":
    asyncio.run(test_summary())
