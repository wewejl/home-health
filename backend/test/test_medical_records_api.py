"""
医疗记录 API 测试

测试 /medical-records 端点：
- POST /medical-records - 创建病历记录
- GET /medical-records - 获取病历记录列表
- GET /medical-records/{record_id} - 获取病历记录详情
- PUT /medical-records/{record_id} - 更新病历记录
- DELETE /medical-records/{record_id} - 删除病历记录
- GET /medical-records/by-folder/{folder_id} - 获取指定文件夹下的记录
"""
import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app.models.user import User
    from app.models.medical_record import MedicalRecord
    from app.models.medical_folder import MedicalFolder
    from app.dependencies import get_current_user
    from app.main import app
except ImportError:
    from backend.app.database import get_db
    from backend.app.models.user import User
    from backend.app.models.medical_record import MedicalRecord
    from backend.app.models.medical_folder import MedicalFolder
    from backend.app.dependencies import get_current_user
    from backend.app.main import app


# ============================================================================
# 医疗记录 API 测试
# ============================================================================

class TestCreateMedicalRecordAPI:
    """测试创建病历记录 API (POST /medical-records)"""

    def test_create_medical_record_success(self, test_client: TestClient, db_session: Session):
        """测试成功创建病历记录"""
        # 创建测试用户
        user = User(
            phone="13800138000",
            nickname="测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建文件夹
        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 登录获取 token
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138000"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/medical-records",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "folder_id": str(folder.id),
                "title": "测试病历",
                "record_date": "2024-01-15",
                "description": "测试描述"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试病历"
        assert data["folder_id"] == str(folder.id)

    def test_create_medical_record_invalid_folder_id(self, test_client: TestClient, db_session: Session):
        """测试创建病历记录时文件夹ID无效"""
        user = User(
            phone="13800138001",
            nickname="测试用户2",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138001"
        })
        token = login_response.json()["access_token"]

        # 使用无效的 UUID
        response = test_client.post(
            "/medical-records",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "folder_id": "invalid-uuid",
                "title": "测试病历",
                "record_date": "2024-01-15"
            }
        )

        assert response.status_code == 400

    def test_create_medical_record_unauthorized_folder(self, test_client: TestClient, db_session: Session):
        """测试创建病历记录时无权限访问文件夹"""
        user1 = User(
            phone="13800138002",
            nickname="用户1",
            is_active=True
        )
        user2 = User(
            phone="13800138003",
            nickname="用户2",
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # 用户1创建文件夹
        folder = MedicalFolder(
            user_id=user1.id,
            name="用户1的文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 用户2尝试在该文件夹下创建记录
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138003"
        })
        token = login_response.json()["access_token"]

        response = test_client.post(
            "/medical-records",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "folder_id": str(folder.id),
                "title": "未授权的病历",
                "record_date": "2024-01-15"
            }
        )

        assert response.status_code == 403


class TestListMedicalRecordsAPI:
    """测试获取病历记录列表 API (GET /medical-records)"""

    def test_list_medical_records_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取病历记录列表"""
        user = User(
            phone="13800138004",
            nickname="列表测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建一些病历记录
        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record1 = MedicalRecord(
            folder_id=folder.id,
            user_id=user.id,
            title="病历1",
            record_date="2024-01-15"
        )
        record2 = MedicalRecord(
            folder_id=folder.id,
            user_id=user.id,
            title="病历2",
            record_date="2024-01-16"
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138004"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/medical-records",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert isinstance(data["records"], list)

    def test_list_medical_records_filter_by_folder(self, test_client: TestClient, db_session: Session):
        """测试按文件夹筛选病历记录"""
        user = User(
            phone="13800138005",
            nickname="筛选用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 创建两个文件夹
        folder1 = MedicalFolder(
            user_id=user.id,
            name="文件夹1",
            is_active=True
        )
        folder2 = MedicalFolder(
            user_id=user.id,
            name="文件夹2",
            is_active=True
        )
        db_session.add_all([folder1, folder2])
        db_session.commit()
        db_session.refresh(folder1)

        # 为文件夹1创建记录
        record = MedicalRecord(
            folder_id=folder1.id,
            user_id=user.id,
            title="文件夹1的记录",
            record_date="2024-01-15"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138005"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-records?folder_id={folder1.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestGetMedicalRecordAPI:
    """测试获取病历记录详情 API (GET /medical-records/{record_id})"""

    def test_get_medical_record_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取病历记录详情"""
        user = User(
            phone="13800138006",
            nickname="详情测试用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=user.id,
            title="测试病历详情",
            record_date="2024-01-15",
            description="详细描述内容"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138006"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "测试病历详情"
        assert data["description"] == "详细描述内容"

    def test_get_medical_record_not_found(self, test_client: TestClient, db_session: Session):
        """测试获取不存在的病历记录"""
        user = User(
            phone="13800138007",
            nickname="不存在用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138007"
        })
        token = login_response.json()["access_token"]

        # 使用不存在的记录ID
        fake_uuid = str(uuid.uuid4())
        response = test_client.get(
            f"/medical-records/{fake_uuid}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404
        assert "病历记录不存在" in response.json()["detail"]

    def test_get_medical_record_unauthorized(self, test_client: TestClient, db_session: Session):
        """测试无权限获取病历记录"""
        user1 = User(
            phone="13800138008",
            nickname="用户1",
            is_active=True
        )
        user2 = User(
            phone="13800138009",
            nickname="用户2",
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        folder = MedicalFolder(
            user_id=user1.id,
            name="用户1的文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=user1.id,
            title="用户1的病历",
            record_date="2024-01-15"
        )
        db_session.add(record)
        db_session.commit()

        # 用户2尝试访问用户1的病历
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138009"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "无权" in response.json()["detail"]


class TestUpdateMedicalRecordAPI:
    """测试更新病历记录 API (PUT /medical-records/{record_id})"""

    def test_update_medical_record_success(self, test_client: TestClient, db_session: Session):
        """测试成功更新病历记录"""
        user = User(
            phone="13800138010",
            nickname="更新用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=user.id,
            title="原始标题",
            record_date="2024-01-15"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138010"
        })
        token = login_response.json()["access_token"]

        response = test_client.put(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "更新后的标题",
                "description": "更新后的描述"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["description"] == "更新后的描述"

    def test_update_medical_record_not_found(self, test_client: TestClient, db_session: Session):
        """测试更新不存在的病历记录"""
        user = User(
            phone="13800138011",
            nickname="更新不用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138011"
        })
        token = login_response.json()["access_token"]

        fake_uuid = str(uuid.uuid4())
        response = test_client.put(
            f"/medical-records/{fake_uuid}",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "更新标题"}
        )

        assert response.status_code == 404


class TestDeleteMedicalRecordAPI:
    """测试删除病历记录 API (DELETE /medical-records/{record_id})"""

    def test_delete_medical_record_success(self, test_client: TestClient, db_session: Session):
        """测试成功删除病历记录"""
        user = User(
            phone="13800138012",
            nickname="删除用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=user.id,
            title="待删除的病历",
            record_date="2024-01-15"
        )
        db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138012"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # 验证记录已删除
        deleted_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record.id
        ).first()
        assert deleted_record is None

    def test_delete_medical_record_unauthorized(self, test_client: TestClient, db_session: Session):
        """测试无权限删除病历记录"""
        user1 = User(
            phone="13800138013",
            nickname="删除用户1",
            is_active=True
        )
        user2 = User(
            phone="13800138014",
            nickname="删除用户2",
            is_active=True
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        folder = MedicalFolder(
            user_id=user1.id,
            name="用户1的文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=user1.id,
            title="用户1的病历",
            record_date="2024-01-15"
        )
        db_session.add(record)
        db_session.commit()

        # 用户2尝试删除用户1的病历
        login_response = test_client.post("/auth/login", json={
            "phone": "13800138014"
        })
        token = login_response.json()["access_token"]

        response = test_client.delete(
            f"/medical-records/{record.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403


class TestGetRecordsByFolderAPI:
    """测试获取指定文件夹下的记录 API (GET /medical-records/by-folder/{folder_id})"""

    def test_get_records_by_folder_success(self, test_client: TestClient, db_session: Session):
        """测试成功获取文件夹下的记录"""
        user = User(
            phone="13800138015",
            nickname="文件夹记录用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        folder = MedicalFolder(
            user_id=user.id,
            name="测试文件夹",
            is_active=True
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 创建多个记录
        for i in range(3):
            record = MedicalRecord(
                folder_id=folder.id,
                user_id=user.id,
                title=f"记录{i+1}",
                record_date=f"2024-01-{15+i}"
            )
            db_session.add(record)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138015"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            f"/medical-records/by-folder/{folder.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_get_records_by_folder_invalid_uuid(self, test_client: TestClient, db_session: Session):
        """测试使用无效的文件夹UUID"""
        user = User(
            phone="13800138016",
            nickname="无效UUID用户",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_response = test_client.post("/auth/login", json={
            "phone": "13800138016"
        })
        token = login_response.json()["access_token"]

        response = test_client.get(
            "/medical-records/by-folder/invalid-uuid-format",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
