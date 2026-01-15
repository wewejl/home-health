#!/usr/bin/env python
"""
测试 medical-events/aggregate 接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.derma_session import DermaSession
from app.models.user import User
from app.models.medical_event import MedicalEvent
import requests

def test_aggregate():
    db = SessionLocal()
    
    try:
        # 1. 获取一个现有的皮肤科会话
        session = db.query(DermaSession).first()
        if not session:
            print("❌ 没有找到皮肤科会话")
            return
        
        print(f"✅ 找到会话: {session.id}")
        print(f"   用户ID: {session.user_id}")
        print(f"   阶段: {session.stage}")
        
        # 2. 获取用户
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            print("❌ 用户不存在")
            return
        
        print(f"✅ 找到用户: {user.phone}")
        
        # 3. 生成token (简化版，实际应该用正确的JWT)
        # 由于我们不知道JWT的密钥，我们直接测试endpoint的逻辑
        from app.routes.medical_events import aggregate_session
        from app.schemas.medical_event import AggregateSessionRequest
        
        # 模拟请求
        request = AggregateSessionRequest(
            session_id=session.id,
            session_type="dermatology"
        )
        
        print(f"\n📤 测试请求:")
        print(f"   session_id: {request.session_id}")
        print(f"   session_type: {request.session_type}")
        
        # 直接调用函数测试
        try:
            result = aggregate_session(request, user, db)
            print(f"\n✅ 聚合成功!")
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
                print(f"   状态: {event.status}")
                print(f"   会话数: {event.session_count}")
        except Exception as e:
            print(f"\n❌ 聚合失败: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    test_aggregate()
