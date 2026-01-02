# AI诊室待实施修改事项

> **状态更新 (2025-12-29)**: 以下修改已在 `diagnosis_agent.py` 中实施完成。

以下为当前确定的功能修改需求，供开发落地：

## 1. 请求体统一化
- **目标**：使用单一请求结构，携带完整上下文，适配开始/继续问诊。
- **结构**：
  ```json
  {
    "consultation_id": "9e141b61-ddbf-45cd-bd4a-b3e1173799ea",
    "force_conclude": false,
    "history": [
      {"role": "assistant", "message": "你好，我是AI医生，请描述病情。", "timestamp": "2025-12-29T11:35:12Z"},
      {"role": "user", "message": "最近总是左下腹疼，午后更明显。", "timestamp": "2025-12-29T11:35:32Z"}
    ],
    "current_input": {"message": "over_week"}
  }
  ```
- **说明**：
  - `history` 建议传最近 5-10 条问答，保证上下文。
  - 统一入口后，后端应根据 `history` 重建状态。
  - `force_conclude` 保持原语义（"直接出结论" 按钮）。

## 2. 进度与诊断触发逻辑改为 AI 评估
- **现状问题**：`progress` 和 `should_continue` 使用硬编码阈值（`min(20 + questions*15, 90)`、`questions_asked >= 8`）。
- **修改方向**：
  1. 在 `ASSESSMENT_PROMPT` 中要求 LLM 输出以下字段：
     ```json
     {
       "progress": 0-100,
       "should_diagnose": true/false,
       "can_conclude": true/false,
       "confidence": 0-100,
       "missing_info": [],
       "reasoning": "..."
     }
     ```
  2. `assess_progress()` 解析上述字段，fallback 时才使用简单策略。
  3. `should_continue()` 逻辑改为：
     ```python
     if state["force_conclude"]:
         return "diagnose"
     if state.get("should_diagnose"):
         return "diagnose"
     return "continue"
     ```
  4. 删除 `questions_asked >= 8` 等硬编码阈值。
  5. 诊断生成后可继续保留 `progress = 100`（表示已完成）。

## 3. 初始快捷选项由 AI 生成
- **现状问题**：`greet()` 返回固定 5 个选项（头痛头晕等）。
- **修改方向**：
  1. 新增 `INITIAL_OPTIONS_PROMPT`（或复用 `generate_quick_options`，但传入 `initial=True`），根据 `chief_complaint` 输出 4-5 个选项。
  2. Prompt 要求包含至少一个“其他/不确定”类选项，结构同现有 `quick_options`。
  3. `greet()` 调用该逻辑生成首轮按钮；若 LLM 解析失败，则 fallback 到默认选项。

## 4. 文档与前端配合
- README 已记录统一请求体示例，后续逻辑变更（AI 评估进度、诊断触发）完成后，需补充说明。
- 前端需要按新请求体实现，确保每次请求都带 `history + current_input`。

## 5. 兼容性与测试建议
- 修改后需回归以下场景：
  1. 正常多轮问诊（确保 AI 不会频繁误判 `should_diagnose`）。
  2. `force_conclude=true` 仍可立即生成诊断。
  3. 首轮快捷选项会根据不同主诉动态变化。
  4. 若 LLM 返回不可解析 JSON，fall back 逻辑仍可避免崩溃。

如需进一步细化 Prompt 或提供实施建议，可在本文件继续补充。
