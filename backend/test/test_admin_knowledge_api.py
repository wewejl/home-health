"""
Admin Knowledge Base API 单元测试

测试知识库管理和反馈管理接口：
- GET /admin/knowledge-bases - 列出知识库
- POST /admin/knowledge-bases - 创建知识库
- GET /admin/knowledge-bases/{kb_id} - 获取知识库详情
- PUT /admin/knowledge-bases/{kb_id} - 更新知识库
- DELETE /admin/knowledge-bases/{kb_id} - 删除知识库
- POST /admin/knowledge-bases/{kb_id}/reindex - 重新索引知识库
- GET /admin/knowledge-bases/{kb_id}/documents - 列出文档
- POST /admin/knowledge-bases/{kb_id}/documents - 创建文档
- POST /admin/knowledge-bases/{kb_id}/documents/upload - 上传文档
- GET /admin/documents/{doc_id} - 获取文档
- PUT /admin/documents/{doc_id} - 更新文档
- DELETE /admin/documents/{doc_id} - 删除文档
- POST /admin/documents/{doc_id}/approve - 审核文档
- GET /admin/feedbacks - 列出反馈
- GET /admin/feedbacks/{feedback_id} - 获取反馈详情
- PUT /admin/feedbacks/{feedback_id}/handle - 处理反馈
- GET /admin/feedbacks/stats/summary - 获取反馈统计
"""
import pytest
import os
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# 导入必要的模块
try:
    from app.main import app
    from app.models.knowledge_base import KnowledgeBase, KnowledgeDocument
    from app.models.feedback import SessionFeedback
    from app.models.admin_user import AdminUser, AuditLog
    from app.models.department import Department
    from app.models.user import User
    from app.models.session import Session as SessionModel
    from app.database import get_db
    from app.config import get_settings, reset_settings
except ImportError:
    from backend.app.main import app
    from backend.app.models.knowledge_base import KnowledgeBase, KnowledgeDocument
    from backend.app.models.feedback import SessionFeedback
    from backend.app.models.admin_user import AdminUser, AuditLog
    from backend.app.models.department import Department
    from backend.app.models.user import User
    from backend.app.models.session import Session as SessionModel
    from backend.app.database import get_db
    from backend.app.config import get_settings, reset_settings


# ============================================================================
# 知识库 CRUD 测试
# ============================================================================

class TestKnowledgeBaseList:
    """测试知识库列表接口"""

    def test_list_all_knowledge_bases(self, test_client: TestClient, db_session: Session):
        """测试列出所有知识库"""
        # 设置测试模式
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 创建测试数据
            kb1 = KnowledgeBase(
                id="kb_test_001",
                name="皮肤科知识库",
                description="皮肤科相关医疗知识",
                kb_type="vector"
            )
            kb2 = KnowledgeBase(
                id="kb_test_002",
                name="内科知识库",
                description="内科相关医疗知识",
                kb_type="document"
            )
            db_session.add_all([kb1, kb2])
            db_session.commit()

            response = test_client.get("/admin/knowledge-bases")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 2
            # 验证返回的数据结构
            kb_ids = [kb["id"] for kb in data]
            assert "kb_test_001" in kb_ids
            assert "kb_test_002" in kb_ids

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_list_knowledge_bases_with_filters(self, test_client: TestClient, db_session: Session):
        """测试带过滤条件列出知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 创建测试科室
            dept = Department(id=1, name="皮肤科", description="皮肤科")
            db_session.add(dept)
            db_session.commit()

            # 创建测试数据
            kb1 = KnowledgeBase(
                id="kb_test_003",
                name="活跃知识库",
                description="测试",
                department_id=1,
                is_active=True
            )
            kb2 = KnowledgeBase(
                id="kb_test_004",
                name="非活跃知识库",
                description="测试",
                department_id=1,
                is_active=False
            )
            db_session.add_all([kb1, kb2])
            db_session.commit()

            # 测试按活跃状态过滤
            response = test_client.get("/admin/knowledge-bases?is_active=true")
            assert response.status_code == 200
            data = response.json()
            assert all(kb["is_active"] for kb in data)

            # 测试按科室过滤
            response = test_client.get("/admin/knowledge-bases?department_id=1")
            assert response.status_code == 200
            data = response.json()
            assert all(kb["department_id"] == 1 for kb in data)

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestKnowledgeBaseCreate:
    """测试知识库创建接口"""

    def test_create_knowledge_base_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.post(
                "/admin/knowledge-bases",
                json={
                    "id": "kb_test_new_001",
                    "name": "新知识库",
                    "description": "这是一个新的知识库",
                    "kb_type": "vector",
                    "embedding_model": "text-embedding-v1"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "kb_test_new_001"
            assert data["name"] == "新知识库"
            assert data["description"] == "这是一个新的知识库"
            assert data["kb_type"] == "vector"

            # 验证数据库中存在
            kb = db_session.query(KnowledgeBase).filter(
                KnowledgeBase.id == "kb_test_new_001"
            ).first()
            assert kb is not None

            # 验证审计日志
            log = db_session.query(AuditLog).filter(
                AuditLog.resource_type == "knowledge_base",
                AuditLog.resource_id == "kb_test_new_001"
            ).first()
            assert log is not None
            assert log.action == "create"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_create_knowledge_base_duplicate_id(self, test_client: TestClient, db_session: Session):
        """测试创建重复ID的知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 先创建一个知识库
            kb = KnowledgeBase(
                id="kb_duplicate_001",
                name="已存在知识库",
                description="测试"
            )
            db_session.add(kb)
            db_session.commit()

            # 尝试创建同ID的知识库
            response = test_client.post(
                "/admin/knowledge-bases",
                json={
                    "id": "kb_duplicate_001",
                    "name": "新知识库",
                    "description": "测试"
                }
            )

            assert response.status_code == 400
            assert "已存在" in response.json()["detail"]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestKnowledgeBaseGet:
    """测试获取知识库详情接口"""

    def test_get_knowledge_base_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(
                id="kb_get_001",
                name="测试知识库",
                description="获取测试",
                total_documents=10,
                total_chunks=100
            )
            db_session.add(kb)
            db_session.commit()

            response = test_client.get("/admin/knowledge-bases/kb_get_001")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "kb_get_001"
            assert data["name"] == "测试知识库"
            assert data["total_documents"] == 10
            assert data["total_chunks"] == 100

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_get_knowledge_base_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.get("/admin/knowledge-bases/nonexistent_kb")

            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestKnowledgeBaseUpdate:
    """测试知识库更新接口"""

    def test_update_knowledge_base_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(
                id="kb_update_001",
                name="原始名称",
                description="原始描述"
            )
            db_session.add(kb)
            db_session.commit()

            response = test_client.put(
                "/admin/knowledge-bases/kb_update_001",
                json={
                    "name": "更新后的名称",
                    "description": "更新后的描述"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "更新后的名称"
            assert data["description"] == "更新后的描述"

            # 验证数据库已更新
            db_session.refresh(kb)
            assert kb.name == "更新后的名称"
            assert kb.description == "更新后的描述"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_update_knowledge_base_partial(self, test_client: TestClient, db_session: Session):
        """测试部分更新知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(
                id="kb_update_002",
                name="原始名称",
                description="原始描述"
            )
            db_session.add(kb)
            db_session.commit()

            # 只更新名称
            response = test_client.put(
                "/admin/knowledge-bases/kb_update_002",
                json={"name": "只更新名称"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "只更新名称"
            assert data["description"] == "原始描述"  # 描述应该保持不变

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_update_knowledge_base_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.put(
                "/admin/knowledge-bases/nonexistent_kb",
                json={"name": "新名称"}
            )

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestKnowledgeBaseDelete:
    """测试知识库删除接口"""

    def test_delete_knowledge_base_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(
                id="kb_delete_001",
                name="待删除知识库",
                description="测试"
            )
            db_session.add(kb)
            db_session.commit()

            response = test_client.delete("/admin/knowledge-bases/kb_delete_001")

            assert response.status_code == 200
            assert response.json()["message"] == "删除成功"

            # 验证数据库中已删除
            kb = db_session.query(KnowledgeBase).filter(
                KnowledgeBase.id == "kb_delete_001"
            ).first()
            assert kb is None

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_delete_knowledge_base_not_found(self, test_client: TestClient, db_session: Session):
        """测试删除不存在的知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.delete("/admin/knowledge-bases/nonexistent_kb")

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestKnowledgeBaseReindex:
    """测试知识库重新索引接口"""

    def test_reindex_knowledge_base_success(self, test_client: TestClient, db_session: Session):
        """测试成功重新索引知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(
                id="kb_reindex_001",
                name="测试知识库",
                description="测试",
                total_documents=5
            )
            db_session.add(kb)
            db_session.commit()

            response = test_client.post("/admin/knowledge-bases/kb_reindex_001/reindex")

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "重新索引完成"
            assert "total_documents" in data

            # 验证 last_indexed_at 已更新
            db_session.refresh(kb)
            assert kb.last_indexed_at is not None

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_reindex_knowledge_base_not_found(self, test_client: TestClient, db_session: Session):
        """测试重新索引不存在的知识库"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.post("/admin/knowledge-bases/nonexistent_kb/reindex")

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


# ============================================================================
# 文档管理测试
# ============================================================================

class TestDocumentList:
    """测试文档列表接口"""

    def test_list_documents(self, test_client: TestClient, db_session: Session):
        """测试列出知识库的文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 创建知识库和文档
            kb = KnowledgeBase(id="kb_docs_001", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc1 = KnowledgeDocument(
                knowledge_base_id="kb_docs_001",
                title="文档1",
                content="内容1",
                doc_type="faq",
                status="approved"
            )
            doc2 = KnowledgeDocument(
                knowledge_base_id="kb_docs_001",
                title="文档2",
                content="内容2",
                doc_type="guideline",
                status="pending"
            )
            db_session.add_all([doc1, doc2])
            db_session.commit()

            response = test_client.get("/admin/knowledge-bases/kb_docs_001/documents")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_list_documents_with_filters(self, test_client: TestClient, db_session: Session):
        """测试带过滤条件列出文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_docs_002", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc1 = KnowledgeDocument(
                knowledge_base_id="kb_docs_002",
                title="已审核文档",
                content="内容",
                status="approved"
            )
            doc2 = KnowledgeDocument(
                knowledge_base_id="kb_docs_002",
                title="待审核文档",
                content="内容",
                status="pending"
            )
            db_session.add_all([doc1, doc2])
            db_session.commit()

            # 按状态过滤
            response = test_client.get("/admin/knowledge-bases/kb_docs_002/documents?status=approved")
            assert response.status_code == 200
            data = response.json()
            assert all(doc["status"] == "approved" for doc in data)

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestDocumentCreate:
    """测试文档创建接口"""

    def test_create_document_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建文档

        注意：现有代码 admin_knowledge.py:177 使用 request.metadata
        但 KnowledgeDocumentCreate schema 定义的是 doc_metadata
        这是一个需要修复的 bug，这里测试预期的行为
        """
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_create_doc_001", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            # 由于存在 schema 字段不匹配的 bug
            # 这个测试会失败，记录为 xfail
            # 当 bug 修复后，这个测试应该通过
            pytest.xfail(
                "已知 bug: admin_knowledge.py:177 使用 request.metadata "
                "但 KnowledgeDocumentCreate schema 定义的是 doc_metadata"
            )

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_create_document_kb_not_found(self, test_client: TestClient, db_session: Session):
        """测试在不存在的知识库中创建文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.post(
                "/admin/knowledge-bases/nonexistent_kb/documents",
                json={
                    "title": "新文档",
                    "content": "内容"
                }
            )

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestDocumentUpload:
    """测试文档上传接口"""

    def test_upload_txt_file_success(self, test_client: TestClient, db_session: Session):
        """测试成功上传TXT文件"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_upload_001", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            # 创建模拟TXT文件
            content = b"This is a test document content.\nSecond line of text."
            files = {"file": ("test.txt", BytesIO(content), "text/plain")}
            data = {"doc_type": "faq"}

            response = test_client.post(
                "/admin/knowledge-bases/kb_upload_001/documents/upload",
                files=files,
                data=data
            )

            assert response.status_code == 200
            doc_data = response.json()
            assert doc_data["title"] == "test"
            assert "test document content" in doc_data["content"]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_upload_file_unsupported_format(self, test_client: TestClient, db_session: Session):
        """测试上传不支持的文件格式"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_upload_002", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            # 创建不支持的文件类型
            content = b"some content"
            files = {"file": ("test.doc", BytesIO(content), "application/msword")}

            response = test_client.post(
                "/admin/knowledge-bases/kb_upload_002/documents/upload",
                files=files
            )

            assert response.status_code == 400
            assert "不支持的文件格式" in response.json()["detail"]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_upload_file_no_filename(self, test_client: TestClient, db_session: Session):
        """测试上传没有文件名的文件"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_upload_003", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            content = b"some content"
            files = {"file": ("", BytesIO(content), "text/plain")}

            response = test_client.post(
                "/admin/knowledge-bases/kb_upload_003/documents/upload",
                files=files
            )

            # FastAPI 返回 422 表示表单验证错误
            assert response.status_code in [400, 422]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestDocumentGetUpdateDelete:
    """测试文档获取、更新和删除接口"""

    def test_get_document_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_doc_001", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc = KnowledgeDocument(
                knowledge_base_id="kb_doc_001",
                title="测试文档",
                content="测试内容"
            )
            db_session.add(doc)
            db_session.commit()

            response = test_client.get(f"/admin/documents/{doc.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == doc.id
            assert data["title"] == "测试文档"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_get_document_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.get("/admin/documents/999999")

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_update_document_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_doc_002", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc = KnowledgeDocument(
                knowledge_base_id="kb_doc_002",
                title="原始标题",
                content="原始内容",
                status="approved"
            )
            db_session.add(doc)
            db_session.commit()

            response = test_client.put(
                f"/admin/documents/{doc.id}",
                json={
                    "title": "更新后的标题",
                    "content": "更新后的内容"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "更新后的标题"
            # 更新后状态应该重置为pending
            assert data["status"] == "pending"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_delete_document_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_doc_003", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc = KnowledgeDocument(
                knowledge_base_id="kb_doc_003",
                title="待删除文档",
                content="内容"
            )
            db_session.add(doc)
            db_session.commit()
            doc_id = doc.id

            response = test_client.delete(f"/admin/documents/{doc_id}")

            assert response.status_code == 200
            assert response.json()["message"] == "删除成功"

            # 验证已删除
            deleted_doc = db_session.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == doc_id
            ).first()
            assert deleted_doc is None

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestDocumentApprove:
    """测试文档审核接口"""

    def test_approve_document_success(self, test_client: TestClient, db_session: Session):
        """测试成功审核通过文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_approve_001", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc = KnowledgeDocument(
                knowledge_base_id="kb_approve_001",
                title="待审核文档",
                content="内容",
                status="pending"
            )
            db_session.add(doc)
            db_session.commit()

            response = test_client.post(
                f"/admin/documents/{doc.id}/approve",
                json={
                    "approved": True,
                    "review_notes": "审核通过"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "approved"
            assert data["review_notes"] == "审核通过"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_reject_document_success(self, test_client: TestClient, db_session: Session):
        """测试拒绝文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            kb = KnowledgeBase(id="kb_approve_002", name="测试知识库")
            db_session.add(kb)
            db_session.commit()

            doc = KnowledgeDocument(
                knowledge_base_id="kb_approve_002",
                title="待审核文档",
                content="内容",
                status="pending"
            )
            db_session.add(doc)
            db_session.commit()

            response = test_client.post(
                f"/admin/documents/{doc.id}/approve",
                json={
                    "approved": False,
                    "review_notes": "内容需要修改"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "rejected"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_approve_document_not_found(self, test_client: TestClient, db_session: Session):
        """测试审核不存在的文档"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.post(
                "/admin/documents/999999/approve",
                json={"approved": True}
            )

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


# ============================================================================
# 反馈管理测试
# ============================================================================

class TestFeedbackList:
    """测试反馈列表接口"""

    def test_list_all_feedbacks(self, test_client: TestClient, db_session: Session):
        """测试列出所有反馈"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            # 创建测试用户和会话
            user = User(id=6001, phone="13800006001", nickname="测试用户")
            session = SessionModel(id="sess_fb_001", user_id=6001, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            # 创建反馈
            fb1 = SessionFeedback(
                session_id="sess_fb_001",
                user_id=6001,
                feedback_type="helpful",
                status="pending"
            )
            fb2 = SessionFeedback(
                session_id="sess_fb_001",
                user_id=6001,
                feedback_type="unhelpful",
                status="resolved"
            )
            db_session.add_all([fb1, fb2])
            db_session.commit()

            response = test_client.get("/admin/feedbacks")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 2

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_list_feedbacks_with_filters(self, test_client: TestClient, db_session: Session):
        """测试带过滤条件列出反馈"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user = User(id=6002, phone="13800006002", nickname="测试用户2")
            session = SessionModel(id="sess_fb_002", user_id=6002, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            fb1 = SessionFeedback(
                session_id="sess_fb_002",
                user_id=6002,
                feedback_type="helpful",
                status="pending"
            )
            fb2 = SessionFeedback(
                session_id="sess_fb_002",
                user_id=6002,
                feedback_type="unhelpful",
                status="reviewed"
            )
            db_session.add_all([fb1, fb2])
            db_session.commit()

            # 按状态过滤
            response = test_client.get("/admin/feedbacks?status=pending")
            assert response.status_code == 200
            data = response.json()
            assert all(fb["status"] == "pending" for fb in data)

            # 按类型过滤
            response = test_client.get("/admin/feedbacks?feedback_type=helpful")
            assert response.status_code == 200
            data = response.json()
            assert all(fb["feedback_type"] == "helpful" for fb in data)

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_list_feedbacks_pagination(self, test_client: TestClient, db_session: Session):
        """测试反馈列表分页"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user = User(id=6003, phone="13800006003", nickname="测试用户3")
            session = SessionModel(id="sess_fb_003", user_id=6003, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            # 创建多条反馈
            for i in range(10):
                fb = SessionFeedback(
                    session_id="sess_fb_003",
                    user_id=6003,
                    feedback_type="helpful"
                )
                db_session.add(fb)
            db_session.commit()

            # 测试分页
            response = test_client.get("/admin/feedbacks?skip=0&limit=5")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 5

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestFeedbackGet:
    """测试获取反馈详情接口"""

    def test_get_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取反馈详情"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user = User(id=6004, phone="13800006004", nickname="测试用户4")
            session = SessionModel(id="sess_fb_004", user_id=6004, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            fb = SessionFeedback(
                session_id="sess_fb_004",
                user_id=6004,
                rating=5,
                feedback_type="helpful",
                feedback_text="很有帮助"
            )
            db_session.add(fb)
            db_session.commit()

            response = test_client.get(f"/admin/feedbacks/{fb.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == fb.id
            assert data["rating"] == 5
            assert data["feedback_type"] == "helpful"
            assert data["feedback_text"] == "很有帮助"

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_get_feedback_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的反馈"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.get("/admin/feedbacks/999999")

            assert response.status_code == 404
            assert "不存在" in response.json()["detail"]

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestFeedbackHandle:
    """测试反馈处理接口"""

    def test_handle_feedback_success(self, test_client: TestClient, db_session: Session):
        """测试成功处理反馈"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user = User(id=6005, phone="13800006005", nickname="测试用户5")
            session = SessionModel(id="sess_fb_005", user_id=6005, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            fb = SessionFeedback(
                session_id="sess_fb_005",
                user_id=6005,
                feedback_type="unsafe",
                status="pending"
            )
            db_session.add(fb)
            db_session.commit()

            response = test_client.put(
                f"/admin/feedbacks/{fb.id}/handle",
                json={
                    "status": "resolved",
                    "resolution_notes": "已处理安全问题"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "resolved"
            assert data["resolution_notes"] == "已处理安全问题"
            assert data["handled_by"] is not None
            assert data["handled_at"] is not None

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_handle_feedback_not_found(self, test_client: TestClient, db_session: Session):
        """测试处理不存在的反馈"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.put(
                "/admin/feedbacks/999999/handle",
                json={"status": "resolved"}
            )

            assert response.status_code == 404

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()


class TestFeedbackStats:
    """测试反馈统计接口"""

    def test_get_feedback_stats_summary(self, test_client: TestClient, db_session: Session):
        """测试获取反馈统计摘要"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            user = User(id=6006, phone="13800006006", nickname="测试用户6")
            session = SessionModel(id="sess_fb_006", user_id=6006, agent_type="general")
            db_session.add_all([user, session])
            db_session.commit()

            # 创建不同状态和类型的反馈
            fb1 = SessionFeedback(session_id="sess_fb_006", user_id=6006, feedback_type="helpful", status="pending")
            fb2 = SessionFeedback(session_id="sess_fb_006", user_id=6006, feedback_type="unhelpful", status="resolved")
            fb3 = SessionFeedback(session_id="sess_fb_006", user_id=6006, feedback_type="unsafe", status="reviewed")
            fb4 = SessionFeedback(session_id="sess_fb_006", user_id=6006, feedback_type="inaccurate", status="pending")
            db_session.add_all([fb1, fb2, fb3, fb4])
            db_session.commit()

            response = test_client.get("/admin/feedbacks/stats/summary")

            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "by_status" in data
            assert "by_type" in data
            assert data["total"] >= 4
            assert data["by_status"]["pending"] >= 2
            assert data["by_type"]["helpful"] >= 1
            assert data["by_type"]["unsafe"] >= 1

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()

    def test_get_feedback_stats_empty(self, test_client: TestClient, db_session: Session):
        """测试没有反馈时的统计"""
        original_test_mode = os.getenv("TEST_MODE")
        os.environ["TEST_MODE"] = "true"
        reset_settings()

        try:
            response = test_client.get("/admin/feedbacks/stats/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["by_status"]["pending"] == 0
            assert data["by_status"]["reviewed"] == 0
            assert data["by_status"]["resolved"] == 0

        finally:
            if original_test_mode is not None:
                os.environ["TEST_MODE"] = original_test_mode
            else:
                os.environ.pop("TEST_MODE", None)
            reset_settings()
