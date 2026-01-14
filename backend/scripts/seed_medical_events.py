"""
创建病历事件假数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models.user import User
from app.models.medical_event import (
    MedicalEvent, EventAttachment, EventNote,
    EventStatus, RiskLevel, AgentType, AttachmentType
)

def seed_medical_events():
    db = SessionLocal()
    try:
        # 获取第一个用户
        user = db.query(User).first()
        if not user:
            print("No user found. Please create a user first.")
            return
        
        print(f"Creating medical events for user: {user.id} ({user.phone})")
        
        # 检查是否已有数据
        existing = db.query(MedicalEvent).filter(MedicalEvent.user_id == user.id).count()
        if existing > 0:
            print(f"User already has {existing} medical events. Skipping seed.")
            return
        
        now = datetime.utcnow()
        
        # 事件1: 皮肤红疹 - 进行中
        event1 = MedicalEvent(
            user_id=user.id,
            title="皮肤红疹",
            department="皮肤科",
            agent_type=AgentType.derma,
            status=EventStatus.active,
            chief_complaint="手臂出现红色皮疹，伴有瘙痒",
            summary="AI判断：过敏性皮炎，建议观察病情变化后就医",
            risk_level=RiskLevel.medium,
            ai_analysis={
                "symptoms": ["红色斑疹", "轻度瘙痒", "局部肿胀"],
                "possible_diagnosis": ["过敏性皮炎 (78%)", "湿疹 (15%)", "接触性皮炎 (7%)"],
                "recommendations": [
                    "避免搔抓患处",
                    "保持皮肤清洁干燥",
                    "可使用炉甘石洗剂止痒",
                    "如症状加重请及时就医"
                ],
                "follow_up_reminders": ["建议3天内到皮肤科门诊就诊"],
                "timeline": [
                    {"time": (now - timedelta(days=3)).isoformat(), "event": "首次出现红疹", "type": "symptom"},
                    {"time": (now - timedelta(days=2)).isoformat(), "event": "开始瘙痒", "type": "symptom"},
                    {"time": (now - timedelta(days=1)).isoformat(), "event": "上传皮肤照片", "type": "action"}
                ]
            },
            sessions=[
                {
                    "session_id": "derma_session_001",
                    "session_type": "derma",
                    "timestamp": (now - timedelta(days=3)).isoformat(),
                    "summary": "用户咨询手臂红疹问题，可能与更换洗衣液有关"
                },
                {
                    "session_id": "derma_session_002",
                    "session_type": "derma",
                    "timestamp": (now - timedelta(days=1)).isoformat(),
                    "summary": "用户反馈症状加重，AI建议就医"
                }
            ],
            session_count=2,
            attachment_count=4,
            start_time=now - timedelta(days=3),
            created_at=now - timedelta(days=3),
            updated_at=now
        )
        db.add(event1)
        db.flush()
        
        # 添加附件
        for i in range(4):
            attachment = EventAttachment(
                event_id=event1.id,
                type=AttachmentType.image,
                url=f"https://example.com/images/skin_photo_{i+1}.jpg",
                thumbnail_url=f"https://example.com/images/skin_photo_{i+1}_thumb.jpg",
                filename=f"皮肤照片{i+1}.jpg",
                file_size=256000 + i * 50000,
                mime_type="image/jpeg",
                description=f"手臂皮疹照片 {i+1}",
                upload_time=now - timedelta(days=3-i)
            )
            db.add(attachment)
        
        # 事件2: 心悸检查 - 已完成
        event2 = MedicalEvent(
            user_id=user.id,
            title="心悸检查",
            department="心内科",
            agent_type=AgentType.cardio,
            status=EventStatus.completed,
            chief_complaint="心跳加速，偶发心慌",
            summary="AI判断：正常范围，无需担心",
            risk_level=RiskLevel.low,
            ai_analysis={
                "symptoms": ["心悸", "心跳加速"],
                "possible_diagnosis": ["窦性心动过速 (60%)", "焦虑性心悸 (30%)", "室上性早搏 (10%)"],
                "recommendations": [
                    "保持情绪稳定",
                    "规律作息",
                    "避免咖啡因摄入",
                    "建议做心电图检查"
                ],
                "follow_up_reminders": [],
                "timeline": []
            },
            sessions=[
                {
                    "session_id": "cardio_session_001",
                    "session_type": "diagnosis",
                    "timestamp": (now - timedelta(days=5)).isoformat(),
                    "summary": "用户咨询心跳加速问题，建议就医检查"
                }
            ],
            session_count=1,
            attachment_count=1,
            start_time=now - timedelta(days=5),
            end_time=now - timedelta(days=4),
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=4)
        )
        db.add(event2)
        db.flush()
        
        # 添加报告附件
        report_attachment = EventAttachment(
            event_id=event2.id,
            type=AttachmentType.report,
            url="https://example.com/reports/ecg_report.pdf",
            filename="心电图报告.pdf",
            file_size=512000,
            mime_type="application/pdf",
            description="心电图检查报告",
            upload_time=now - timedelta(days=4)
        )
        db.add(report_attachment)
        
        # 事件3: 头痛咨询 - 已导出
        event3 = MedicalEvent(
            user_id=user.id,
            title="头痛咨询",
            department="神经科",
            agent_type=AgentType.neuro,
            status=EventStatus.exported,
            chief_complaint="持续性头痛，伴有头晕",
            summary="AI判断：紧张性头痛，建议调整作息",
            risk_level=RiskLevel.low,
            ai_analysis={
                "symptoms": ["头痛", "头晕", "疲劳"],
                "possible_diagnosis": ["紧张性头痛 (75%)", "偏头痛 (20%)", "其他 (5%)"],
                "recommendations": [
                    "保证充足睡眠",
                    "减少用眼时间",
                    "适当运动放松",
                    "必要时可服用止痛药"
                ],
                "follow_up_reminders": [],
                "timeline": []
            },
            sessions=[
                {
                    "session_id": "neuro_session_001",
                    "session_type": "diagnosis",
                    "timestamp": (now - timedelta(days=7)).isoformat(),
                    "summary": "用户咨询头痛问题，初步判断为紧张性头痛"
                }
            ],
            session_count=1,
            attachment_count=0,
            export_count=1,
            start_time=now - timedelta(days=7),
            end_time=now - timedelta(days=6),
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=6)
        )
        db.add(event3)
        
        # 添加备注
        note = EventNote(
            event_id=event1.id,
            content="最近换了新的洗衣液，可能是过敏原",
            is_important=True
        )
        db.add(note)
        
        db.commit()
        print("Successfully created 3 medical events with attachments and notes!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_medical_events()
