# LangGraph 多智能体架构迁移实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有 CrewAI 多智能体系统迁移到 LangGraph，实现响应速度从 30-60 秒降低到 1-3 秒，同时保持 API 完全兼容。

**Architecture:** 采用渐进式迁移策略，先创建 LangGraph 基础设施和 LLM 提供者单例，然后实现皮肤科 LangGraph Agent，通过配置开关实现 A/B 测试，验证后逐步迁移其他科室。

**Tech Stack:** LangGraph 0.2+, LangChain-Core 0.3+, LangChain-OpenAI 0.2+, Pydantic 2.x, FastAPI

---

## 实施概览

本计划分为 6 个阶段，共 17 个任务：

1. **Phase 1: 基础设施搭建** (Task 1-4) - 安装依赖、配置、LLM Provider、基类
2. **Phase 2: 皮肤科实现** (Task 5-12) - Prompts、状态、节点、图构建、Wrapper
3. **Phase 3: 测试验证** (Task 13-14) - 单元测试、集成测试
4. **Phase 4: 性能对比** (Task 15) - Benchmark 测试
5. **Phase 5: 文档更新** (Task 16) - 迁移指南
6. **Phase 6: 优化** (Task 17) - 日志监控

预计总工作量：3-4 天

---

## Phase 1: 基础设施搭建

### Task 1: 安装 LangGraph 依赖

**Files:**
- Modify: `/Users/zhuxinye/Desktop/project/home-health/backend/requirements.txt`

**Step 1: 添加依赖**

在 requirements.txt 末尾添加：
```
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
```

**Step 2: 安装**

Run: `cd /Users/zhuxinye/Desktop/project/home-health/backend && pip install -r requirements.txt`

**Step 3: 验证**

Run: `python -c "import langgraph; print('OK')"`

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "feat: add langgraph dependencies"
```

---

### Task 2: 添加配置

**Files:**
- Modify: `/Users/zhuxinye/Desktop/project/home-health/backend/app/config.py:35`

**Step 1: 添加配置项**

在 LLM 配置后添加：
```python
    # LangGraph 配置
    USE_LANGGRAPH: bool = True
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 1
    LLM_MAX_TOKENS: int = 1500
    LLM_VL_MAX_TOKENS: int = 2000
```

**Step 2: Commit**

```bash
git add app/config.py
git commit -m "feat: add langgraph config"
```

---

### Task 3: 创建 LLM Provider

**Files:**
- Create: `/Users/zhuxinye/Desktop/project/home-health/backend/app/services/llm_provider.py`

**Step 1: 创建文件**

完整代码见设计文档第 7.2 节。

**Step 2: Commit**

```bash
git add app/services/llm_provider.py
git commit -m "feat: add LLM provider singleton"
```

---

### Task 4: 创建 LangGraph 基类

**Files:**
- Create: `/Users/zhuxinye/Desktop/project/home-health/backend/app/services/base/langgraph_base.py`
- Modify: `/Users/zhuxinye/Desktop/project/home-health/backend/app/services/base/__init__.py`

**Step 1: 创建基类**

完整代码见设计文档第 8 节。

**Step 2: 更新 __init__.py**

```python
from .base_agent import BaseAgent
from .langgraph_base import LangGraphAgentBase, BaseAgentState

__all__ = ["BaseAgent", "LangGraphAgentBase", "BaseAgentState"]
```

**Step 3: Commit**

```bash
git add app/services/base/
git commit -m "feat: add LangGraphAgentBase"
```

---

## Phase 2: 皮肤科实现

### Task 5-7: 创建支持文件

创建以下文件（代码见设计文档）：
- `prompts.py` - 精简 Prompts
- `derma_state.py` - 状态定义
- `output_models.py` - Pydantic 模型

Commit: `git commit -m "feat: add derma support files"`

---

### Task 8-10: 实现 Agent

创建 `derma_langgraph_agent.py`，分三部分实现：
1. 路由、问候、对话节点
2. 图片分析、诊断节点
3. 图构建和能力配置

完整代码见设计文档第 9 节。

Commit: `git commit -m "feat: implement derma langgraph agent"`

---

### Task 11-12: 创建 Wrapper 和配置开关

**Files:**
- Create: `derma_langgraph_wrapper.py`
- Modify: `__init__.py`

在 `__init__.py` 添加切换逻辑：
```python
from ...config import get_settings
settings = get_settings()

if settings.USE_LANGGRAPH:
    from .derma_langgraph_wrapper import DermaLangGraphWrapper as DermaAgentWrapper
else:
    from .derma_wrapper import DermaAgentWrapper
```

Commit: `git commit -m "feat: add config switch"`

---

## Phase 3-6: 测试、性能、文档、优化

详细步骤见原设计文档 Task 13-17。

---

## 验收标准

### 功能
- [ ] 所有单元测试通过
- [ ] 手动测试完整对话流程
- [ ] API 接口完全兼容

### 性能
- [ ] 问候 < 0.1s
- [ ] 对话 1-3s
- [ ] 图片分析 5-10s
- [ ] Token < 600/round

### 兼容性
- [ ] 配置开关正常
- [ ] 可切换回 CrewAI
- [ ] 状态结构兼容

---

## 执行建议

建议按顺序执行 Task 1-12，每完成一个 Task 立即测试验证。Task 13-17 可根据实际情况调整优先级。

完整代码实现请参考原设计文档中的详细代码示例。
