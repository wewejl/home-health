#!/usr/bin/env python3
"""
前端集成测试 - 测试医患对话和病历创建功能
"""
import asyncio
import httpx
import json
from datetime import datetime


async def test_frontend_flow():
    """测试完整的医患对话流程"""

    # 模拟医患对话（用户之前提供的真实对话）
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

    # 模拟前端发送的请求（包含医生ID和患者ID）
    request_data = {
        "session_id": f"web_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "his_user_id": "doctor_web_001",
        "his_patient_id": "P001",  # 使用 P001 作为测试患者ID
        "message": doctor_patient_dialogue
    }

    print("=" * 80)
    print("🌐 前端集成测试")
    print("=" * 80)
    print()
    print("📋 请求信息：")
    print(f"  - 会话ID: {request_data['session_id']}")
    print(f"  - 医生ID: {request_data['his_user_id']}")
    print(f"  - 患者ID: {request_data['his_patient_id']}")
    print(f"  - 对话长度: {len(doctor_patient_dialogue)} 字符")
    print()
    print("=" * 80)
    print()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", url, json=request_data) as response:
                print(f"📡 响应状态: {response.status_code}")
                print()

                if response.status_code != 200:
                    print("❌ 请求失败！")
                    return

                print("📊 流式响应事件：")
                print("-" * 80)

                events_summary = {
                    'ThoughtEvent': 0,
                    'ToolCallRequestEvent': 0,
                    'ToolCallExecutionEvent': 0,
                    'Response': 0,
                    'ToolCallSummaryMessage': 0
                }

                final_response_content = ""
                medical_record_id = None

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()

                        if not data_str or data_str == '{"event_type":"done"}':
                            continue

                        try:
                            data = json.loads(data_str)
                            event_type = data.get('event_type', 'Unknown')

                            if event_type in events_summary:
                                events_summary[event_type] += 1

                            # 处理具体事件
                            if event_type == 'ToolCallRequestEvent':
                                tool_name = '未知工具'
                                try:
                                    content = data.get('data', {}).get('content', '')
                                    if 'medical_record_extractor' in content:
                                        tool_name = '📋 智能问诊记录员'
                                    elif 'save_to_his_system' in content:
                                        tool_name = '💾 保存病历系统'
                                except:
                                    pass
                                print(f"  🔧 [{event_type}] 调用 {tool_name}")

                            elif event_type == 'ToolCallExecutionEvent':
                                print(f"  ✅ [{event_type}] 工具执行完成")

                                # 尝试提取病历编号
                                try:
                                    result = data.get('data', {}).get('result', '')
                                    if result and result.startswith('MR'):
                                        medical_record_id = result
                                        print(f"     └─ 病历编号: {result}")
                                except:
                                    pass

                            elif event_type == 'Response':
                                content = data.get('data', {}).get('chat_message', {}).get('content', '')
                                if content:
                                    final_response_content = content
                                    print(f"  💬 [{event_type}] 主Agent回复 ({len(content)} 字符)")

                            elif event_type == 'ToolCallSummaryMessage':
                                print(f"  📋 [{event_type}] 工具调用总结")

                        except json.JSONDecodeError as e:
                            print(f"  ⚠️ JSON 解析错误: {e}")

                print("-" * 80)
                print()
                print("📈 事件统计：")
                for event_type, count in events_summary.items():
                    if count > 0:
                        print(f"  - {event_type}: {count} 次")
                print()

                print("=" * 80)
                print("📝 主Agent最终回复：")
                print("=" * 80)
                if final_response_content:
                    print(final_response_content)
                    print("=" * 80)
                else:
                    print("⚠️ 未收到最终回复")
                    print("=" * 80)

                print()
                print("🎯 测试结果：")
                print("-" * 80)

                # 检查各项功能
                tests_passed = []
                tests_failed = []

                # 1. 检查是否成功创建病历
                # 从Response内容中提取病历编号（MR后面跟着14位数字）
                import re
                if final_response_content and 'MR' in final_response_content:
                    match = re.search(r'MR\d{14}', final_response_content)
                    if match:
                        medical_record_id = match.group()
                        tests_passed.append(f"✅ 病历创建成功: {medical_record_id}")
                    else:
                        tests_failed.append("❌ 无法解析病历编号")
                else:
                    tests_failed.append("❌ 病历创建失败")

                # 2. 检查主Agent是否生成了总结
                if final_response_content:
                    if '病历已创建' in final_response_content or '病历编号' in final_response_content:
                        tests_passed.append("✅ 主Agent确认病历创建")
                    else:
                        tests_failed.append("⚠️ 主Agent未明确确认病历创建")

                    # 检查是否包含关键信息回顾
                    keywords = ['主诉', '症状', '病史', '建议']
                    found_keywords = [kw for kw in keywords if kw in final_response_content]
                    if found_keywords:
                        tests_passed.append(f"✅ 总结包含关键信息: {', '.join(found_keywords)}")
                    else:
                        tests_failed.append("⚠️ 总结缺少关键信息")

                    # 检查是否包含医疗建议
                    if '建议' in final_response_content:
                        tests_passed.append("✅ 包含医疗建议")
                    else:
                        tests_failed.append("⚠️ 缺少医疗建议")
                else:
                    tests_failed.append("❌ 主Agent未生成总结")

                # 3. 检查患者ID和医生ID是否正确传递
                if medical_record_id:
                    import os
                    record_file = f"data/medical_records/P001/{medical_record_id}.json"
                    if os.path.exists(record_file):
                        with open(record_file, 'r', encoding='utf-8') as f:
                            record = json.load(f)
                            if record.get('patient_id') == 'P001':
                                tests_passed.append(f"✅ 患者ID正确关联: {record.get('patient_id')}")
                            else:
                                tests_failed.append(f"❌ 患者ID错误: {record.get('patient_id')}")

                            if record.get('his_user_id') == 'doctor_web_001':
                                tests_passed.append(f"✅ 医生ID正确关联: {record.get('his_user_id')}")
                            else:
                                tests_failed.append(f"❌ 医生ID错误: {record.get('his_user_id')}")

                print()
                print("通过的项目：")
                for test in tests_passed:
                    print(f"  {test}")

                if tests_failed:
                    print()
                    print("失败/警告的项目：")
                    for test in tests_failed:
                        print(f"  {test}")

                print()
                print("=" * 80)

                if not tests_failed:
                    print("🎉 所有测试通过！前端集成正常工作。")
                else:
                    print(f"⚠️ {len(tests_failed)} 项测试失败，请检查")

                print("=" * 80)

        except Exception as e:
            print(f"❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_frontend_flow())
