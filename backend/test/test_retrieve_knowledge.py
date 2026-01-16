"""
测试 retrieve_derma_knowledge 工具

验证皮肤科知识检索功能
"""
import pytest
from app.services.dermatology.react_tools import retrieve_derma_knowledge


class TestRetrieveDermaKnowledge:
    """测试 retrieve_derma_knowledge 工具"""
    
    def test_retrieve_with_symptoms(self):
        """根据症状检索知识"""
        result = retrieve_derma_knowledge.invoke({
            "symptoms": ["红疹", "瘙痒"],
            "location": "手臂"
        })
        
        assert isinstance(result, list)
        assert len(result) > 0
        # 每个结果应包含必要字段
        for ref in result:
            assert "id" in ref
            assert "title" in ref
            assert "snippet" in ref
    
    def test_retrieve_with_query(self):
        """根据查询词检索知识"""
        result = retrieve_derma_knowledge.invoke({
            "symptoms": ["水疱"],
            "location": "手指",
            "query": "汗疱疹"
        })
        
        assert isinstance(result, list)
    
    def test_retrieve_returns_relevant_content(self):
        """检索结果应与症状相关"""
        result = retrieve_derma_knowledge.invoke({
            "symptoms": ["红斑", "脱屑"],
            "location": "面部"
        })
        
        assert isinstance(result, list)
        # 至少返回一条结果
        assert len(result) >= 1
    
    def test_retrieve_with_empty_symptoms(self):
        """空症状也应返回结果"""
        result = retrieve_derma_knowledge.invoke({
            "symptoms": [],
            "location": "全身"
        })
        
        assert isinstance(result, list)
    
    def test_retrieve_result_structure(self):
        """验证返回结果的数据结构"""
        result = retrieve_derma_knowledge.invoke({
            "symptoms": ["瘙痒"],
            "location": "腿部"
        })
        
        assert isinstance(result, list)
        if len(result) > 0:
            ref = result[0]
            assert isinstance(ref.get("id"), str)
            assert isinstance(ref.get("title"), str)
            assert isinstance(ref.get("snippet"), str)
            # source 和 link 是可选的
            if "source" in ref:
                assert ref["source"] is None or isinstance(ref["source"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
