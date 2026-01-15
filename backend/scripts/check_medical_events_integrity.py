"""
检查和修复 medical_events 表的数据完整性

运行方式:
cd backend
python -m scripts.check_medical_events_integrity
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.medical_event import MedicalEvent, EventStatus, RiskLevel, AgentType
from datetime import datetime

def check_and_fix_integrity():
    """检查并修复数据完整性"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    print("=" * 60)
    print("开始检查 medical_events 表数据完整性")
    print("=" * 60)
    
    try:
        # 1. 检查总记录数
        total_count = db.query(MedicalEvent).count()
        print(f"\n📊 总记录数: {total_count}")
        
        if total_count == 0:
            print("✅ 表为空，无需检查")
            return
        
        # 2. 检查枚举字段
        print("\n🔍 检查枚举字段...")
        
        valid_agent_types = [e.value for e in AgentType]
        valid_statuses = [e.value for e in EventStatus]
        valid_risk_levels = [e.value for e in RiskLevel]
        
        issues_found = []
        fixed_count = 0
        
        events = db.query(MedicalEvent).all()
        
        for event in events:
            event_issues = []
            needs_update = False
            
            # 检查 agent_type
            if event.agent_type and event.agent_type.value not in valid_agent_types:
                event_issues.append(f"无效的 agent_type: {event.agent_type}")
                event.agent_type = AgentType.GENERAL
                needs_update = True
            
            # 检查 status
            if event.status and event.status.value not in valid_statuses:
                event_issues.append(f"无效的 status: {event.status}")
                event.status = EventStatus.ACTIVE
                needs_update = True
            
            # 检查 risk_level
            if event.risk_level and event.risk_level.value not in valid_risk_levels:
                event_issues.append(f"无效的 risk_level: {event.risk_level}")
                event.risk_level = RiskLevel.LOW
                needs_update = True
            
            # 检查必填字段
            if not event.title or event.title.strip() == "":
                event_issues.append("title 为空")
                event.title = f"病历事件 {event.id}"
                needs_update = True
            
            if not event.department or event.department.strip() == "":
                event_issues.append("department 为空")
                event.department = "全科"
                needs_update = True
            
            # 检查 JSON 字段
            if event.sessions is None:
                event.sessions = []
                needs_update = True
            
            if event.ai_analysis is None:
                event.ai_analysis = {}
                needs_update = True
            
            # 检查计数字段
            if event.session_count is None:
                event.session_count = len(event.sessions) if event.sessions else 0
                needs_update = True
            
            if event.attachment_count is None:
                event.attachment_count = 0
                needs_update = True
            
            if event.export_count is None:
                event.export_count = 0
                needs_update = True
            
            if event_issues:
                issues_found.append({
                    "id": event.id,
                    "issues": event_issues
                })
                
            if needs_update:
                fixed_count += 1
        
        # 3. 显示问题
        if issues_found:
            print(f"\n⚠️  发现 {len(issues_found)} 条记录存在问题:")
            for item in issues_found[:10]:  # 只显示前10条
                print(f"\n  记录 ID: {item['id']}")
                for issue in item['issues']:
                    print(f"    - {issue}")
            
            if len(issues_found) > 10:
                print(f"\n  ... 还有 {len(issues_found) - 10} 条记录存在问题")
        else:
            print("\n✅ 所有记录的枚举字段都有效")
        
        # 4. 提交修复
        if fixed_count > 0:
            print(f"\n🔧 正在修复 {fixed_count} 条记录...")
            db.commit()
            print("✅ 修复完成")
        else:
            print("\n✅ 无需修复")
        
        # 5. 统计信息
        print("\n📈 数据统计:")
        
        # 按科室统计
        print("\n  按科室分布:")
        result = db.execute(text("""
            SELECT agent_type, COUNT(*) as count 
            FROM medical_events 
            GROUP BY agent_type 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"    {row[0]}: {row[1]}")
        
        # 按状态统计
        print("\n  按状态分布:")
        result = db.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM medical_events 
            GROUP BY status 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"    {row[0]}: {row[1]}")
        
        # 按风险等级统计
        print("\n  按风险等级分布:")
        result = db.execute(text("""
            SELECT risk_level, COUNT(*) as count 
            FROM medical_events 
            GROUP BY risk_level 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"    {row[0]}: {row[1]}")
        
        print("\n" + "=" * 60)
        print("✅ 数据完整性检查完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 检查过程中出错: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    check_and_fix_integrity()
