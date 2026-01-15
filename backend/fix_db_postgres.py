"""
修复 PostgreSQL 数据库中的 medical_events 表
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

def fix_database():
    print("=" * 60)
    print("开始修复 medical_events 表数据")
    print("=" * 60)
    
    with engine.connect() as conn:
        # 1. 检查总记录数
        result = conn.execute(text("SELECT COUNT(*) FROM medical_events"))
        total = result.scalar()
        print(f"\n📊 总记录数: {total}")
        
        if total == 0:
            print("✅ 表为空，无需修复")
            return
        
        # 2. 修复无效的 agent_type
        print("\n🔧 修复无效的 agent_type...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET agent_type = 'general' 
            WHERE agent_type NOT IN ('cardio', 'derma', 'ortho', 'neuro', 'general', 'endo', 'gastro', 'respiratory')
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 3. 修复无效的 status
        print("\n🔧 修复无效的 status...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET status = 'active' 
            WHERE status NOT IN ('active', 'completed', 'exported', 'archived')
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 4. 修复无效的 risk_level
        print("\n🔧 修复无效的 risk_level...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET risk_level = 'low' 
            WHERE risk_level NOT IN ('low', 'medium', 'high', 'emergency')
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 5. 修复空的 title
        print("\n🔧 修复空的 title...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET title = '病历事件 ' || id 
            WHERE title IS NULL OR title = ''
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 6. 修复空的 department
        print("\n🔧 修复空的 department...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET department = '全科' 
            WHERE department IS NULL OR department = ''
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 7. 修复 NULL 的 JSON 字段
        print("\n🔧 修复 NULL 的 sessions 字段...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET sessions = '[]'::jsonb 
            WHERE sessions IS NULL
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        print("\n🔧 修复 NULL 的 ai_analysis 字段...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET ai_analysis = '{}'::jsonb 
            WHERE ai_analysis IS NULL
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 8. 修复计数字段
        print("\n🔧 修复 session_count...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET session_count = 0 
            WHERE session_count IS NULL
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        print("\n🔧 修复 attachment_count...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET attachment_count = 0 
            WHERE attachment_count IS NULL
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        print("\n🔧 修复 export_count...")
        result = conn.execute(text("""
            UPDATE medical_events 
            SET export_count = 0 
            WHERE export_count IS NULL
        """))
        print(f"   修复了 {result.rowcount} 条记录")
        
        # 提交更改
        conn.commit()
        print("\n✅ 所有修复已提交")
        
        # 9. 显示修复后的统计
        print("\n" + "=" * 60)
        print("📈 修复后的数据统计")
        print("=" * 60)
        
        print("\n按科室分布:")
        result = conn.execute(text("""
            SELECT agent_type, COUNT(*) as count 
            FROM medical_events 
            GROUP BY agent_type 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n按状态分布:")
        result = conn.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM medical_events 
            GROUP BY status 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n按风险等级分布:")
        result = conn.execute(text("""
            SELECT risk_level, COUNT(*) as count 
            FROM medical_events 
            GROUP BY risk_level 
            ORDER BY count DESC
        """))
        for row in result:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n" + "=" * 60)
        print("✅ 数据库修复完成")
        print("=" * 60)

if __name__ == "__main__":
    try:
        fix_database()
    except Exception as e:
        print(f"\n❌ 修复过程中出错: {e}")
        import traceback
        traceback.print_exc()
