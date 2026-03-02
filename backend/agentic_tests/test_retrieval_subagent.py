import pytest

from backend.app.agentic.subagents.retrieval_agent import RetrievalSubagent


class _FakeKnowledgeClient:
    def __init__(self):
        self.calls = []

    async def search(self, query: str, specialty: str, top_k: int):
        self.calls.append((query, specialty, top_k))
        if specialty == "cardiology":
            return {
                "found": False,
                "results": [],
                "count": 0,
                "query_used": query,
                "specialty": specialty,
            }
        return {
            "found": True,
            "results": [
                {"content": "证据A：胸痛伴气短提示需要进一步评估。", "score": 0.91},
                {"content": "证据A：胸痛伴气短提示需要进一步评估。", "score": 0.88},
                {"content": "证据B：持续胸闷建议门诊心电图检查。", "score": 0.73},
            ],
            "count": 3,
            "query_used": query,
            "specialty": specialty,
        }


@pytest.mark.asyncio
async def test_retrieval_subagent_dedupes_and_fallbacks(monkeypatch):
    fake = _FakeKnowledgeClient()

    agent = RetrievalSubagent()
    monkeypatch.setattr(agent, "_search", fake.search)
    bundle = await agent.run(
        conversation_text="用户：胸闷两天，活动后加重。",
        last_user_message="胸闷气短怎么回事？",
        specialty="cardiology",
        query_hint="胸闷气短 鉴别",
    )

    assert bundle.found is True
    assert bundle.count == 2
    assert bundle.confidence > 0.7
    assert any("胸痛伴气短" in h or "胸闷" in h for h in bundle.highlights)
    assert [call[1] for call in fake.calls] == ["cardiology", "general"]
