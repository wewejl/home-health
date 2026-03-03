#!/usr/bin/env python3
"""
测试 AutoGen 0.7.5 官方 API

验证:
1. 导入是否正确
2. 模型客户端创建
3. 智能体创建
4. 工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 测试导入
print("=" * 60)
print("🧪 测试 AutoGen 0.7.5 导入")
print("=" * 60)

try:
    from autogen_agentchat.agents import AssistantAgent
    print("✅ autogen_agentchat.agents.AssistantAgent")
except ImportError as e:
    print(f"❌ autogen_agentchat.agents.AssistantAgent: {e}")
    sys.exit(1)

try:
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    print("✅ autogen_ext.models.openai.OpenAIChatCompletionClient")
except ImportError as e:
    print(f"❌ autogen_ext.models.openai.OpenAIChatCompletionClient: {e}")
    sys.exit(1)

try:
    from autogen_core.models import ModelFamily
    print("✅ autogen_core.models.ModelFamily")
except ImportError as e:
    print(f"❌ autogen_core.models.ModelFamily: {e}")
    sys.exit(1)

try:
    from autogen_agentchat.messages import TextMessage
    print("✅ autogen_agentchat.messages.TextMessage")
except ImportError as e:
    print(f"❌ autogen_agentchat.messages.TextMessage: {e}")
    sys.exit(1)

try:
    from autogen_core import CancellationToken
    print("✅ autogen_core.CancellationToken")
except ImportError as e:
    print(f"❌ autogen_core.CancellationToken: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🧪 测试模型客户端创建")
print("=" * 60)

# 创建模型客户端
try:
    from config.settings import create_model_client

    model_client = create_model_client(parallel_tool_calls=False)
    print(f"✅ 模型客户端创建成功: {type(model_client).__name__}")
except Exception as e:
    print(f"❌ 模型客户端创建失败: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🧪 测试全科医生智能体创建")
print("=" * 60)

try:
    from src.agents.general_practitioner import create_general_practitioner

    agent = create_general_practitioner()
    print(f"✅ 智能体创建成功: {agent.name}")
except Exception as e:
    print(f"❌ 智能体创建失败: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("🧪 测试工具函数")
print("=" * 60)

try:
    from src.agents.general_practitioner import search_disease_info, search_medication

    # 测试疾病查询
    result = asyncio.run(search_disease_info("高血压"))
    print(f"✅ search_disease_info('高血压'):\n{result}\n")

    # 测试药物查询
    result = asyncio.run(search_medication("阿司匹林"))
    print(f"✅ search_medication('阿司匹林'):\n{result}\n")

except Exception as e:
    print(f"❌ 工具函数测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
print()
print("📝 安装命令（如果尚未安装）:")
print("   pip install -U 'autogen-agentchat' 'autogen-ext[openai]'")
print()
