# 测试覆盖 100% 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 实现项目测试覆盖率从当前 ~5% 提升到 100%，覆盖所有核心业务逻辑

**架构:** 分阶段实现，TDD 驱动，优先覆盖 P0 核心功能，然后扩展到 P1/P2

**技术栈:**
- 后端: pytest + pytest-asyncio + pytest-cov + httpx
- 前端: Vitest + Testing Library + MSW
- iOS: XCTest (已配置)

---

## 第一阶段：后端 P0 测试覆盖 (优先级: 最高)

### Task 1: 用户认证 API 测试

**Files:**
- Create: `backend/test/test_auth_api.py`

**Step 1: Write the failing test**

```python
# backend/test/test_auth_api.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_send_verification_code_success():
    """测试发送验证码成功"""
    response = client.post("/api/auth/send-code", json={"phone": "13800138000"})
    assert response.status_code == 200
    data = response.json()
    assert "expires_in" in data
    assert data["expires_in"] > 0

def test_send_verification_code_invalid_phone():
    """测试发送验证码 - 无效手机号"""
    response = client.post("/api/auth/send-code", json={"phone": "12345"})
    assert response.status_code == 422  # Validation error

def test_login_with_test_mode():
    """测试登录 - 测试模式"""
    response = client.post("/api/auth/login", json={
        "phone": "13800138000",
        "code": "000000"  # 测试模式万能验证码
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["phone"] == "13800138000"

def test_get_current_user():
    """测试获取当前用户信息"""
    # 先登录获取 token
    login_response = client.post("/api/auth/login", json={
        "phone": "13800138000",
        "code": "000000"
    })
    token = login_response.json()["token"]

    # 使用 token 获取用户信息
    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "13800138000"

def test_update_profile():
    """测试更新用户资料"""
    # 先登录
    login_response = client.post("/api/auth/login", json={
        "phone": "13800138000",
        "code": "000000"
    })
    token = login_response.json()["token"]

    # 更新资料
    response = client.put("/api/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "nickname": "测试用户",
            "gender": "male"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nickname"] == "测试用户"
    assert data["gender"] == "male"

def test_check_phone_exists():
    """测试检查手机号状态"""
    response = client.get("/api/auth/check-phone?phone=13800138000")
    assert response.status_code == 200
    data = response.json()
    assert "exists" in data

def test_password_login():
    """测试密码登录"""
    # 首先设置密码
    register_response = client.post("/api/auth/register-password", json={
        "phone": "13900139000",
        "password": "Test123456"
    })
    assert register_response.status_code == 200

    # 使用密码登录
    login_response = client.post("/api/auth/login-password", json={
        "phone": "13900139000",
        "password": "Test123456"
    })
    assert login_response.status_code == 200
    data = login_response.json()
    assert "token" in data

def test_refresh_token():
    """测试刷新 Token"""
    # 先登录
    login_response = client.post("/api/auth/login", json={
        "phone": "13800138000",
        "code": "000000"
    })
    refresh_token = login_response.json()["refresh_token"]

    # 刷新 token
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "refresh_token" in data
```

**Step 2: Run test to verify it fails**

```bash
docker exec -it home-health-backend pytest backend/test/test_auth_api.py -v
```

Expected: 部分测试通过（已有用户），部分失败（需要数据库状态）

**Step 3: Configure test fixtures**

```python
# backend/test/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base, get_db
from backend.app.main import app
from fastapi.testclient import TestClient

# 测试数据库
TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@postgres:5432/home_health_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

**Step 4: Run tests and verify they pass**

```bash
docker exec -it home-health-backend pytest backend/test/test_auth_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/test/test_auth_api.py backend/test/conftest.py
git commit -m "test(auth): add authentication API tests"
```

---

### Task 2: 医生工作台 API 测试

**Files:**
- Create: `backend/test/test_doctor_workstation_api.py`

**Step 1: Write the failing test**

```python
# backend/test/test_doctor_workstation_api.py
import pytest
from datetime import date, datetime

def test_get_doctor_info(test_client):
    """测试获取医生信息"""
    # 使用测试模式 token
    response = test_client.get("/api/doctor/me", headers={
        "Authorization": "Bearer test_1"  # test_N 格式的测试令牌
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "managed_doctors" in data

def test_get_patient_stats(test_client):
    """测试获取患者统计"""
    response = test_client.get("/api/doctor/patient-stats", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "active" in data
    assert "new_today" in data
    assert "low_compliance" in data

def test_get_patients(test_client):
    """测试获取患者列表"""
    response = test_client.get("/api/doctor/patients", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_patients_with_search(test_client):
    """测试搜索患者"""
    response = test_client.get("/api/doctor/patients?search=张", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_assign_patient(test_client):
    """测试分配患者"""
    response = test_client.post("/api/doctor/patients/assign",
        headers={"Authorization": "Bearer test_1"},
        json={
            "patient_id": 1,
            "relationship_type": "primary"
        }
    )
    assert response.status_code in [200, 201]

def test_get_assignable_patients(test_client):
    """测试获取可分配患者列表"""
    response = test_client.get("/api/doctor/patients/assignable", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_unassign_patient(test_client):
    """测试解除患者关联"""
    response = test_client.delete("/api/doctor/patients/1/unassign", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 404]  # 404 if not assigned

def test_get_patient_detail(test_client):
    """测试获取患者详情"""
    response = test_client.get("/api/doctor/patients/1", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 403, 404]  # 403 if no access, 404 if not exists

def test_get_patient_consultations(test_client):
    """测试获取患者对话列表"""
    response = test_client.get("/api/doctor/patients/1/consultations", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 403, 404]

def test_get_consultation_detail(test_client):
    """测试获取对话详情"""
    response = test_client.get("/api/doctor/consultations/test-session-id", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 403, 404]

def test_create_order(test_client):
    """测试创建医嘱"""
    response = test_client.post("/api/doctor/orders",
        headers={"Authorization": "Bearer test_1"},
        json={
            "patient_id": 1,
            "order_type": "medication",
            "title": "测试医嘱",
            "description": "每天服用",
            "schedule_type": "daily",
            "start_date": "2026-02-11",
            "reminder_times": ["08:00", "20:00"]
        }
    )
    assert response.status_code in [201, 403, 404]

def test_activate_order(test_client):
    """测试激活医嘱"""
    response = test_client.post("/api/doctor/orders/1/activate",
        headers={"Authorization": "Bearer test_1"},
        json={"confirm": True}
    )
    assert response.status_code in [200, 400, 403, 404]

def test_get_patient_orders(test_client):
    """测试获取患者医嘱列表"""
    response = test_client.get("/api/doctor/patients/1/orders", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 403, 404]

def test_get_patient_tasks(test_client):
    """测试获取患者任务列表"""
    response = test_client.get("/api/doctor/patients/1/tasks?task_date=2026-02-11", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 403, 404]
```

**Step 2: Run test to verify it fails**

```bash
docker exec -it home-health-backend pytest backend/test/test_doctor_workstation_api.py::test_get_doctor_info -v
```

**Step 3: Ensure test mode is enabled**

Verify `TEST_MODE=true` in environment for `test_1` token to work.

**Step 4: Run tests and verify they pass**

```bash
docker exec -it home-health-backend pytest backend/test/test_doctor_workstation_api.py -v
```

**Step 5: Commit**

```bash
git add backend/test/test_doctor_workstation_api.py
git commit -m "test(doctor): add doctor workstation API tests"
```

---

### Task 3: 医嘱管理 API 测试

**Files:**
- Create: `backend/test/test_medical_orders_api.py`

**Step 1: Write the failing test**

```python
# backend/test/test_medical_orders_api.py
import pytest
from datetime import date

def test_create_medical_order(test_client):
    """测试创建医嘱"""
    response = test_client.post("/api/medical-orders",
        headers={"Authorization": "Bearer test_1"},
        json={
            "order_type": "medication",
            "title": "阿司匹林",
            "description": "每日一次",
            "schedule_type": "daily",
            "start_date": "2026-02-11",
            "reminder_times": ["08:00"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "阿司匹林"
    assert data["status"] == "draft"

def test_get_medical_orders(test_client):
    """测试获取医嘱列表"""
    response = test_client.get("/api/medical-orders", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_medical_orders_with_status_filter(test_client):
    """测试按状态筛选医嘱"""
    response = test_client.get("/api/medical-orders?status=active", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200

def test_get_medical_order_detail(test_client):
    """测试获取医嘱详情"""
    response = test_client.get("/api/medical-orders/1", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 404]

def test_update_medical_order(test_client):
    """测试更新医嘱"""
    response = test_client.put("/api/medical-orders/1",
        headers={"Authorization": "Bearer test_1"},
        json={"title": "更新后的医嘱"}
    )
    assert response.status_code in [200, 404, 400]

def test_activate_medical_order(test_client):
    """测试激活医嘱"""
    response = test_client.post("/api/medical-orders/1/activate",
        headers={"Authorization": "Bearer test_1"},
        json={"confirm": True}
    )
    assert response.status_code in [200, 404, 400]

def test_get_daily_tasks(test_client):
    """测试获取每日任务"""
    response = test_client.get("/api/medical-orders/tasks/2026-02-11", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "completed" in data
    assert "overdue" in data
    assert "summary" in data

def test_complete_task(test_client):
    """测试完成任务打卡"""
    response = test_client.post("/api/medical-orders/tasks/1/complete",
        headers={"Authorization": "Bearer test_1"},
        json={
            "completion_type": "check",
            "notes": "已完成"
        }
    )
    assert response.status_code in [200, 404, 400]

def test_get_daily_compliance(test_client):
    """测试获取每日依从性"""
    response = test_client.get("/api/medical-orders/compliance/daily?task_date=2026-02-11", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200

def test_get_weekly_compliance(test_client):
    """测试获取每周依从性"""
    response = test_client.get("/api/medical-orders/compliance/weekly", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200

def test_create_family_bond(test_client):
    """测试创建家属关系"""
    response = test_client.post("/api/medical-orders/family-bonds",
        headers={"Authorization": "Bearer test_1"},
        json={
            "patient_id": 1,
            "family_member_phone": "13800138001",
            "relationship": "spouse"
        }
    )
    assert response.status_code in [201, 400, 404]

def test_get_family_bonds(test_client):
    """测试获取家属关系"""
    response = test_client.get("/api/medical-orders/family-bonds", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200

def test_get_alerts(test_client):
    """测试获取预警列表"""
    response = test_client.get("/api/medical-orders/alerts", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200
```

**Step 2-5:** Run, Verify, Commit (same pattern)

---

### Task 4: 科室和疾病 API 测试

**Files:**
- Create: `backend/test/test_departments_diseases_api.py`

**Step 1: Write the tests**

```python
# backend/test/test_departments_diseases_api.py
import pytest

def test_get_departments(test_client):
    """测试获取科室列表"""
    response = test_client.get("/api/departments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_department_detail(test_client):
    """测试获取科室详情"""
    response = test_client.get("/api/departments/1")
    assert response.status_code in [200, 404]

def test_get_diseases(test_client):
    """测试获取疾病列表"""
    response = test_client.get("/api/diseases")
    assert response.status_code == 200

def test_get_diseases_with_search(test_client):
    """测试搜索疾病"""
    response = test_client.get("/api/diseases?search=感冒")
    assert response.status_code == 200

def test_get_disease_detail(test_client):
    """测试获取疾病详情"""
    response = test_client.get("/api/diseases/1")
    assert response.status_code in [200, 404]

def test_get_diseases_by_department(test_client):
    """测试按科室获取疾病"""
    response = test_client.get("/api/diseases?department_id=1")
    assert response.status_code == 200
```

---

### Task 5: 药品管理 API 测试

**Files:**
- Create: `backend/test/test_drugs_api.py`

**Step 1: Write the tests**

```python
# backend/test/test_drugs_api.py
import pytest

def test_get_drugs(test_client):
    """测试获取药品列表"""
    response = test_client.get("/api/drugs")
    assert response.status_code == 200

def test_get_drugs_with_search(test_client):
    """测试搜索药品"""
    response = test_client.get("/api/drugs?search=阿司匹林")
    assert response.status_code == 200

def test_get_drug_detail(test_client):
    """测试获取药品详情"""
    response = test_client.get("/api/drugs/1")
    assert response.status_code in [200, 404]
```

---

### Task 6: AI 对话 API 测试

**Files:**
- Create: `backend/test/test_ai_api.py`

**Step 1: Write the tests**

```python
# backend/test/test_ai_api.py
import pytest

def test_create_session(test_client):
    """测试创建会话"""
    response = test_client.post("/api/sessions",
        headers={"Authorization": "Bearer test_1"},
        json={"department_id": 1, "doctor_id": 1}
    )
    assert response.status_code in [200, 201]

def test_send_message(test_client):
    """测试发送消息"""
    response = test_client.post("/api/sessions/test-session/messages",
        headers={"Authorization": "Bearer test_1"},
        json={"content": "你好，我头疼"}
    )
    assert response.status_code in [200, 404]

def test_get_sessions(test_client):
    """测试获取会话列表"""
    response = test_client.get("/api/sessions", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code == 200

def test_get_session_messages(test_client):
    """测试获取会话消息"""
    response = test_client.get("/api/sessions/test-session/messages", headers={
        "Authorization": "Bearer test_1"
    })
    assert response.status_code in [200, 404]
```

---

### Task 7: AuthService 单元测试

**Files:**
- Create: `backend/test/test_auth_service.py`

**Step 1: Write the tests**

```python
# backend/test/test_auth_service.py
import pytest
from backend.app.services.auth_service import AuthService
from datetime import datetime, timedelta

def test_create_token(db_session):
    """测试创建 access token"""
    token = AuthService.create_token(1, "access")
    assert token is not None
    assert isinstance(token, str)

def test_create_refresh_token(db_session):
    """测试创建 refresh token"""
    token = AuthService.create_token(1, "refresh")
    assert token is not None
    assert isinstance(token, str)

def test_create_tokens_pair(db_session):
    """测试创建 token 对"""
    access, refresh = AuthService.create_tokens(1)
    assert access is not None
    assert refresh is not None
    assert access != refresh

def test_verify_valid_token(db_session):
    """测试验证有效 token"""
    token = AuthService.create_token(1, "access")
    user_id = AuthService.verify_token(token, "access")
    assert user_id == 1

def test_verify_invalid_token(db_session):
    """测试验证无效 token"""
    user_id = AuthService.verify_token("invalid_token", "access")
    assert user_id is None

def test_verify_test_mode_token(db_session):
    """测试测试模式 token"""
    # 需要确保 TEST_MODE=true
    user_id = AuthService.verify_token("test_123", "access")
    assert user_id == 123

def test_refresh_tokens_valid(db_session):
    """测试刷新 token - 有效"""
    refresh_token = AuthService.create_token(1, "refresh")
    result = AuthService.refresh_tokens(refresh_token)
    assert result is not None
    new_access, new_refresh = result
    assert new_access is not None
    assert new_refresh is not None

def test_refresh_tokens_invalid(db_session):
    """测试刷新 token - 无效"""
    result = AuthService.refresh_tokens("invalid_token")
    assert result is None

def test_get_or_create_user_new(db_session):
    """测试获取或创建用户 - 新用户"""
    user, is_new = AuthService.get_or_create_user(db_session, "19912345678")
    assert is_new is True
    assert user.phone == "19912345678"

def test_get_or_create_user_existing(db_session):
    """测试获取或创建用户 - 已存在用户"""
    phone = "19912345678"
    # 第一次创建
    AuthService.get_or_create_user(db_session, phone)
    # 第二次获取
    user, is_new = AuthService.get_or_create_user(db_session, phone)
    assert is_new is False
    assert user.phone == phone

def test_update_user_profile(db_session):
    """测试更新用户资料"""
    user, _ = AuthService.get_or_create_user(db_session, "19912345679")
    updated = AuthService.update_user_profile(
        db_session, user,
        {"nickname": "测试用户", "gender": "male"}
    )
    assert updated.nickname == "测试用户"
    assert updated.gender == "male"
    assert updated.is_profile_completed is True

def test_check_phone_status_not_exists(db_session):
    """测试检查手机号状态 - 不存在"""
    exists, has_password = AuthService.check_phone_status(db_session, "19912345670")
    assert exists is False
    assert has_password is False

def test_register_with_password_new_user(db_session):
    """测试密码注册 - 新用户"""
    user, is_new = AuthService.register_with_password(
        db_session, "19912345671", "Test123456"
    )
    assert is_new is True
    assert user.phone == "19912345671"
    assert user.password_hash is not None

def test_login_with_password_success(db_session):
    """测试密码登录 - 成功"""
    # 先注册
    AuthService.register_with_password(db_session, "19912345672", "Test123456")
    # 再登录
    user, error = AuthService.login_with_password(db_session, "19912345672", "Test123456")
    assert user is not None
    assert error == ""

def test_login_with_password_wrong_password(db_session):
    """测试密码登录 - 错误密码"""
    # 先注册
    AuthService.register_with_password(db_session, "19912345673", "Test123456")
    # 错误密码登录
    user, error = AuthService.login_with_password(db_session, "19912345673", "WrongPassword")
    assert user is None
    assert error != ""

def test_login_with_password_user_not_exists(db_session):
    """测试密码登录 - 用户不存在"""
    user, error = AuthService.login_with_password(db_session, "19912345674", "Test123456")
    assert user is None
    assert error != ""

def test_set_user_password(db_session):
    """测试设置用户密码"""
    user, _ = AuthService.get_or_create_user(db_session, "19912345675")
    success = AuthService.set_user_password(db_session, user, "NewPassword123")
    assert success is True
    assert user.password_hash is not None

def test_reset_password_success(db_session):
    """测试重置密码 - 成功"""
    user, _ = AuthService.get_or_create_user(db_session, "19912345676")
    success, error = AuthService.reset_password(db_session, user.phone, "NewPassword123")
    assert success is True
    assert error == ""

def test_reset_password_user_not_exists(db_session):
    """测试重置密码 - 用户不存在"""
    success, error = AuthService.reset_password(db_session, "19912345677", "NewPassword123")
    assert success is False
    assert error != ""
```

---

### Task 8: MedicalOrderService 单元测试

**Files:**
- Create: `backend/test/test_medical_order_service.py`

**Step 1: Write the tests**

```python
# backend/test/test_medical_order_service.py
import pytest
from datetime import date, time
from backend.app.services.medical_order_service import MedicalOrderService

def test_create_draft_order(db_session):
    """测试创建草稿医嘱"""
    service = MedicalOrderService(db_session)

    user, _ = AuthService.get_or_create_user(db_session, "19912345680")

    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": "medication",
        "title": "阿司匹林",
        "description": "每日一次",
        "schedule_type": "daily",
        "start_date": date(2026, 2, 11),
        "reminder_times": ["08:00"]
    })

    assert order.id is not None
    assert order.title == "阿司匹林"
    assert order.status.value == "draft"

def test_activate_order(db_session):
    """测试激活医嘱"""
    service = MedicalOrderService(db_session)

    user, _ = AuthService.get_or_create_user(db_session, "19912345681")

    # 创建草稿
    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": "medication",
        "title": "测试医嘱",
        "schedule_type": "once",
        "start_date": date(2026, 2, 11),
        "reminder_times": ["08:00"]
    })

    # 激活
    activated = service.activate_order(order.id)
    assert activated.status.value == "active"

def test_activate_order_not_found(db_session):
    """测试激活不存在的医嘱"""
    service = MedicalOrderService(db_session)
    with pytest.raises(ValueError):
        service.activate_order(99999)

def test_get_patient_orders(db_session):
    """测试获取患者医嘱列表"""
    service = MedicalOrderService(db_session)

    user, _ = AuthService.get_or_create_user(db_session, "19912345682")

    service.create_draft_order({
        "patient_id": user.id,
        "order_type": "medication",
        "title": "测试医嘱",
        "schedule_type": "once",
        "start_date": date(2026, 2, 11),
        "reminder_times": ["08:00"]
    })

    orders = service.get_patient_orders(user.id)
    assert len(orders) > 0

def test_get_patient_tasks(db_session):
    """测试获取患者任务列表"""
    service = MedicalOrderService(db_session)

    user, _ = AuthService.get_or_create_user(db_session, "19912345683")

    # 创建并激活医嘱
    order = service.create_draft_order({
        "patient_id": user.id,
        "order_type": "medication",
        "title": "测试医嘱",
        "schedule_type": "once",
        "start_date": date(2026, 2, 11),
        "reminder_times": ["08:00"]
    })
    service.activate_order(order.id)

    tasks = service.get_patient_tasks(user.id, date(2026, 2, 11))
    assert len(tasks) > 0
```

---

## 第二阶段：前端 P0 测试覆盖

### Task 9: 登录页面组件测试

**Files:**
- Create: `frontend/src/pages/__tests__/Login.test.tsx`

**Step 1: Write the test**

```typescript
// frontend/src/pages/__tests__/Login.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { Login } from '../Login';

// Mock API
vi.mock('@/api', () => ({
  authApi: {
    sendCode: vi.fn(),
    login: vi.fn(),
  },
}));

const { authApi } = await import('@/api');

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderLogin = () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );
  };

  describe('UI Rendering', () => {
    it('should render phone input', () => {
      renderLogin();
      expect(screen.getByPlaceholderText(/手机号/)).toBeInTheDocument();
    });

    it('should render code input', () => {
      renderLogin();
      expect(screen.getByPlaceholderText(/验证码/)).toBeInTheDocument();
    });

    it('should render send code button', () => {
      renderLogin();
      expect(screen.getByText(/获取验证码/)).toBeInTheDocument();
    });

    it('should render login button', () => {
      renderLogin();
      expect(screen.getByText(/登录/)).toBeInTheDocument();
    });
  });

  describe('Send Verification Code', () => {
    it('should send code successfully', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.sendCode).mockResolvedValue({ data: { expires_in: 300 } });

      renderLogin();

      const phoneInput = screen.getByPlaceholderText(/手机号/);
      const sendButton = screen.getByText(/获取验证码/);

      await user.type(phoneInput, '13800138000');
      await user.click(sendButton);

      await waitFor(() => {
        expect(authApi.sendCode).toHaveBeenCalledWith('13800138000');
      });
    });

    it('should show error with invalid phone', async () => {
      const user = userEvent.setup();
      renderLogin();

      const phoneInput = screen.getByPlaceholderText(/手机号/);
      const sendButton = screen.getByText(/获取验证码/);

      await user.type(phoneInput, '123');
      await user.click(sendButton);

      expect(screen.getByText(/请输入正确的手机号/)).toBeInTheDocument();
    });
  });

  describe('Login', () => {
    it('should login successfully', async () => {
      const user = userEvent.setup();
      vi.mocked(authApi.login).mockResolvedValue({
        data: {
          token: 'test_token',
          user: { id: 1, phone: '13800138000' },
          is_new_user: false
        }
      });

      renderLogin();

      const phoneInput = screen.getByPlaceholderText(/手机号/);
      const codeInput = screen.getByPlaceholderText(/验证码/);
      const loginButton = screen.getByText(/登录/);

      await user.type(phoneInput, '13800138000');
      await user.type(codeInput, '123456');
      await user.click(loginButton);

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalledWith({
          phone: '13800138000',
          code: '123456'
        });
      });
    });
  });
});
```

**Step 2: Configure vitest**

```javascript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

```typescript
// frontend/src/test/setup.ts
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

expect.extend(matchers);

afterEach(() => {
  cleanup();
});
```

**Step 3: Run tests**

```bash
cd frontend && npm run test
```

**Step 4: Commit**

```bash
git add frontend/src/pages/__tests__/ frontend/vitest.config.ts frontend/src/test/
git commit -m "test(frontend): add login page tests"
```

---

### Task 10: 仪表盘组件测试

**Files:**
- Create: `frontend/src/pages/__tests__/Dashboard.test.tsx`

**Step 1: Write the tests**

```typescript
// frontend/src/pages/__tests__/Dashboard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from '../Dashboard';

vi.mock('@/api', () => ({
  statsApi: {
    getStats: vi.fn().mockResolvedValue({
      data: { total_users: 100, total_doctors: 10 }
    });
  },
}));

describe('Dashboard Page', () => {
  const renderDashboard = () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  it('should render dashboard title', () => {
    renderDashboard();
    expect(screen.getByText(/仪表盘/)).toBeInTheDocument();
  });

  it('should render stats cards', () => {
    renderDashboard();
    // 检查统计数据卡片是否渲染
    expect(screen.getByText(/总用户数/)).toBeInTheDocument();
  });
});
```

---

### Task 11: 患者列表组件测试

**Files:**
- Create: `frontend/src/pages/doctor/__tests__/PatientList.test.tsx`

**Step 1: Write the tests**

```typescript
// frontend/src/pages/doctor/__tests__/PatientList.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PatientList } from '../PatientList';

vi.mock('@/api', () => ({
  doctorApi: {
    getPatients: vi.fn().mockResolvedValue({
      data: [
        { id: 1, nickname: '张三', phone: '13800138000' }
      ]
    }),
    getMe: vi.fn().mockResolvedValue({
      data: { id: 1, username: 'Dr. Li' }
    }),
    getPatientStats: vi.fn().mockResolvedValue({
      data: { total: 10, active: 5, new_today: 1, low_compliance: 2 }
    }),
  },
}));

describe('PatientList Page', () => {
  it('should render page title', () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>
    );
    expect(screen.getByText(/我的患者/)).toBeInTheDocument();
  });

  it('should render search input', () => {
    render(
      <BrowserRouter>
        <PatientList />
      </BrowserRouter>
    );
    expect(screen.getByPlaceholderText(/搜索患者/)).toBeInTheDocument();
  });
});
```

---

### Task 12: ProtectedRoute 组件测试

**Files:**
- Create: `frontend/src/components/auth/__tests__/ProtectedRoute.test.tsx`

**Step 1: Write the tests**

```typescript
// frontend/src/components/auth/__tests__/ProtectedRoute.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';

describe('ProtectedRoute', () => {
  it('should redirect to login when not authenticated', () => {
    render(
      <BrowserRouter>
        <Routes>
          <ProtectedRoute path="/protected" element={<div>Protected Content</div>} />
        </Routes>
      </BrowserRouter>
    );

    // 应该重定向到登录页
    expect(window.location.pathname).toContain('/login');
  });

  it('should render content when authenticated', () => {
    // Mock authenticated state
    vi.mock('@/hooks/useAuth', () => ({
      useAuth: () => ({ user: { id: 1 }, isAuthenticated: true })
    }));

    render(
      <BrowserRouter>
        <Routes>
          <ProtectedRoute path="/protected" element={<div>Protected Content</div>} />
        </Routes>
      </BrowserRouter>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});
```

---

## 第三阶段：iOS P0 测试覆盖

### Task 13: AuthManager 单元测试

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyishengTests/AuthManagerTests.swift`

**Step 1: Write the tests**

```swift
// ios/xinlingyisheng/xinlingyishengTests/AuthManagerTests.swift
import XCTest
@testable import xinlingyisheng

/// AuthManager 单元测试
final class AuthManagerTests: XCTestCase {

    var authManager: AuthManager!

    override func setUp() {
        super.setUp()
        authManager = AuthManager.shared
    }

    override func tearDown() {
        authManager = nil
        super.tearDown()
    }

    // MARK: - Token Management Tests

    func testSaveAccessToken() async throws {
        // Given
        let token = "test_access_token_123"

        // When
        try await authManager.saveAccessToken(token)

        // Then
        let retrieved = try await authManager.getAccessToken()
        XCTAssertEqual(retrieved, token)
    }

    func testSaveRefreshToken() async throws {
        // Given
        let refreshToken = "test_refresh_token_456"

        // When
        try await authManager.saveRefreshToken(refreshToken)

        // Then
        let retrieved = try await authManager.getRefreshToken()
        XCTAssertEqual(retrieved, refreshToken)
    }

    func testClearAllTokens() async throws {
        // Given
        try await authManager.saveAccessToken("token")
        try await authManager.saveRefreshToken("refresh")

        // When
        try await authManager.clearAllTokens()

        // Then
        // 尝试获取 token 应该抛出错误
        do {
            _ = try await authManager.getAccessToken()
            XCTFail("应该抛出错误")
        } catch {
            // 预期行为
        }
    }

    // MARK: - Login Tests

    func testLoginWithCodeSuccess() async throws {
        // Given
        let phone = "13800138000"
        let code = "123456"

        // Mock API response
        // 需要配置 mock API

        // When
        try await authManager.loginWithCode(phone: phone, code: code)

        // Then
        XCTAssertNotNil(authManager.currentUser)
        XCTAssertEqual(authManager.currentUser?.phone, phone)
    }

    func testLogout() async throws {
        // Given - 先登录
        // ... 设置登录状态

        // When
        authManager.logout()

        // Then
        XCTAssertNil(authManager.currentUser)
    }

    // MARK: - User Profile Tests

    func testUpdateProfile() async throws {
        // Given
        let profile = UserProfileUpdate(
            nickname: "测试用户",
            gender: .male,
            birthday: Date()
        )

        // When
        try await authManager.updateProfile(profile)

        // Then
        XCTAssertEqual(authManager.currentUser?.nickname, "测试用户")
    }
}
```

**Step 2: Run tests**

```bash
cd ios && xcodebuild test -scheme xinlingyisheng -destination 'platform=iOS Simulator,name=iPhone 15'
```

**Step 3: Commit**

```bash
git add ios/xinlingyisheng/xinlingyishengTests/AuthManagerTests.swift
git commit -m "test(ios): add AuthManager unit tests"
```

---

### Task 14: KeychainManager 单元测试

**Files:**
- Create: `ios/xinlingyisheng/xinlingyishengTests/KeychainManagerTests.swift`

**Step 1: Write the tests**

```swift
// ios/xinlingyisheng/xinlingyishengTests/KeychainManagerTests.swift
import XCTest
@testable import xinlingyisheng

/// KeychainManager 单元测试
final class KeychainManagerTests: XCTestCase {

    var keychain: KeychainManager!

    override func setUp() {
        super.setUp()
        keychain = KeychainManager.shared
        // 清理测试数据
        try? keychain.delete(forKey: "test_key")
    }

    override func tearDown() {
        // 清理测试数据
        try? keychain.delete(forKey: "test_key")
        keychain = nil
        super.tearDown()
    }

    // MARK: - Save/Retrieve Tests

    func testSaveAndRetrieve() async throws {
        // Given
        let key = "test_key"
        let value = "test_value_123"

        // When
        try await keychain.save(value, forKey: key)
        let retrieved = try await keychain.retrieve(forKey: key)

        // Then
        XCTAssertEqual(retrieved, value)
    }

    func testRetrieveNonExistentKey() async throws {
        // Given
        let key = "non_existent_key"

        // When & Then
        do {
            _ = try await keychain.retrieve(forKey: key)
            XCTFail("应该抛出错误")
        } catch KeychainError.itemNotFound {
            // 预期行为
        }
    }

    func testDeleteKey() async throws {
        // Given
        let key = "test_key_delete"
        try await keychain.save("value", forKey: key)

        // When
        try await keychain.delete(forKey: key)

        // Then
        do {
            _ = try await keychain.retrieve(forKey: key)
            XCTFail("应该抛出错误")
        } catch KeychainError.itemNotFound {
            // 预期行为
        }
    }

    func testUpdateValue() async throws {
        // Given
        let key = "test_key_update"
        try await keychain.save("original_value", forKey: key)

        // When
        try await keychain.save("updated_value", forKey: key)
        let retrieved = try await keychain.retrieve(forKey: key)

        // Then
        XCTAssertEqual(retrieved, "updated_value")
    }

    func testExists() async throws {
        // Given
        let key = "test_key_exists"

        // When - 不存在时
        var exists = keychain.exists(forKey: key)
        XCTAssertFalse(exists)

        // 保存后
        try await keychain.save("value", forKey: key)
        exists = keychain.exists(forKey: key)

        // Then
        XCTAssertTrue(exists)
    }

    // MARK: - Token Methods Tests

    func testSaveAndGetAccessToken() async throws {
        // Given
        let token = "access_token_xyz"

        // When
        try await keychain.saveAccessToken(token)
        let retrieved = try await keychain.getAccessToken()

        // Then
        XCTAssertEqual(retrieved, token)
    }

    func testSaveAndGetRefreshToken() async throws {
        // Given
        let token = "refresh_token_abc"

        // When
        try await keychain.saveRefreshToken(token)
        let retrieved = try await keychain.getRefreshToken()

        // Then
        XCTAssertEqual(retrieved, token)
    }

    func testClearAllTokens() async throws {
        // Given
        try await keychain.saveAccessToken("access")
        try await keychain.saveRefreshToken("refresh")

        // When
        try await keychain.clearAllTokens()

        // Then
        XCTAssertFalse(keychain.exists(forKey: "auth_token"))
        XCTAssertFalse(keychain.exists(forKey: "refresh_token"))
    }
}
```

---

### Task 15: LoginViewModel 单元测试

**Files:**
- Create: `ios/xinlingyisheng/xinlingyishengTests/LoginViewModelTests.swift`

**Step 1: Write the tests**

```swift
// ios/xinlingyisheng/xinlingyishengTests/LoginViewModelTests.swift
import XCTest
@testable import xinlingyisheng

/// LoginViewModel 单元测试
final class LoginViewModelTests: XCTestCase {

    var viewModel: LoginViewModel!

    override func setUp() {
        super.setUp()
        viewModel = LoginViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: - Phone Validation Tests

    func testValidPhone() {
        // Given
        viewModel.phone = "13800138000"

        // When & Then
        XCTAssertTrue(viewModel.isPhoneValid)
    }

    func testInvalidPhoneTooShort() {
        // Given
        viewModel.phone = "138001380"

        // When & Then
        XCTAssertFalse(viewModel.isPhoneValid)
    }

    func testInvalidPhoneTooLong() {
        // Given
        viewModel.phone = "138001380001"

        // When & Then
        XCTAssertFalse(viewModel.isPhoneValid)
    }

    func testInvalidPhoneNonNumeric() {
        // Given
        viewModel.phone = "1380013800a"

        // When & Then
        XCTAssertFalse(viewModel.isPhoneValid)
    }

    // MARK: - Code Validation Tests

    func testValidCode() {
        // Given
        viewModel.verificationCode = "123456"

        // When & Then
        XCTAssertTrue(viewModel.isCodeValid)
    }

    func testInvalidCodeTooShort() {
        // Given
        viewModel.verificationCode = "12345"

        // When & Then
        XCTAssertFalse(viewModel.isCodeValid)
    }

    // MARK: - Login State Tests

    func testInitialState() {
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
    }

    func testLoginButtonDisabledWhenInvalid() {
        // Given
        viewModel.phone = "123"
        viewModel.verificationCode = "123456"

        // When & Then
        XCTAssertFalse(viewModel.canLogin)
    }

    func testLoginButtonEnabledWhenValid() {
        // Given
        viewModel.phone = "13800138000"
        viewModel.verificationCode = "123456"

        // When & Then
        XCTAssertTrue(viewModel.canLogin)
    }
}
```

---

### Task 16: UnifiedChatViewModel 单元测试

**Files:**
- Create: `ios/xinlingyisheng/xinlingyishengTests/UnifiedChatViewModelTests.swift`

**Step 1: Write the tests**

```swift
// ios/xinlingyisheng/xinlingyishengTests/UnifiedChatViewModelTests.swift
import XCTest
@testable import xinlingyisheng

/// UnifiedChatViewModel 单元测试
final class UnifiedChatViewModelTests: XCTestCase {

    var viewModel: UnifiedChatViewModel!

    override func setUp() {
        super.setUp()
        viewModel = UnifiedChatViewModel(
            userId: 1,
            departmentId: 1,
            doctorId: 1
        )
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: - Message Management Tests

    func testInitialState() {
        XCTAssertFalse(viewModel.messages.isEmpty)
        XCTAssertEqual(viewModel.inputMode, .text)
        XCTAssertFalse(viewModel.isVoiceMode)
    }

    func testSendMessage() async throws {
        // Given
        let messageText = "你好，我头疼"
        let initialCount = viewModel.messages.count

        // When
        try await viewModel.sendMessage(messageText)

        // Then
        XCTAssertEqual(viewModel.messages.count, initialCount + 1)
        let lastMessage = viewModel.messages.last
        XCTAssertEqual(lastMessage?.content, messageText)
    }

    func testClearMessages() {
        // Given
        viewModel.clearMessages()

        // Then
        XCTAssertTrue(viewModel.messages.isEmpty)
    }

    // MARK: - Voice Mode Tests

    func testToggleVoiceMode() {
        // Given
        XCTAssertFalse(viewModel.isVoiceMode)

        // When
        viewModel.isVoiceMode = true

        // Then
        XCTAssertTrue(viewModel.isVoiceMode)
    }

    // MARK: - Cleanup Tests

    func testCleanup() {
        // When
        viewModel.cleanupVoiceBindings()
        viewModel.fullCleanup()

        // Then - 验证资源被清理
        XCTAssertTrue(viewModel.messages.isEmpty)
        XCTAssertEqual(viewModel.inputMode, .text)
    }
}
```

---

## 第四阶段：E2E 测试

### Task 17: 前端 E2E 测试配置

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/tests/e2e/auth.spec.ts`

**Step 1: Configure Playwright**

```typescript
// frontend/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:8150',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:8150',
    reuseExistingServer: !process.env.CI,
  },
});
```

**Step 2: Write E2E tests**

```typescript
// frontend/tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/');

    // 点击登录
    await page.click('text=登录');

    // 输入手机号
    await page.fill('input[placeholder*="手机号"]', '13800138000');

    // 输入验证码（测试模式）
    await page.fill('input[placeholder*="验证码"]', '000000');

    // 点击登录按钮
    await page.click('button:has-text("登录")');

    // 验证登录成功
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/');
    await page.click('text=登录');

    await page.fill('input[placeholder*="手机号"]', '12345');
    await page.click('text=获取验证码');

    // 验证错误提示
    await expect(page.locator('text=请输入正确的手机号')).toBeVisible();
  });
});
```

**Step 3: Run E2E tests**

```bash
cd frontend && npx playwright test
```

**Step 4: Commit**

```bash
git add frontend/playwright.config.ts frontend/tests/
git commit -m "test(e2e): add Playwright E2E tests"
```

---

## 第五阶段：CI/CD 测试集成

### Task 18: 配置 GitHub Actions 测试流水线

**Files:**
- Create: `.github/workflows/test.yml`

**Step 1: Create workflow**

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: home_health_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx

      - name: Run tests
        run: |
          cd backend
          pytest test/ -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run tests
        run: cd frontend && npm run test

      - name: Run E2E tests
        run: cd frontend && npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/

  ios-tests:
    runs-on: macos-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Xcode
        uses: maxim-lobanov/setup-xcode@v1
        with:
          xcode-version: latest-stable

      - name: Run iOS tests
        run: |
          cd ios
          xcodebuild test -scheme xinlingyisheng \
            -destination 'platform=iOS Simulator,name=iPhone 15' \
            -resultBundlePath TestResults.xcresult

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ios-test-results
          path: ios/TestResults.xcresult
```

---

## 执行步骤总结

### Phase 1: 后端测试 (Tasks 1-8)
1. 认证 API 测试
2. 医生工作台 API 测试
3. 医嘱管理 API 测试
4. 科室疾病 API 测试
5. 药品管理 API 测试
6. AI 对话 API 测试
7. AuthService 单元测试
8. MedicalOrderService 单元测试

### Phase 2: 前端测试 (Tasks 9-12)
9. 登录页面测试
10. 仪表盘测试
11. 患者列表测试
12. ProtectedRoute 测试

### Phase 3: iOS 测试 (Tasks 13-16)
13. AuthManager 测试
14. KeychainManager 测试
15. LoginViewModel 测试
16. UnifiedChatViewModel 测试

### Phase 4: E2E 测试 (Task 17)
17. 前端 E2E 测试

### Phase 5: CI/CD (Task 18)
18. GitHub Actions 配置

---

## 目标验证

执行完成后，运行以下命令验证覆盖率：

**后端:**
```bash
docker exec -it home-health-backend pytest backend/test/ --cov=app --cov-report=term
# 目标: > 80%
```

**前端:**
```bash
cd frontend && npm run test -- --coverage
# 目标: > 70%
```

**iOS:**
```bash
cd ios && xcodebuild test -scheme xinlingyisheng
# 目标: 所有测试通过
```

---

**创建时间**: 2026-02-11
**预计工作量**: 3-5 天
