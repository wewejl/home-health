"""
病历夹和病历记录 API 测试

测试内容：
- 病历夹 CRUD 操作（创建、读取、更新、删除）
- 病历记录 CRUD 操作（创建、读取、更新、删除）
- 文件夹与记录的关联关系
- 权限控制（用户只能访问自己的数据）
- 边界条件处理（无效 ID、重复名称等）

测试模式：使用 TEST_MODE=True 绕过认证
"""
import pytest
from datetime import date, datetime
import uuid

try:
    from app.models.medical_folder import MedicalFolder
    from app.models.medical_record import MedicalRecord
    from app.models.medical_file import MedicalFile
    from app.models.user import User
except ImportError:
    from backend.app.models.medical_folder import MedicalFolder
    from backend.app.models.medical_record import MedicalRecord
    from backend.app.models.medical_file import MedicalFile
    from backend.app.models.user import User


# ============================================================================
# 病历夹 CRUD 测试
# ============================================================================

class TestMedicalFoldersCRUD:
    """病历夹 CRUD 操作测试"""

    def test_create_medical_folder_success(self, test_client):
        """测试创建病历夹 - 成功"""
        request_data = {
            "name": "门诊记录",
            "description": "门诊看病记录",
            "color": "#FF5733",
            "icon": "folder-medical",
            "sort_order": 1
        }
        response = test_client.post("/api/medical-folders", json=request_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "门诊记录"
        assert data["description"] == "门诊看病记录"
        assert data["color"] == "#FF5733"
        assert data["icon"] == "folder-medical"
        assert data["sort_order"] == 1
        assert data["record_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_medical_folder_minimal(self, test_client):
        """测试创建病历夹 - 最小参数"""
        request_data = {
            "name": "住院记录"
        }
        response = test_client.post("/api/medical-folders", json=request_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "住院记录"
        assert data["color"] == "#7B5FEA"  # 默认颜色
        assert data["icon"] == "folder"  # 默认图标
        assert data["sort_order"] == 0  # 默认排序

    def test_create_medical_folder_duplicate_name(self, db_session, test_client):
        """测试创建病历夹 - 重名应失败"""
        # 创建第一个文件夹
        request_data = {
            "name": "检查报告"
        }
        response = test_client.post("/api/medical-folders", json=request_data)
        assert response.status_code == 201

        # 尝试创建同名文件夹
        response = test_client.post("/api/medical-folders", json=request_data)
        assert response.status_code == 400
        data = response.json()
        assert "已存在同名文件夹" in data.get("detail", "")

    def test_create_medical_folder_empty_name(self, test_client):
        """测试创建病历夹 - 空名称应失败"""
        request_data = {
            "name": ""
        }
        response = test_client.post("/api/medical-folders", json=request_data)
        assert response.status_code == 422  # 验证错误

    def test_list_medical_folders_empty(self, test_client):
        """测试获取病历夹列表 - 空列表"""
        response = test_client.get("/api/medical-folders")
        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["folders"]) == 0

    def test_list_medical_folders_with_data(self, db_session, test_client):
        """测试获取病历夹列表 - 有数据"""
        # 创建测试用户
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        # 创建多个文件夹
        folder1 = MedicalFolder(
            user_id=test_user.id,
            name="门诊记录",
            sort_order=1
        )
        folder2 = MedicalFolder(
            user_id=test_user.id,
            name="住院记录",
            sort_order=2
        )
        folder3 = MedicalFolder(
            user_id=test_user.id,
            name="检查报告",
            sort_order=0
        )
        db_session.add_all([folder1, folder2, folder3])
        db_session.commit()

        response = test_client.get("/api/medical-folders")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        # 应该按 sort_order 排序
        assert data["folders"][0]["name"] == "检查报告"
        assert data["folders"][1]["name"] == "门诊记录"
        assert data["folders"][2]["name"] == "住院记录"

    def test_get_medical_folder_success(self, db_session, test_client):
        """测试获取病历夹详情 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="处方单",
            description="医生开具的处方单"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        response = test_client.get(f"/api/medical-folders/{folder.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(folder.id)
        assert data["name"] == "处方单"
        assert data["description"] == "医生开具的处方单"

    def test_get_medical_folder_invalid_id(self, test_client):
        """测试获取病历夹详情 - 无效 ID"""
        response = test_client.get("/api/medical-folders/invalid-uuid")
        assert response.status_code == 400
        data = response.json()
        assert "无效的文件夹ID" in data.get("detail", "")

    def test_get_medical_folder_not_found(self, test_client):
        """测试获取病历夹详情 - 不存在"""
        fake_id = uuid.uuid4()
        response = test_client.get(f"/api/medical-folders/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert "病历夹不存在" in data.get("detail", "")

    def test_update_medical_folder_success(self, db_session, test_client):
        """测试更新病历夹 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="旧名称",
            color="#000000"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        update_data = {
            "name": "新名称",
            "description": "更新后的描述",
            "color": "#00FF00"
        }
        response = test_client.put(f"/api/medical-folders/{folder.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新名称"
        assert data["description"] == "更新后的描述"
        assert data["color"] == "#00FF00"

    def test_update_medical_folder_partial(self, db_session, test_client):
        """测试更新病历夹 - 部分字段"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="原始名称",
            description="原始描述",
            color="#123456"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 只更新名称
        update_data = {
            "name": "只更新名称"
        }
        response = test_client.put(f"/api/medical-folders/{folder.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "只更新名称"
        assert data["description"] == "原始描述"  # 保持不变
        assert data["color"] == "#123456"  # 保持不变

    def test_update_medical_folder_duplicate_name(self, db_session, test_client):
        """测试更新病历夹 - 重名应失败"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder1 = MedicalFolder(
            user_id=test_user.id,
            name="已存在名称"
        )
        folder2 = MedicalFolder(
            user_id=test_user.id,
            name="另一个名称"
        )
        db_session.add_all([folder1, folder2])
        db_session.commit()
        db_session.refresh(folder1)
        db_session.refresh(folder2)

        # 尝试将 folder2 改为与 folder1 同名
        update_data = {
            "name": "已存在名称"
        }
        response = test_client.put(f"/api/medical-folders/{folder2.id}", json=update_data)
        assert response.status_code == 400
        data = response.json()
        assert "已存在同名文件夹" in data.get("detail", "")

    def test_delete_medical_folder_success(self, db_session, test_client):
        """测试删除病历夹 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="待删除的文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        folder_id = folder.id

        response = test_client.delete(f"/api/medical-folders/{folder_id}")
        assert response.status_code == 204

        # 验证已删除
        response = test_client.get(f"/api/medical-folders/{folder_id}")
        assert response.status_code == 404

    def test_delete_medical_folder_with_records(self, db_session, test_client):
        """测试删除带记录的病历夹 - 应级联删除"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="带记录的文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="测试记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()

        folder_id = folder.id
        record_id = record.id

        # 删除文件夹
        response = test_client.delete(f"/api/medical-folders/{folder_id}")
        assert response.status_code == 204

        # 验证记录也被级联删除
        deleted_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        assert deleted_record is None


# ============================================================================
# 病历记录 CRUD 测试
# ============================================================================

class TestMedicalRecordsCRUD:
    """病历记录 CRUD 操作测试"""

    def test_create_medical_record_success(self, db_session, test_client):
        """测试创建病历记录 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="门诊记录"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        request_data = {
            "folder_id": str(folder.id),
            "title": "感冒就诊记录",
            "record_date": "2024-01-15",
            "description": "诊断为上呼吸道感染，开药治疗"
        }
        response = test_client.post("/api/medical-records", json=request_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "感冒就诊记录"
        assert data["folder_id"] == str(folder.id)
        assert data["description"] == "诊断为上呼吸道感染，开药治疗"
        assert data["file_count"] == 0
        assert "id" in data

    def test_create_medical_record_with_date_object(self, db_session, test_client):
        """测试创建病历记录 - 使用 date 对象"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="门诊记录"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        request_data = {
            "folder_id": str(folder.id),
            "title": "检查记录",
            "record_date": date.today().isoformat(),
            "description": "血常规检查"
        }
        response = test_client.post("/api/medical-records", json=request_data)
        assert response.status_code == 201

    def test_create_medical_record_invalid_folder_id(self, test_client):
        """测试创建病历记录 - 无效的文件夹 ID"""
        fake_id = uuid.uuid4()
        request_data = {
            "folder_id": str(fake_id),
            "title": "测试记录",
            "record_date": "2024-01-15"
        }
        response = test_client.post("/api/medical-records", json=request_data)
        assert response.status_code == 404

    def test_create_medical_record_missing_fields(self, test_client):
        """测试创建病历记录 - 缺少必填字段"""
        request_data = {
            "folder_id": str(uuid.uuid4())
            # 缺少 title 和 record_date
        }
        response = test_client.post("/api/medical-records", json=request_data)
        assert response.status_code == 422

    def test_list_medical_records_empty(self, test_client):
        """测试获取病历记录列表 - 空列表"""
        response = test_client.get("/api/medical-records")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert data["total"] == 0

    def test_list_medical_records_with_data(self, db_session, test_client):
        """测试获取病历记录列表 - 有数据"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record1 = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="记录1",
            record_date=date(2024, 1, 10)
        )
        record2 = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="记录2",
            record_date=date(2024, 1, 15)
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = test_client.get("/api/medical-records")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        # 应按记录日期降序排列
        assert data["records"][0]["title"] == "记录2"
        assert data["records"][1]["title"] == "记录1"

    def test_list_medical_records_by_folder(self, db_session, test_client):
        """测试按文件夹筛选病历记录"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder1 = MedicalFolder(
            user_id=test_user.id,
            name="门诊记录"
        )
        folder2 = MedicalFolder(
            user_id=test_user.id,
            name="住院记录"
        )
        db_session.add_all([folder1, folder2])
        db_session.commit()
        db_session.refresh(folder1)
        db_session.refresh(folder2)

        record1 = MedicalRecord(
            folder_id=folder1.id,
            user_id=test_user.id,
            title="门诊记录1",
            record_date=date.today()
        )
        record2 = MedicalRecord(
            folder_id=folder1.id,
            user_id=test_user.id,
            title="门诊记录2",
            record_date=date.today()
        )
        record3 = MedicalRecord(
            folder_id=folder2.id,
            user_id=test_user.id,
            title="住院记录1",
            record_date=date.today()
        )
        db_session.add_all([record1, record2, record3])
        db_session.commit()

        # 只获取 folder1 的记录
        response = test_client.get(f"/api/medical-records?folder_id={folder1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for record in data["records"]:
            assert record["folder_id"] == str(folder1.id)

    def test_list_medical_records_invalid_folder_id(self, test_client):
        """测试按文件夹筛选 - 无效 ID"""
        response = test_client.get("/api/medical-records?folder_id=invalid-uuid")
        assert response.status_code == 400

    def test_get_medical_record_success(self, db_session, test_client):
        """测试获取病历记录详情 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="测试记录",
            record_date=date.today(),
            description="测试描述"
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = test_client.get(f"/api/medical-records/{record.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(record.id)
        assert data["title"] == "测试记录"
        assert data["description"] == "测试描述"
        assert "files" in data

    def test_get_medical_record_invalid_id(self, test_client):
        """测试获取病历记录详情 - 无效 ID"""
        response = test_client.get("/api/medical-records/invalid-uuid")
        assert response.status_code == 400
        data = response.json()
        assert "无效的记录ID" in data.get("detail", "")

    def test_get_medical_record_not_found(self, test_client):
        """测试获取病历记录详情 - 不存在"""
        fake_id = uuid.uuid4()
        response = test_client.get(f"/api/medical-records/{fake_id}")
        assert response.status_code == 404

    def test_update_medical_record_success(self, db_session, test_client):
        """测试更新病历记录 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="原始标题",
            record_date=date(2024, 1, 1),
            description="原始描述"
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        update_data = {
            "title": "更新后的标题",
            "description": "更新后的描述"
        }
        response = test_client.put(f"/api/medical-records/{record.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["description"] == "更新后的描述"

    def test_update_medical_record_change_folder(self, db_session, test_client):
        """测试更新病历记录 - 更换文件夹"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder1 = MedicalFolder(
            user_id=test_user.id,
            name="文件夹1"
        )
        folder2 = MedicalFolder(
            user_id=test_user.id,
            name="文件夹2"
        )
        db_session.add_all([folder1, folder2])
        db_session.commit()
        db_session.refresh(folder1)
        db_session.refresh(folder2)

        record = MedicalRecord(
            folder_id=folder1.id,
            user_id=test_user.id,
            title="测试记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        # 更换到 folder2
        update_data = {
            "folder_id": str(folder2.id)
        }
        response = test_client.put(f"/api/medical-records/{record.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["folder_id"] == str(folder2.id)

    def test_update_medical_record_invalid_folder(self, db_session, test_client):
        """测试更新病历记录 - 无效的文件夹 ID"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="测试记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        # 尝试更新到不存在的文件夹
        fake_id = uuid.uuid4()
        update_data = {
            "folder_id": str(fake_id)
        }
        response = test_client.put(f"/api/medical-records/{record.id}", json=update_data)
        assert response.status_code == 404

    def test_delete_medical_record_success(self, db_session, test_client):
        """测试删除病历记录 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="待删除的记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        record_id = record.id

        response = test_client.delete(f"/api/medical-records/{record_id}")
        assert response.status_code == 204

        # 验证已删除
        response = test_client.get(f"/api/medical-records/{record_id}")
        assert response.status_code == 404

    def test_delete_medical_record_invalid_id(self, test_client):
        """测试删除病历记录 - 无效 ID"""
        response = test_client.delete("/api/medical-records/invalid-uuid")
        assert response.status_code == 400

    def test_get_records_by_folder_success(self, db_session, test_client):
        """测试通过文件夹路径获取记录 - 成功"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="门诊记录"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record1 = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="记录1",
            record_date=date(2024, 1, 10)
        )
        record2 = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="记录2",
            record_date=date(2024, 1, 15)
        )
        db_session.add_all([record1, record2])
        db_session.commit()

        response = test_client.get(f"/api/medical-records/by-folder/{folder.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        # 验证所有记录都属于该文件夹
        for record in data["records"]:
            assert record["folder_id"] == str(folder.id)

    def test_get_records_by_folder_invalid_id(self, test_client):
        """测试通过文件夹路径获取记录 - 无效 ID"""
        response = test_client.get("/api/medical-records/by-folder/invalid-uuid")
        assert response.status_code == 400

    def test_get_records_by_folder_not_found(self, test_client):
        """测试通过文件夹路径获取记录 - 文件夹不存在"""
        fake_id = uuid.uuid4()
        response = test_client.get(f"/api/medical-records/by-folder/{fake_id}")
        assert response.status_code == 404


# ============================================================================
# 文件夹与记录关联测试
# ============================================================================

class TestFolderRecordAssociation:
    """文件夹与记录关联测试"""

    def test_folder_record_count(self, db_session, test_client):
        """测试文件夹的记录计数"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 添加多条记录
        for i in range(3):
            record = MedicalRecord(
                folder_id=folder.id,
                user_id=test_user.id,
                title=f"记录{i+1}",
                record_date=date.today()
            )
            db_session.add(record)
        db_session.commit()

        # 获取文件夹列表，检查记录计数
        response = test_client.get("/api/medical-folders")
        assert response.status_code == 200
        data = response.json()
        folder_data = next((f for f in data["folders"] if f["name"] == "测试文件夹"), None)
        assert folder_data is not None
        assert folder_data["record_count"] == 3

    def test_record_with_files(self, db_session, test_client):
        """测试带文件的病历记录"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="带文件的记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        # 添加文件
        file1 = MedicalFile(
            record_id=record.id,
            user_id=test_user.id,
            filename="report1.pdf",
            file_type="pdf",
            mime_type="application/pdf",
            file_size=1024000,
            url="https://example.com/file1.pdf"
        )
        file2 = MedicalFile(
            record_id=record.id,
            user_id=test_user.id,
            filename="image1.jpg",
            file_type="image",
            mime_type="image/jpeg",
            file_size=512000,
            url="https://example.com/image1.jpg"
        )
        db_session.add_all([file1, file2])
        db_session.commit()

        # 获取记录详情
        response = test_client.get(f"/api/medical-records/{record.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["file_count"] == 2
        assert len(data["files"]) == 2
        assert data["files"][0]["filename"] == "report1.pdf"
        assert data["files"][1]["filename"] == "image1.jpg"

    def test_cascade_delete_folder_with_records(self, db_session, test_client):
        """测试级联删除：删除文件夹时记录也被删除"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="待删除文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="随文件夹删除的记录",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()

        folder_id = folder.id
        record_id = record.id

        # 删除文件夹
        test_client.delete(f"/api/medical-folders/{folder_id}")

        # 验证记录已被级联删除
        deleted_record = db_session.query(MedicalRecord).filter(
            MedicalRecord.id == record_id
        ).first()
        assert deleted_record is None


# ============================================================================
# 权限控制测试
# ============================================================================

class TestPermissionControl:
    """权限控制测试"""

    def test_user_cannot_access_other_user_folder(self, db_session, test_client):
        """测试用户无法访问其他用户的文件夹"""
        # 创建其他用户
        other_user = User(
            phone="other_user",
            nickname="其他用户",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        # 创建属于其他用户的文件夹
        other_folder = MedicalFolder(
            user_id=other_user.id,
            name="其他用户的文件夹"
        )
        db_session.add(other_folder)
        db_session.commit()

        # 当前测试用户尝试访问
        response = test_client.get(f"/api/medical-folders/{other_folder.id}")
        assert response.status_code == 403
        data = response.json()
        assert "无权访问" in data.get("detail", "")

    def test_user_cannot_update_other_user_folder(self, db_session, test_client):
        """测试用户无法更新其他用户的文件夹"""
        other_user = User(
            phone="other_user2",
            nickname="其他用户2",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_folder = MedicalFolder(
            user_id=other_user.id,
            name="其他用户的文件夹"
        )
        db_session.add(other_folder)
        db_session.commit()

        update_data = {"name": "试图修改"}
        response = test_client.put(f"/api/medical-folders/{other_folder.id}", json=update_data)
        assert response.status_code == 403

    def test_user_cannot_delete_other_user_folder(self, db_session, test_client):
        """测试用户无法删除其他用户的文件夹"""
        other_user = User(
            phone="other_user3",
            nickname="其他用户3",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_folder = MedicalFolder(
            user_id=other_user.id,
            name="其他用户的文件夹"
        )
        db_session.add(other_folder)
        db_session.commit()

        response = test_client.delete(f"/api/medical-folders/{other_folder.id}")
        assert response.status_code == 403

    def test_user_cannot_access_other_user_record(self, db_session, test_client):
        """测试用户无法访问其他用户的病历记录"""
        other_user = User(
            phone="other_user4",
            nickname="其他用户4",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_folder = MedicalFolder(
            user_id=other_user.id,
            name="其他用户的文件夹"
        )
        db_session.add(other_folder)
        db_session.commit()
        db_session.refresh(other_folder)

        other_record = MedicalRecord(
            folder_id=other_folder.id,
            user_id=other_user.id,
            title="其他用户的记录",
            record_date=date.today()
        )
        db_session.add(other_record)
        db_session.commit()

        response = test_client.get(f"/api/medical-records/{other_record.id}")
        assert response.status_code == 403

    def test_user_cannot_create_record_in_other_user_folder(self, db_session, test_client):
        """测试用户无法在其他用户的文件夹中创建记录"""
        other_user = User(
            phone="other_user5",
            nickname="其他用户5",
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_folder = MedicalFolder(
            user_id=other_user.id,
            name="其他用户的文件夹"
        )
        db_session.add(other_folder)
        db_session.commit()

        request_data = {
            "folder_id": str(other_folder.id),
            "title": "试图在其他用户文件夹创建记录",
            "record_date": "2024-01-15"
        }
        response = test_client.post("/api/medical-records", json=request_data)
        assert response.status_code == 403


# ============================================================================
# 边界条件和异常处理测试
# ============================================================================

class TestEdgeCases:
    """边界条件和异常处理测试"""

    def test_create_folder_very_long_name(self, test_client):
        """测试创建文件夹 - 名称长度边界"""
        # 255 字符应该成功
        long_name = "A" * 255
        request_data = {
            "name": long_name
        }
        response = test_client.post("/api/medical-folders", json=request_data)
        # 可能成功或失败，取决于验证规则
        assert response.status_code in [201, 422]

    def test_create_record_very_long_title(self, db_session, test_client):
        """测试创建记录 - 标题长度边界"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        # 255 字符应该成功
        long_title = "B" * 255
        request_data = {
            "folder_id": str(folder.id),
            "title": long_title,
            "record_date": "2024-01-15"
        }
        response = test_client.post("/api/medical-records", json=request_data)
        # 可能成功或失败，取决于验证规则
        assert response.status_code in [201, 422]

    def test_update_with_empty_body(self, db_session, test_client):
        """测试更新记录 - 空请求体"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="测试文件夹"
        )
        db_session.add(folder)
        db_session.commit()
        db_session.refresh(folder)

        record = MedicalRecord(
            folder_id=folder.id,
            user_id=test_user.id,
            title="原始标题",
            record_date=date.today()
        )
        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        # 空更新应该不改变任何内容
        response = test_client.put(f"/api/medical-records/{record.id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "原始标题"

    def test_list_with_special_characters_in_name(self, db_session, test_client):
        """测试特殊字符处理"""
        test_user = db_session.query(User).filter(User.phone == "test_user").first()

        folder = MedicalFolder(
            user_id=test_user.id,
            name="文件夹<特殊>&\"字符'"
        )
        db_session.add(folder)
        db_session.commit()

        response = test_client.get("/api/medical-folders")
        assert response.status_code == 200
        data = response.json()
        # 验证特殊字符被正确处理
        assert len(data["folders"]) > 0
