"""
医疗文件 API 测试

测试 /medical-files 端点：
- POST /medical-files/upload - 上传文件
- GET /medical-files/{file_id} - 获取文件信息
- GET /medical-files/record/{record_id} - 获取记录的所有文件
- PUT /medical-files/{file_id} - 重命名文件
- DELETE /medical-files/{file_id} - 删除文件
"""
import pytest
import uuid
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.user import User
    from app.models.medical_file import MedicalFile
    from app.models.medical_record import MedicalRecord
    from app.models.medical_folder import MedicalFolder
    from app.services.auth_service import AuthService
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.models.medical_file import MedicalFile
    from backend.app.models.medical_record import MedicalRecord
    from backend.app.models.medical_folder import MedicalFolder
    from backend.app.services.auth_service import AuthService
    from backend.app.main import app


# ============================================================================
# 医疗文件 API 测试
# ============================================================================

class TestUploadFileAPI:
    """测试文件上传 API (POST /medical-files/upload)"""

    def test_upload_file_success(self, test_client: TestClient, db_session: Session):
        """测试成功上传文件"""
        user = User(
            phone="13800555",
            nickname="文件上传用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建病历记录
        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录"
        )
        db_session.add(record)
        db_session.commit()

        # 登录获取 token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800555"
        })
        token = login_response.json()["access_token"]

        # 创建测试文件
        file_content = b"test file content"
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }
        data = {
            "record_id": str(record.id)
        }

        response = test_client.post(
            "/medical-files/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 201
        result = response.json()
        assert result["file"]["filename"] == "test.txt"
        assert result["message"] == "文件上传成功"

    def test_upload_file_invalid_record(self, test_client: TestClient, db_session: Session):
        """测试上传到不存在的记录"""
        user = User(
            phone="13800556",
            nickname="错误记录用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800556"
        })
        token = login_response.json()["access_token"]

        fake_record_id = str(uuid.uuid4())
        files = {
            "file": ("test.txt", io.BytesIO(b"content"), "text/plain")
        }
        data = {"record_id": fake_record_id}

        response = test_client.post(
            "/medical-files/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 404

    def test_upload_file_unauthorized(self, test_client: TestClient):
        """测试未授权上传"""
        response = test_client.post("/medical-files/upload")

        assert response.status_code == 401

    def test_upload_file_too_large(self, test_client: TestClient, db_session: Session):
        """测试上传过大文件"""
        user = User(
            phone="13800557",
            nickname="大文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹2"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录2"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800557"
        })
        token = login_response.json()["access_token"]

        # 创建超过限制的文件 (模拟 51MB)
        large_content = b"x" * (51 * 1024 * 1024)
        files = {
            "file": ("large.txt", io.BytesIO(large_content), "text/plain")
        }
        data = {"record_id": str(record.id)}

        response = test_client.post(
            "/medical-files/upload",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )

        assert response.status_code == 413


class TestGetFileInfoAPI:
    """测试获取文件信息 API (GET /medical-files/{file_id})"""

    def test_get_file_info_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取文件信息"""
        user = User(
            phone="13800558",
            nickname="获取文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹3"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录3"
        )
        db_session.add(record)
        db_session.commit()

        file = MedicalFile(
            id=uuid.uuid4(),
            record_id=record.id,
            user_id=user.id,
            filename="test_file.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_size=1024,
            url="/static/test.jpg"
        )
        db_session.add(file)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800558"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-files/{file.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test_file.jpg"

    def test_get_file_info_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的文件"""
        user = User(
            phone="13800559",
            nickname="不存在文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800559"
        })
        token = login_response.json()["access_token"]

        fake_file_id = str(uuid.uuid4())
        response = test_client.get(
            f"/medical-files/{fake_file_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_get_file_info_invalid_id(self, test_client: TestClient, db_session: Session):
        """测试无效的文件ID"""
        user = User(
            phone="13800560",
            nickname="无效ID用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800560"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/medical-files/invalid-uuid",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400


class TestGetRecordFilesAPI:
    """测试获取记录文件列表 API (GET /medical-files/record/{record_id})"""

    def test_get_record_files_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取记录的所有文件"""
        user = User(
            phone="13800561",
            nickname="记录文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹4"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录4"
        )
        db_session.add(record)
        db_session.commit()

        # 创建多个文件
        for i in range(3):
            file = MedicalFile(
                id=uuid.uuid4(),
                record_id=record.id,
                user_id=user.id,
                filename=f"file{i}.jpg",
                file_type="image",
                mime_type="image/jpeg",
                file_size=1024,
                url=f"/static/file{i}.jpg"
            )
            db_session.add(file)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800561"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-files/record/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["files"]) == 3

    def test_get_record_files_empty(self, test_client: TestClient, db_session: Session):
        """测试获取空文件列表"""
        user = User(
            phone="13800562",
            nickname="空文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹5"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录5"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800562"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-files/record/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["files"]) == 0


class TestRenameFileAPI:
    """测试重命名文件 API (PUT /medical-files/{file_id})"""

    def test_rename_file_success(self, test_client: TestClient, db_session: Session):
        """测试成功重命名文件"""
        user = User(
            phone="13800563",
            nickname="重命名用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹6"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录6"
        )
        db_session.add(record)
        db_session.commit()

        file = MedicalFile(
            id=uuid.uuid4(),
            record_id=record.id,
            user_id=user.id,
            filename="original_name.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_size=1024,
            url="/static/original.jpg"
        )
        db_session.add(file)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800563"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/medical-files/{file.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"filename": "new_name.jpg"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "new_name.jpg"


class TestDeleteFileAPI:
    """测试删除文件 API (DELETE /medical-files/{file_id})"""

    def test_delete_file_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除文件"""
        user = User(
            phone="13800564",
            nickname="删除文件用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="测试文件夹7"
        )
        db_session.add(folder)
        db_session.commit()

        record = MedicalRecord(
            id=str(uuid.uuid4()),
            user_id=user.id,
            folder_id=folder.id,
            title="测试记录7"
        )
        db_session.add(record)
        db_session.commit()

        file = MedicalFile(
            id=uuid.uuid4(),
            record_id=record.id,
            user_id=user.id,
            filename="to_delete.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_size=1024,
            url="/static/to_delete.jpg"
        )
        db_session.add(file)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800564"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/medical-files/{file.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

    def test_delete_file_not_found(self, test_client: TestClient, db_session: Session):
        """测试删除不存在的文件"""
        user = User(
            phone="13800565",
            nickname="删除不存在用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800565"
        })
        token = login_response.json()["access_token"]

        fake_file_id = str(uuid.uuid4())
        response = test_client.delete(
            f"/medical-files/{fake_file_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404

    def test_delete_file_unauthorized(self, test_client: TestClient, db_session: Session):
        """测试未授权删除"""
        response = test_client.delete("/medical-files/some-file-id")

        assert response.status_code == 401
