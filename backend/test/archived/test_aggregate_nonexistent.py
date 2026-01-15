#!/usr/bin/env python
"""
测试不存在的会话ID - 应该创建通用会话数据而不是返回404
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.medical_event import MedicalEvent
from app.routes.medical_events import aggregate_session
from app.schemas.medical_event import AggregateSessionRequest
import uuid

def test_nonexistent_session():
    db = SessionLocal()
    
    try:
        # 获取一个用户
        user = db.query(User).first()
        if not user:
            print("❌ 没有用户")
            return
        
        print(f"✅ 找到用户: {user.phone}")
        
        # 使用一个不存在的会话ID
        fake_session_id = str(uuid.uuid4())
        
        request = AggregateSessionRequest(
            session_id=fake_session_id,
            session_type="dermatology"
        )
        
        print(f"\n📤 测试不存在的会话:")
        print(f"   session_id: {request.session_id}")
        print(f"   session_type: {request.session_type}")
        
        try:
            result = aggregate_session(request, user, db)
            print(f"\n✅ 聚合成功! (即使会话不存在)")
            print(f"   event_id: {result.event_id}")
            print(f"   is_new_event: {result.is_new_event}")
            print(f"   message: {result.message}")
            
            # 检查数据库中的事件
            event = db.query(MedicalEvent).filter(MedicalEvent.id == int(result.event_id)).first()
            if event:
                print(f"\n📊 病历事件详情:")
                print(f"   标题: {event.title}")
                print(f"   科室: {event.department}")
                print(f"   智能体类型: {event.agent_type}")
                print(f"   会话数: {event.session_count}")
                print(f"   会话列表: {event.sessions}")
        except Exception as e:
            print(f"\n❌ 聚合失败: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    test_nonexistent_session()
