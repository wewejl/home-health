"""
KnowledgeService 单元测试

测试知识库服务的所有方法：
- 知识库创建
- 文档添加
- 文档搜索
- 文档审核
- 知识库统计更新
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

# 导入 KnowledgeService 和相关模型
try:
    from app.services.knowledge_service import KnowledgeService
    from app.models.knowledge_base import KnowledgeBase, KnowledgeDocument
    from app.models.doctor import Doctor
    from app.models.department import Department
except ImportError:
    from backend.app.services.knowledge_service import KnowledgeService
    from backend.app.models.knowledge_base import KnowledgeBase, KnowledgeDocument
    from backend.app.models.doctor import Doctor
    from backend.app.models.department import Department


# ============================================================================
# 知识库创建测试
# ============================================================================

class TestCreateKnowledgeBase:
    """测试知识库创建"""

    def test_create_knowledge_base_basic(self, db_session: Session):
        """测试创建基本知识库"""
        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_001",
            name="测试知识库",
            description="用于测试的知识库"
        )
        assert kb is not None
        assert kb.id == "test_kb_001"
        assert kb.name == "测试知识库"
        assert kb.description == "用于测试的知识库"
        assert kb.total_documents == 0
        assert kb.total_chunks == 0
        assert kb.is_active is True

    def test_create_knowledge_base_with_doctor(self, db_session: Session):
        """测试创建关联医生的知识库"""
        # 创建一个测试医生和科室（Doctor 需要 department_id）
        dept = Department(
            name="皮肤科",
            description="皮肤科科室",
            icon="skin",
            sort_order=1
        )
        db_session.add(dept)
        db_session.commit()
        db_session.refresh(dept)

        doctor = Doctor(
            name="测试医生",
            department_id=dept.id
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(doctor)

        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_002",
            name="医生知识库",
            doctor_id=doctor.id
        )
        assert kb.doctor_id == doctor.id

    def test_create_knowledge_base_with_department(self, db_session: Session):
        """测试创建关联科室的知识库"""
        # 创建测试科室
        dept = Department(
            name="皮肤科",
            description="皮肤科科室",
            icon="skin",
            sort_order=1
        )
        db_session.add(dept)
        db_session.commit()
        db_session.refresh(dept)

        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_003",
            name="科室知识库",
            department_id=dept.id
        )
        assert kb.department_id == dept.id

    def test_create_knowledge_base_full(self, db_session: Session):
        """测试创建完整参数的知识库"""
        # 创建测试科室和医生
        dept = Department(
            name="内科",
            description="内科科室",
            icon="heart",
            sort_order=2
        )
        db_session.add(dept)
        db_session.commit()
        db_session.refresh(dept)

        doctor = Doctor(
            name="测试医生",
            department_id=dept.id
        )
        db_session.add(doctor)
        db_session.commit()
        db_session.refresh(doctor)

        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_004",
            name="完整知识库",
            description="包含医生和科室的知识库",
            doctor_id=doctor.id,
            department_id=dept.id
        )
        assert kb.doctor_id == doctor.id
        assert kb.department_id == dept.id


# ============================================================================
# 文档添加测试
# ============================================================================

class TestAddDocument:
    """测试文档添加"""

    def test_add_document_basic(self, db_session: Session):
        """测试添加基本文档"""
        # 先创建知识库
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_add_001",
            name="测试知识库"
        )

        # 添加文档
        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_add_001",
            title="测试文档",
            content="这是测试文档的内容"
        )

        assert doc is not None
        assert doc.title == "测试文档"
        assert doc.content == "这是测试文档的内容"
        assert doc.status == "pending"
        assert doc.knowledge_base_id == "test_kb_add_001"

    def test_add_document_with_all_fields(self, db_session: Session):
        """测试添加包含所有字段的文档"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_add_002",
            name="测试知识库"
        )

        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_add_002",
            title="完整文档",
            content="完整文档的内容",
            doc_type="guideline",
            source="医学指南",
            tags=["心血管", "高血压"],
            metadata={"author": "张医生", "year": 2024}
        )

        assert doc.doc_type == "guideline"
        assert doc.source == "医学指南"
        assert doc.tags == ["心血管", "高血压"]
        assert doc.doc_metadata == {"author": "张医生", "year": 2024}

    def test_add_document_updates_kb_stats(self, db_session: Session):
        """测试添加文档时更新知识库统计"""
        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_add_003",
            name="测试知识库"
        )
        assert kb.total_documents == 0

        # 添加第一份文档
        KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_add_003",
            title="文档1",
            content="内容1"
        )

        # 刷新知识库
        db_session.refresh(kb)
        assert kb.total_documents >= 1  # 文档数应该增加

    def test_add_multiple_documents(self, db_session: Session):
        """测试添加多个文档"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_add_004",
            name="测试知识库"
        )

        # 添加多个文档
        for i in range(3):
            KnowledgeService.add_document(
                db_session,
                knowledge_base_id="test_kb_add_004",
                title=f"文档{i+1}",
                content=f"内容{i+1}"
            )

        # 验证文档数量
        docs = db_session.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == "test_kb_add_004"
        ).all()
        assert len(docs) == 3


# ============================================================================
# 文档搜索测试
# ============================================================================

class TestSearchDocuments:
    """测试文档搜索"""

    def test_search_empty_kb(self, db_session: Session):
        """测试搜索空知识库"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_001",
            name="空知识库"
        )

        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_001",
            query="测试"
        )
        assert results == []

    def test_search_pending_documents_not_found(self, db_session: Session):
        """测试待审核的文档不会被搜索到"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_002",
            name="测试知识库"
        )

        # 添加文档（默认状态为 pending）
        KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_search_002",
            title="高血压治疗",
            content="高血压的治疗方法"
        )

        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_002",
            query="高血压"
        )
        assert results == []  # pending 文档不应该被搜索到

    def test_search_approved_documents(self, db_session: Session):
        """测试搜索已审核的文档"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_003",
            name="测试知识库"
        )

        # 添加并审核文档
        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_search_003",
            title="糖尿病饮食",
            content="糖尿病患者应该注意饮食控制"
        )
        KnowledgeService.approve_document(db_session, doc.id, True, reviewed_by=1)

        # 搜索
        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_003",
            query="糖尿病"
        )
        assert len(results) == 1
        assert results[0].title == "糖尿病饮食"

    def test_search_keyword_matching(self, db_session: Session):
        """测试关键词匹配"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_004",
            name="测试知识库"
        )

        # 添加多个文档
        docs = [
            ("高血压指南", "高血压的诊断标准是140/90mmHg"),
            ("糖尿病管理", "糖尿病的血糖控制目标"),
            ("心脏病预防", "心脏病的预防措施")
        ]
        for title, content in docs:
            doc = KnowledgeService.add_document(
                db_session,
                knowledge_base_id="test_kb_search_004",
                title=title,
                content=content
            )
            KnowledgeService.approve_document(db_session, doc.id, True, reviewed_by=1)

        # 搜索"高血压"
        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_004",
            query="高血压"
        )
        assert len(results) >= 1
        assert "高血压" in results[0].title

    def test_search_tag_matching(self, db_session: Session):
        """测试标签匹配加分"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_005",
            name="测试知识库"
        )

        # 添加带标签的文档
        doc1 = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_search_005",
            title="心血管疾病",
            content="心脏相关疾病",
            tags=["心脏", "心血管"]
        )
        doc2 = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_search_005",
            title="其他疾病",
            content="提及心脏的其他内容"
        )
        KnowledgeService.approve_document(db_session, doc1.id, True, reviewed_by=1)
        KnowledgeService.approve_document(db_session, doc2.id, True, reviewed_by=1)

        # 搜索"心脏" - 带标签的应该排前面
        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_005",
            query="心脏"
        )
        assert len(results) >= 1
        # 第一个结果应该是匹配标签的文档（分数更高）
        assert results[0].title == "心血管疾病"

    def test_search_top_k_limit(self, db_session: Session):
        """测试搜索结果数量限制"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_search_006",
            name="测试知识库"
        )

        # 添加多个文档
        for i in range(5):
            doc = KnowledgeService.add_document(
                db_session,
                knowledge_base_id="test_kb_search_006",
                title=f"疾病{i}治疗",
                content=f"疾病{i}的治疗方法"
            )
            KnowledgeService.approve_document(db_session, doc.id, True, reviewed_by=1)

        # 只返回 top 3
        results = KnowledgeService.search_documents(
            db_session,
            knowledge_base_id="test_kb_search_006",
            query="治疗",
            top_k=3
        )
        assert len(results) <= 3


# ============================================================================
# 上下文获取测试
# ============================================================================

class TestGetContextForQuery:
    """测试获取查询上下文"""

    def test_get_context_empty_kb(self, db_session: Session):
        """测试空知识库返回空上下文"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_ctx_001",
            name="测试知识库"
        )

        context = KnowledgeService.get_context_for_query(
            db_session,
            knowledge_base_id="test_kb_ctx_001",
            query="测试"
        )
        assert context == ""

    def test_get_context_with_documents(self, db_session: Session):
        """测试有文档时获取上下文"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_ctx_002",
            name="测试知识库"
        )

        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_ctx_002",
            title="心绞痛治疗",
            content="心绞痛的治疗包括药物治疗和介入治疗"
        )
        KnowledgeService.approve_document(db_session, doc.id, True, reviewed_by=1)

        context = KnowledgeService.get_context_for_query(
            db_session,
            knowledge_base_id="test_kb_ctx_002",
            query="心绞痛"
        )
        assert context != ""
        assert "参考资料:" in context
        assert "心绞痛治疗" in context

    def test_get_context_none_kb_id(self, db_session: Session):
        """测试 None kb_id 返回空字符串"""
        context = KnowledgeService.get_context_for_query(
            db_session,
            knowledge_base_id=None,
            query="测试"
        )
        assert context == ""

    def test_get_context_empty_string_kb_id(self, db_session: Session):
        """测试空字符串 kb_id 返回空字符串"""
        context = KnowledgeService.get_context_for_query(
            db_session,
            knowledge_base_id="",
            query="测试"
        )
        assert context == ""


# ============================================================================
# 文档审核测试
# ============================================================================

class TestApproveDocument:
    """测试文档审核"""

    def test_approve_document_success(self, db_session: Session):
        """测试审核通过文档"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_appr_001",
            name="测试知识库"
        )

        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_appr_001",
            title="测试文档",
            content="内容"
        )

        approved_doc = KnowledgeService.approve_document(
            db_session,
            doc_id=doc.id,
            approved=True,
            reviewed_by=1,
            review_notes="审核通过"
        )

        assert approved_doc.status == "approved"
        assert approved_doc.reviewed_by == 1
        assert approved_doc.review_notes == "审核通过"
        assert approved_doc.reviewed_at is not None
        assert approved_doc.is_indexed is True
        assert approved_doc.chunk_count == 1

    def test_reject_document(self, db_session: Session):
        """测试拒绝文档"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_appr_002",
            name="测试知识库"
        )

        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_appr_002",
            title="测试文档",
            content="内容"
        )

        rejected_doc = KnowledgeService.approve_document(
            db_session,
            doc_id=doc.id,
            approved=False,
            reviewed_by=1,
            review_notes="质量不合格"
        )

        assert rejected_doc.status == "rejected"
        assert rejected_doc.review_notes == "质量不合格"
        # 拒绝的文档不应该被索引
        assert rejected_doc.is_indexed is False

    def test_approve_nonexistent_document(self, db_session: Session):
        """测试审核不存在的文档"""
        result = KnowledgeService.approve_document(
            db_session,
            doc_id=99999,
            approved=True,
            reviewed_by=1
        )
        assert result is None

    def test_approve_without_notes(self, db_session: Session):
        """测试审核不填写备注"""
        KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_appr_003",
            name="测试知识库"
        )

        doc = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_appr_003",
            title="测试文档",
            content="内容"
        )

        approved_doc = KnowledgeService.approve_document(
            db_session,
            doc_id=doc.id,
            approved=True,
            reviewed_by=1
        )

        assert approved_doc.status == "approved"
        assert approved_doc.review_notes is None


# ============================================================================
# 知识库统计更新测试
# ============================================================================

class TestUpdateKbStats:
    """测试知识库统计更新"""

    def test_update_kb_stats_empty(self, db_session: Session):
        """测试更新空知识库统计"""
        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_stats_001",
            name="测试知识库"
        )

        KnowledgeService.update_kb_stats(db_session, "test_kb_stats_001")
        db_session.refresh(kb)

        assert kb.total_documents == 0
        assert kb.total_chunks == 0

    def test_update_kb_stats_with_documents(self, db_session: Session):
        """测试更新有文档的知识库统计"""
        kb = KnowledgeService.create_knowledge_base(
            db_session,
            kb_id="test_kb_stats_002",
            name="测试知识库"
        )

        # 添加3个文档，审核2个
        doc1 = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_stats_002",
            title="文档1",
            content="内容1"
        )
        doc2 = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_stats_002",
            title="文档2",
            content="内容2"
        )
        doc3 = KnowledgeService.add_document(
            db_session,
            knowledge_base_id="test_kb_stats_002",
            title="文档3",
            content="内容3"
        )

        KnowledgeService.approve_document(db_session, doc1.id, True, reviewed_by=1)
        KnowledgeService.approve_document(db_session, doc2.id, True, reviewed_by=1)

        KnowledgeService.update_kb_stats(db_session, "test_kb_stats_002")
        db_session.refresh(kb)

        assert kb.total_documents == 3
        assert kb.total_chunks == 2  # 只有已审核的

    def test_update_kb_stats_nonexistent_kb(self, db_session: Session):
        """测试更新不存在的知识库统计"""
        # 应该不会抛出异常
        KnowledgeService.update_kb_stats(db_session, "nonexistent_kb")
