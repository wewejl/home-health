#!/usr/bin/env python3
"""
完整流式测试 - 模拟前端行为
"""
import asyncio
import httpx
import json

async def test_full_stream():
    print("🧪 完整流式测试")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream('POST', 'http://localhost:8000/chat/stream', json={
            'session_id': 'test_full_flow',
            'his_user_id': 'doctor_web',
            'message': '患者同时服用阿司匹林和华法林，需要注意什么？'
        }) as response:
            print(f"✅ 连接成功: {response.status_code}\n")

            event_count = 0
            thought_events = []
            tool_calls = []
            tool_results = []
            final_response = ""

            async for line in response.aiter_lines():
                if not line.startswith('data: '):
                    continue

                data_str = line[6:].strip()

                if data_str == '[DONE]' or data_str == '':
                    continue

                try:
                    data = json.loads(data_str)
                    event_count += 1
                    event_type = data.get('event_type', data.get('type', 'unknown'))

                    # 处理不同事件类型
                    if event_type == 'ThoughtEvent':
                        content = data.get('data', {}).get('content', '')
                        thought_events.append(content)
                        print(f"[事件 {event_count}] 💭 思考: {content[:60]}...")

                    elif event_type == 'ToolCallRequestEvent':
                        content = data.get('data', {}).get('content', '')
                        tool_calls.append(content)
                        # 提取工具名
                        try:
                            calls = json.loads(content)
                            tool_name = calls[0]['name'] if calls else 'unknown'
                            print(f"[事件 {event_count}] 🔧 工具调用: {tool_name}")
                        except:
                            print(f"[事件 {event_count}] 🔧 工具调用请求")

                    elif event_type == 'ToolCallExecutionEvent':
                        content = data.get('data', {}).get('content', '')
                        tool_results.append(content)
                        print(f"[事件 {event_count}] ✅ 工具执行完成")

                    elif event_type == 'Response':
                        content = data.get('data', {}).get('chat_message', {}).get('content', '')
                        final_response = content
                        print(f"[事件 {event_count}] 💬 最终回复收到 ({len(content)} 字符)")

                    elif event_type in ['done', 'unknown']:
                        print(f"[事件 {event_count}] ✅ 完成")
                        break

                    elif event_type == 'error':
                        error_msg = data.get('error', data.get('message', 'Unknown error'))
                        print(f"[事件 {event_count}] ❌ 错误: {error_msg}")
                        break

                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON 解析失败: {e}")
                    print(f"   原始数据: {data_str[:100]}")
                except Exception as e:
                    print(f"⚠️  处理错误: {e}")

    # 统计结果
    print("\n" + "=" * 70)
    print("📊 流式统计:")
    print(f"  总事件数: {event_count}")
    print(f"  思考事件: {len(thought_events)}")
    print(f"  工具调用: {len(tool_calls)}")
    print(f"  工具结果: {len(tool_results)}")
    print(f"  最终回复: {len(final_response)} 字符")

    # 验证
    if final_response:
        print("\n✅ 测试通过！流式输出正常工作")
        print(f"\n最终回复预览:\n{final_response[:200]}...")
    else:
        print("\n❌ 测试失败！未收到最终回复")

if __name__ == '__main__':
    asyncio.run(test_full_stream())
