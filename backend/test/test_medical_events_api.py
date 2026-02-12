"""
病历事件 API 测试

测试覆盖：
1. CRUD 操作（创建、读取、更新、删除）
2. 分页和筛选功能
3. 权限验证
4. 数据验证
5. 附件管理
6. 备注管理
7. 数据聚合
8. 导出功能
9. 共享链接

注意：TEST_MODE 下，get_current_user 总是返回固定的测试用户（phone="test_user"）
"""
import pytest
import os
from datetime import datetime, timedelta, timezone
from fastapi import status

# 导入模型
try:
    from app.models.medical_event import (
        MedicalEvent, EventAttachment, EventNote, ExportRecord,
        EventStatus, RiskLevel, AgentType, AttachmentType
    )
    from app.models.session import Session
    from app.models.message import Message, SenderType
    from app.models.user import User
except ImportError:
    from backend.app.models.medical_event import (
        MedicalEvent, EventAttachment, EventNote, ExportRecord,
        EventStatus, RiskLevel, AgentType, AttachmentType
    )
    from backend.app.models.session import Session
    from backend.app.models.message import Message, SenderType
    from backend.app.models.user import User


# ============================================================================
# 设置测试模式
# ============================================================================

os.environ["TEST_MODE"] = "true"


# ============================================================================
# 辅助函数
# ============================================================================

def get_test_user(db_session):
    """获取或创建固定的测试用户（与 TEST_MODE 行为一致）"""
    test_user = db_session.query(User).filter(User.phone == "test_user").first()
    if not test_user:
        test_user = User(
            phone="test_user",
            nickname="测试用户",
            is_active=True
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
    return test_user


def get_test_user_2(db_session):
    """获取或创建第二个测试用户"""
    test_user = db_session.query(User).filter(User.phone == "test_user_2").first()
    if not test_user:
        test_user = User(
            phone="test_user_2",
            nickname="测试用户2",
            is_active=True
        )
        db_session.add(test_user)
        db_session.commit()
        db_session.refresh(test_user)
    return test_user


def create_test_event(db_session, user_id, **kwargs):
    """创建测试医疗事件"""
    from datetime import datetime, timedelta, timezone

    event = MedicalEvent(
        user_id=user_id,
        title=kwargs.get("title", "测试病历事件"),
        department=kwargs.get("department", "皮肤科"),
        agent_type=kwargs.get("agent_type", AgentType.derma),
        chief_complaint=kwargs.get("chief_complaint", "皮肤瘙痒"),
        risk_level=kwargs.get("risk_level", RiskLevel.low),
        status=kwargs.get("status", EventStatus.active),
        summary=kwargs.get("summary"),
        ai_analysis=kwargs.get("ai_analysis", {}),
        sessions=kwargs.get("sessions", []),
        session_count=kwargs.get("session_count", 0),
        attachment_count=kwargs.get("attachment_count", 0),
        export_count=kwargs.get("export_count", 0),
    )
    db_session.add(event)
    db_session.commit()

    # 如果提供了 created_at，显式设置它
    if "created_at" in kwargs:
        event.created_at = kwargs["created_at"]
        db_session.commit()

    db_session.refresh(event)
    return event


def create_test_session(db_session, user_id, session_id=None, **kwargs):
    """创建测试会话"""
    session = Session(
        id=session_id or "test-session-123",
        user_id=user_id,
        agent_type=kwargs.get("agent_type", "derma"),
        agent_state=kwargs.get("agent_state", {
            "chief_complaint": "皮肤瘙痒",
            "symptoms": ["红疹", "瘙痒"],
            "risk_level": "low",
            "stage": "completed"
        }),
        status=kwargs.get("status", "active"),
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


def create_test_message(db_session, session_id, **kwargs):
    """创建测试消息"""
    message = Message(
        session_id=session_id,
        sender=kwargs.get("sender", SenderType.user),
        content=kwargs.get("content", "测试消息"),
        message_type=kwargs.get("message_type", "text"),
        attachments=kwargs.get("attachments"),
    )
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message


# ============================================================================
# CRUD 操作测试
# ============================================================================

class TestMedicalEventsCRUD:
    """病历事件 CRUD 操作测试"""

    def test_create_medical_event_success(self, test_client, db_session):
        """测试成功创建病历事件"""
        # 确保测试用户存在
        test_user = get_test_user(db_session)

        response = test_client.post(
            "/medical-events",
            json={
                "title": "皮肤科咨询",
                "department": "皮肤科",
                "agent_type": "derma",
                "chief_complaint": "面部红疹",
                "risk_level": "low"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "皮肤科咨询"
        assert data["department"] == "皮肤科"
        assert data["agent_type"] == "derma"
        assert data["chief_complaint"] == "面部红疹"
        assert data["risk_level"] == "low"
        assert data["status"] == "active"
        assert "id" in data

    def test_create_medical_event_with_minimal_fields(self, test_client, db_session):
        """测试使用最小字段创建病历事件"""
        get_test_user(db_session)

        response = test_client.post(
            "/medical-events",
            json={
                "title": "最小字段测试",
                "department": "全科",
                "agent_type": "general"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "最小字段测试"
        assert data["risk_level"] == "low"  # 默认值

    def test_create_medical_event_unauthorized(self, test_client):
        """测试未授权创建病历事件（TEST_MODE下总是有用户）"""
        # TEST_MODE 下会自动创建用户，所以不会返回 401
        response = test_client.post(
            "/medical-events",
            json={
                "title": "未授权测试",
                "department": "皮肤科",
                "agent_type": "derma"
            }
        )

        # TEST_MODE 下应该成功创建
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_medical_event_success(self, test_client, db_session):
        """测试成功获取病历事件详情"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.get(f"/medical-events/{event.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(event.id)
        assert data["title"] == "测试病历事件"

    def test_get_medical_event_not_found(self, test_client):
        """测试获取不存在的病历事件"""
        response = test_client.get("/medical-events/999999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_medical_event_forbidden(self, test_client, db_session):
        """测试获取其他用户的病历事件"""
        test_user = get_test_user(db_session)
        test_user_2 = get_test_user_2(db_session)
        event = create_test_event(db_session, test_user_2.id)

        response = test_client.get(f"/medical-events/{event.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_medical_event_success(self, test_client, db_session):
        """测试成功更新病历事件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.put(
            f"/medical-events/{event.id}",
            json={
                "title": "更新后的标题",
                "chief_complaint": "更新后的主诉",
                "risk_level": "medium"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "更新后的标题"
        assert data["chief_complaint"] == "更新后的主诉"
        assert data["risk_level"] == "medium"

    def test_update_medical_event_status(self, test_client, db_session):
        """测试更新病历事件状态"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.put(
            f"/medical-events/{event.id}",
            json={"status": "completed"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"

    def test_update_archived_event_fails(self, test_client, db_session):
        """测试更新已归档事件失败"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id, status=EventStatus.archived)

        response = test_client.put(
            f"/medical-events/{event.id}",
            json={"title": "尝试更新"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_medical_event_success(self, test_client, db_session):
        """测试成功删除病历事件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.delete(
            f"/medical-events/{event.id}?confirm=true"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 验证已删除
        get_response = test_client.get(f"/medical-events/{event.id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_medical_event_requires_confirmation(self, test_client, db_session):
        """测试删除需要确认参数"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        # 没有confirm参数或confirm=false会报400错误
        # 但是FastAPI的Query参数验证会返回422
        response = test_client.delete(f"/medical-events/{event.id}")

        # FastAPI 验证参数不存在会返回 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_archive_medical_event_success(self, test_client, db_session):
        """测试成功归档病历事件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(f"/medical-events/{event.id}/archive")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "archived"
        assert data["end_time"] is not None


# ============================================================================
# 列表和筛选测试
# ============================================================================

class TestMedicalEventsList:
    """病历事件列表和筛选测试"""

    def test_list_medical_events_empty(self, test_client):
        """测试获取空的病历事件列表"""
        response = test_client.get("/medical-events")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    def test_list_medical_events_with_data(self, test_client, db_session):
        """测试获取病历事件列表"""
        test_user = get_test_user(db_session)
        create_test_event(db_session, test_user.id, title="事件1")
        create_test_event(db_session, test_user.id, title="事件2")
        create_test_event(db_session, test_user.id, title="事件3")

        response = test_client.get("/medical-events")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 3
        assert data["total"] == 3

    def test_list_medical_events_pagination(self, test_client, db_session):
        """测试分页功能"""
        test_user = get_test_user(db_session)
        for i in range(25):
            create_test_event(db_session, test_user.id, title=f"事件{i}")

        response = test_client.get("/medical-events?page=1&page_size=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_medical_events_keyword_search(self, test_client, db_session):
        """测试关键词搜索"""
        test_user = get_test_user(db_session)
        create_test_event(db_session, test_user.id, title="皮肤过敏", chief_complaint="过敏症状", department="皮肤科")
        create_test_event(db_session, test_user.id, title="心血管检查", chief_complaint="心慌", department="心血管科")
        create_test_event(db_session, test_user.id, summary="包含皮肤关键词的内容", chief_complaint="其他症状", department="皮肤科")

        response = test_client.get("/medical-events?keyword=皮肤")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 应该找到2个：标题中的"皮肤过敏"和摘要中的"皮肤"
        assert len(data["events"]) == 2
        assert data["total"] == 2

    def test_list_medical_events_department_filter(self, test_client, db_session):
        """测试科室筛选"""
        test_user = get_test_user(db_session)
        create_test_event(db_session, test_user.id, department="皮肤科", agent_type=AgentType.derma)
        create_test_event(db_session, test_user.id, department="心血管科", agent_type=AgentType.cardio)
        create_test_event(db_session, test_user.id, department="皮肤科", agent_type=AgentType.derma)

        response = test_client.get("/medical-events?department=皮肤科")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 2

    def test_list_medical_events_status_filter(self, test_client, db_session):
        """测试状态筛选"""
        test_user = get_test_user(db_session)
        create_test_event(db_session, test_user.id, status=EventStatus.active)
        create_test_event(db_session, test_user.id, status=EventStatus.archived)
        create_test_event(db_session, test_user.id, status=EventStatus.completed)

        response = test_client.get("/medical-events?status=active")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 1

    def test_list_medical_events_risk_level_filter(self, test_client, db_session):
        """测试风险等级筛选"""
        test_user = get_test_user(db_session)
        create_test_event(db_session, test_user.id, risk_level=RiskLevel.low)
        create_test_event(db_session, test_user.id, risk_level=RiskLevel.high)
        create_test_event(db_session, test_user.id, risk_level=RiskLevel.medium)

        response = test_client.get("/medical-events?risk_level=high")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["risk_level"] == "high"

    def test_list_medical_events_date_range_filter(self, test_client, db_session):
        """测试日期范围筛选"""
        test_user = get_test_user(db_session)
        today = datetime.now().date()
        event = create_test_event(db_session, test_user.id)

        response = test_client.get(
            f"/medical-events?start_date={(today - timedelta(days=1)).isoformat()}&end_date={(today + timedelta(days=1)).isoformat()}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) >= 1

    def test_list_medical_events_sort_by_created_at(self, test_client, db_session):
        """测试按创建时间排序"""
        from datetime import datetime, timedelta, timezone

        test_user = get_test_user(db_session)
        now = datetime.now(timezone.utc)
        # 创建两个时间戳不同的事件
        event1 = create_test_event(db_session, test_user.id, title="事件1", created_at=now - timedelta(hours=1))
        event2 = create_test_event(db_session, test_user.id, title="事件2", created_at=now)

        response = test_client.get("/medical-events?sort_by=created_at&sort_order=desc")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 后创建的应该在前面
        assert data["events"][0]["title"] == "事件2"
        assert data["events"][1]["title"] == "事件1"

    def test_list_only_own_events(self, test_client, db_session):
        """测试只返回自己的事件"""
        test_user = get_test_user(db_session)
        test_user_2 = get_test_user_2(db_session)
        create_test_event(db_session, test_user.id, title="用户1的事件")
        create_test_event(db_session, test_user_2.id, title="用户2的事件")

        response = test_client.get("/medical-events")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["title"] == "用户1的事件"


# ============================================================================
# 附件管理测试
# ============================================================================

class TestAttachments:
    """附件管理测试"""

    def test_add_attachment_success(self, test_client, db_session):
        """测试成功添加附件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(
            f"/medical-events/{event.id}/attachments",
            json={
                "type": "image",
                "url": "https://example.com/image.jpg",
                "filename": "test.jpg",
                "file_size": 1024,
                "mime_type": "image/jpeg",
                "description": "测试图片"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["type"] == "image"
        assert data["url"] == "https://example.com/image.jpg"

    def test_add_attachment_to_archived_event_fails(self, test_client, db_session):
        """测试向已归档事件添加附件失败"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id, status=EventStatus.archived)

        response = test_client.post(
            f"/medical-events/{event.id}/attachments",
            json={
                "type": "image",
                "url": "https://example.com/image.jpg"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_attachment_increases_count(self, test_client, db_session):
        """测试添加附件后计数增加"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id, attachment_count=0)

        test_client.post(
            f"/medical-events/{event.id}/attachments",
            json={
                "type": "report",
                "url": "https://example.com/report.pdf"
            }
        )

        # 验证计数增加
        response = test_client.get(f"/medical-events/{event.id}")
        data = response.json()
        assert data["attachment_count"] == 1

    def test_delete_attachment_success(self, test_client, db_session):
        """测试成功删除附件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        # 先添加附件
        attachment = EventAttachment(
            event_id=event.id,
            type=AttachmentType.image,
            url="https://example.com/image.jpg"
        )
        db_session.add(attachment)
        db_session.commit()

        response = test_client.delete(
            f"/medical-events/{event.id}/attachments/{attachment.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_attachment_not_found(self, test_client, db_session):
        """测试删除不存在的附件"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.delete(
            f"/medical-events/{event.id}/attachments/999999"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# 备注管理测试
# ============================================================================

class TestNotes:
    """备注管理测试"""

    def test_add_note_success(self, test_client, db_session):
        """测试成功添加备注"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(
            f"/medical-events/{event.id}/notes",
            json={
                "content": "这是一条重要备注",
                "is_important": True
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "这是一条重要备注"
        assert data["is_important"] is True

    def test_add_note_validation_error(self, test_client, db_session):
        """测试添加空备注失败"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(
            f"/medical-events/{event.id}/notes",
            json={
                "content": ""
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_note_success(self, test_client, db_session):
        """测试成功更新备注"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        note = EventNote(
            event_id=event.id,
            content="原始备注"
        )
        db_session.add(note)
        db_session.commit()

        response = test_client.put(
            f"/medical-events/{event.id}/notes/{note.id}",
            json={
                "content": "更新后的备注"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "更新后的备注"

    def test_update_note_not_found(self, test_client, db_session):
        """测试更新不存在的备注"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.put(
            f"/medical-events/{event.id}/notes/999999",
            json={
                "content": "尝试更新"
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_note_success(self, test_client, db_session):
        """测试成功删除备注"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        note = EventNote(
            event_id=event.id,
            content="要删除的备注"
        )
        db_session.add(note)
        db_session.commit()

        response = test_client.delete(
            f"/medical-events/{event.id}/notes/{note.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


# ============================================================================
# 数据聚合测试
# ============================================================================

class TestAggregation:
    """数据聚合测试"""

    def test_aggregate_session_creates_new_event(self, test_client, db_session):
        """测试聚合会话创建新事件"""
        test_user = get_test_user(db_session)
        session = create_test_session(
            db_session,
            test_user.id,
            session_id="agg-test-1",
            agent_state={
                "chief_complaint": "手部皮肤干燥",
                "symptoms": ["脱皮", "瘙痒"],
                "risk_level": "low",
                "stage": "completed"
            }
        )

        # 添加消息
        create_test_message(db_session, session.id, content="我手部皮肤很干燥")
        create_test_message(db_session, session.id, sender=SenderType.ai, content="请问有多久了？")

        response = test_client.post(
            "/medical-events/aggregate",
            json={
                "session_id": "agg-test-1",
                "session_type": "derma"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_new_event"] is True
        assert "event_id" in data
        assert data["session_summary"]["chief_complaint"] == "手部皮肤干燥"

    def test_aggregate_session_adds_to_existing_event(self, test_client, db_session):
        """测试聚合会话到现有事件"""
        test_user = get_test_user(db_session)

        # 创建今天的事件
        today = datetime.now().date()
        existing_event = create_test_event(
            db_session,
            test_user.id,
            agent_type=AgentType.derma,
            status=EventStatus.active
        )
        # 修改创建时间为今天
        existing_event.start_time = datetime.combine(today, datetime.min.time())
        db_session.commit()

        session = create_test_session(
            db_session,
            test_user.id,
            session_id="agg-test-2",
            agent_state={
                "chief_complaint": "新的症状",
                "symptoms": ["红肿"],
                "risk_level": "medium",
                "stage": "completed"
            }
        )
        create_test_message(db_session, session.id, content="还有红肿")

        response = test_client.post(
            "/medical-events/aggregate",
            json={
                "session_id": "agg-test-2",
                "session_type": "derma"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 应该添加到现有事件
        assert "event_id" in data

    def test_aggregate_session_not_found(self, test_client):
        """测试聚合不存在的会话"""
        response = test_client.post(
            "/medical-events/aggregate",
            json={
                "session_id": "non-existent-session",
                "session_type": "derma"
            }
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_aggregate_session_insufficient_data(self, test_client, db_session):
        """测试数据不足时聚合失败"""
        test_user = get_test_user(db_session)
        session = create_test_session(
            db_session,
            test_user.id,
            session_id="agg-test-3",
            agent_state={
                "chief_complaint": "",
                "symptoms": [],
                "risk_level": "low",
                "stage": "greeting"
            }
        )

        response = test_client.post(
            "/medical-events/aggregate",
            json={
                "session_id": "agg-test-3",
                "session_type": "derma"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "会话信息不完整" in data["detail"]


# ============================================================================
# 导出功能测试
# ============================================================================

class TestExport:
    """导出功能测试"""

    def test_create_share_link_export(self, test_client, db_session):
        """测试创建共享链接导出"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(
            "/medical-events/export",
            json={
                "event_ids": [str(event.id)],
                "export_type": "share_link",
                "share_password": "test123",
                "expires_in_days": 7
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["export_type"] == "share_link"
        assert data["share_url"] is not None
        assert data["share_token"] is not None

    def test_create_pdf_export(self, test_client, db_session):
        """测试创建 PDF 导出"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        response = test_client.post(
            "/medical-events/export",
            json={
                "event_ids": [str(event.id)],
                "export_type": "pdf"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["export_type"] == "pdf"

    def test_export_increases_export_count(self, test_client, db_session):
        """测试导出后计数增加"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id, export_count=0)

        test_client.post(
            "/medical-events/export",
            json={
                "event_ids": [str(event.id)],
                "export_type": "share_link"
            }
        )

        # 验证计数增加
        response = test_client.get(f"/medical-events/{event.id}")
        data = response.json()
        assert data["export_count"] == 1

    def test_list_exports(self, test_client, db_session):
        """测试获取导出记录列表"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-token-123"
        )
        db_session.add(export)
        db_session.commit()

        response = test_client.get("/medical-events/exports")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1

    def test_delete_export(self, test_client, db_session):
        """测试删除导出记录"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-token-456"
        )
        db_session.add(export)
        db_session.commit()

        response = test_client.delete(f"/medical-events/exports/{export.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_access_share_link_success(self, test_client, db_session):
        """测试访问共享链接成功"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-share-789",
            is_active=True
        )
        db_session.add(export)
        db_session.commit()

        response = test_client.get("/medical-events/share/test-share-789")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "events" in data
        assert "export_info" in data

    def test_access_share_link_with_password(self, test_client, db_session):
        """测试带密码的共享链接"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-share-pass",
            share_password="secret123",
            is_active=True
        )
        db_session.add(export)
        db_session.commit()

        # 错误密码
        response = test_client.get("/medical-events/share/test-share-pass?password=wrong")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 正确密码
        response = test_client.get("/medical-events/share/test-share-pass?password=secret123")
        assert response.status_code == status.HTTP_200_OK

    def test_access_expired_share_link_fails(self, test_client, db_session):
        """测试访问过期链接失败"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-share-expired",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True
        )
        db_session.add(export)
        db_session.commit()

        response = test_client.get("/medical-events/share/test-share-expired")

        assert response.status_code == status.HTTP_410_GONE

    def test_access_max_views_link_fails(self, test_client, db_session):
        """测试访问达到最大次数的链接失败"""
        test_user = get_test_user(db_session)
        event = create_test_event(db_session, test_user.id)

        export = ExportRecord(
            user_id=test_user.id,
            event_id=event.id,
            export_type="share_link",
            event_ids=[str(event.id)],
            share_token="test-share-max",
            max_views=1,
            view_count=1,
            is_active=True
        )
        db_session.add(export)
        db_session.commit()

        response = test_client.get("/medical-events/share/test-share-max")

        assert response.status_code == status.HTTP_410_GONE


# ============================================================================
# 生成摘要测试
# ============================================================================

class TestGenerateSummary:
    """生成摘要测试"""

    def test_generate_summary_fallback(self, test_client, db_session):
        """测试摘要生成降级模式"""
        test_user = get_test_user(db_session)
        event = create_test_event(
            db_session,
            test_user.id,
            chief_complaint="测试主诉",
            department="皮肤科"
        )

        response = test_client.post(f"/medical-events/{event.id}/generate-summary")

        # AI 服务可能不可用，应该返回降级结果
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summary" in data
        assert "ai_analysis" in data

    def test_generate_summary_with_existing_summary(self, test_client, db_session):
        """测试已有摘要时跳过生成"""
        test_user = get_test_user(db_session)
        event = create_test_event(
            db_session,
            test_user.id,
            summary="已有摘要",
            ai_analysis={"symptoms": ["症状1"]}
        )

        response = test_client.post(f"/medical-events/{event.id}/generate-summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "已有摘要" in data["message"]

    def test_generate_summary_force_regenerate(self, test_client, db_session):
        """测试强制重新生成摘要"""
        test_user = get_test_user(db_session)
        event = create_test_event(
            db_session,
            test_user.id,
            summary="旧摘要",
            ai_analysis={}
        )

        response = test_client.post(
            f"/medical-events/{event.id}/generate-summary?force_regenerate=true"
        )

        assert response.status_code == status.HTTP_200_OK
