# 诊断展示增强实施计划

> **状态:** ✅ 已完成
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让皮肤科 ReAct Agent 实现"查资料 → 推理 → 结构化诊断"的完整流程，前端展示中间建议、引用证据和诊断卡。

**Architecture:** 后端扩展 ReAct 状态和 Schema，新增检索工具和结构化诊断输出；iOS 端扩展模型并实现 UI 组件。

**Tech Stack:** Python/FastAPI/Pydantic/LangGraph (后端), Swift/SwiftUI (iOS)

---

## Task 1: 后端状态扩展

**Files:**
- Modify: `backend/app/services/dermatology/react_state.py`
- Test: `backend/test/test_react_state.py`

**Step 1:** Create test file `backend/test/test_react_state.py` with tests for `advice_history`, `diagnosis_card`, `reasoning_steps` fields.

**Step 2:** Run: `cd backend && python -m pytest test/test_react_state.py -v` — Expected: FAIL

**Step 3:** Modify `react_state.py`: Add `advice_history: List[dict]`, `diagnosis_card: Optional[dict]`, `reasoning_steps: List[str]` to `DermaReActState` and `create_react_initial_state()`.

**Step 4:** Run: `cd backend && python -m pytest test/test_react_state.py -v` — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(backend): extend DermaReActState with advice_history, diagnosis_card, reasoning_steps"`

---

## Task 2: 后端 Schema 扩展

**Files:**
- Modify: `backend/app/schemas/derma.py`
- Test: `backend/test/test_derma_schema.py`

**Step 1:** Create test file with tests for `DermaAdviceSchema`, `DermaKnowledgeRefSchema`, `DermaConditionSchema`, `DermaDiagnosisCardSchema`.

**Step 2:** Run tests — Expected: FAIL

**Step 3:** Add new schemas to `derma.py` and extend `DermaResponse` with `advice_history`, `diagnosis_card`, `knowledge_refs`, `reasoning_steps`.

**Step 4:** Run tests — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(backend): add DermaAdviceSchema, DermaDiagnosisCardSchema"`

---

## Task 3: API 响应构建扩展

**Files:**
- Modify: `backend/app/routes/derma.py`
- Test: `backend/test/test_build_response.py`

**Step 1:** Create test file with tests for `build_response()` including new fields.

**Step 2:** Run tests — Expected: FAIL

**Step 3:** Modify `build_response()` to include `advice_history`, `diagnosis_card`, `knowledge_refs`, `reasoning_steps`.

**Step 4:** Run tests — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(backend): extend build_response for new fields"`

---

## Task 4: 检索工具实现

**Files:**
- Modify: `backend/app/services/dermatology/react_tools.py`
- Test: `backend/test/test_retrieve_knowledge.py`

**Step 1:** Create test file for `retrieve_derma_knowledge` tool.

**Step 2:** Run tests — Expected: FAIL

**Step 3:** Implement `retrieve_derma_knowledge` with local knowledge base (5 entries). Update `get_derma_tools()`.

**Step 4:** Run tests — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(backend): add retrieve_derma_knowledge tool"`

---

## Task 5: 结构化诊断输出

**Files:**
- Modify: `backend/app/services/dermatology/react_tools.py`
- Test: `backend/test/test_structured_diagnosis.py`

**Step 1:** Create test file for `generate_structured_diagnosis` tool.

**Step 2:** Run tests — Expected: FAIL

**Step 3:** Implement `generate_structured_diagnosis` with LLM structured output returning `DiagnosisOutput`.

**Step 4:** Run tests — Expected: PASS

**Step 5:** Commit: `git commit -m "feat(backend): add generate_structured_diagnosis tool"`

---

## Task 6: iOS 模型扩展

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Models/UnifiedChatModels.swift`

**Step 1:** Add `AdviceEntry`, `KnowledgeRef`, `DiagnosisCondition`, `DiagnosisCard` structs with Codable.

**Step 2:** Extend `UnifiedMessageResponse` with `adviceHistory`, `diagnosisCard`, `knowledgeRefs`, `reasoningSteps`.

**Step 3:** Build: `xcodebuild -scheme xinlingyisheng build` — Expected: BUILD SUCCEEDED

**Step 4:** Commit: `git commit -m "feat(ios): add AdviceEntry, DiagnosisCard models"`

---

## Task 7: iOS AdviceCardView 组件

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Components/Diagnosis/AdviceCardView.swift`

**Step 1:** Create SwiftUI component with title, content, evidence tags, accept button.

**Step 2:** Build — Expected: BUILD SUCCEEDED

**Step 3:** Commit: `git commit -m "feat(ios): add AdviceCardView component"`

---

## Task 8: iOS DiagnosisSummaryCard 组件

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Components/Diagnosis/DiagnosisSummaryCard.swift`

**Step 1:** Create SwiftUI component with risk badge, summary, conditions, reasoning timeline, care plan, references, CTA button.

**Step 2:** Also create helper views: `RiskLevelBadge`, `ConditionRowView`, `ReasoningTimelineView`, `EvidenceListView`.

**Step 3:** Build — Expected: BUILD SUCCEEDED

**Step 4:** Commit: `git commit -m "feat(ios): add DiagnosisSummaryCard component"`

---

## Task 9: iOS ViewModel 扩展

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/ViewModels/UnifiedChatViewModel.swift`

**Step 1:** Add `@Published var adviceHistory`, `diagnosisCard`, `knowledgeRefs`.

**Step 2:** Update response handling to populate new properties.

**Step 3:** Build — Expected: BUILD SUCCEEDED

**Step 4:** Commit: `git commit -m "feat(ios): extend UnifiedChatViewModel for diagnosis display"`

---

## Task 10: iOS 聊天界面集成

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/ModernConsultationView.swift`

**Step 1:** Add `DiagnosisSummaryCard` display after message list when `diagnosisCard != nil`.

**Step 2:** Build — Expected: BUILD SUCCEEDED

**Step 3:** Commit: `git commit -m "feat(ios): integrate DiagnosisSummaryCard into chat view"`

---

## Task 11: 更新 API 文档

**Files:**
- Modify: `docs/API_CONTRACT.md`

**Step 1:** Add documentation for `advice_history`, `diagnosis_card`, `knowledge_refs`, `reasoning_steps` response fields.

**Step 2:** Commit: `git commit -m "docs: update API_CONTRACT with new diagnosis fields"`

---

## Task 12: 端到端测试

**Files:**
- Create: `backend/test/test_diagnosis_e2e.py`

**Step 1:** Create E2E test covering: state creation → symptom collection → knowledge retrieval → diagnosis generation → response building.

**Step 2:** Run: `cd backend && python -m pytest test/test_diagnosis_e2e.py -v` — Expected: PASS

**Step 3:** Commit: `git commit -m "test(backend): add diagnosis display E2E test"`

---

## Summary

| Task | Files | Estimated Time |
|------|-------|----------------|
| 1. 状态扩展 | react_state.py | 15 min |
| 2. Schema 扩展 | derma.py | 20 min |
| 3. API 响应 | derma.py (routes) | 15 min |
| 4. 检索工具 | react_tools.py | 30 min |
| 5. 结构化诊断 | react_tools.py | 30 min |
| 6. iOS 模型 | UnifiedChatModels.swift | 20 min |
| 7. AdviceCardView | New file | 20 min |
| 8. DiagnosisSummaryCard | New file | 40 min |
| 9. ViewModel | UnifiedChatViewModel.swift | 15 min |
| 10. 界面集成 | ModernConsultationView.swift | 15 min |
| 11. API 文档 | API_CONTRACT.md | 10 min |
| 12. E2E 测试 | test_diagnosis_e2e.py | 20 min |

**Total: ~4 hours**
