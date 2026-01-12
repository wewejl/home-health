"""
修复 PostgreSQL 序列问题
当出现 "duplicate key value violates unique constraint" 错误时运行此脚本
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy import text

def reset_all_sequences():
    """重置所有表的序列"""
    print("开始重置 PostgreSQL 序列...")
    
    # 所有需要重置序列的表（只包含使用整数自增主键的表）
    tables_with_serial = [
        "users", 
        "departments", 
        "doctors", 
        "messages",  # 这是当前出问题的表
        "admin_users", 
        "audit_logs", 
        "session_feedbacks",
        "diseases", 
        "drugs", 
        "drug_categories", 
        "knowledge_documents"
    ]
    
    # 注意: sessions, diagnosis_sessions, derma_sessions 使用 UUID，不需要重置序列
    
    with engine.connect() as conn:
        for table in tables_with_serial:
            try:
                # 获取表中最大的 ID
                result = conn.execute(text(f"SELECT MAX(id) FROM {table}"))
                max_id = result.scalar()
                
                if max_id is not None:
                    # 重置序列到 max_id + 1
                    conn.execute(text(f"""
                        SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                               {max_id}, true)
                    """))
                    print(f"✅ {table}: 序列重置到 {max_id}")
                else:
                    # 表为空，重置到 1
                    conn.execute(text(f"""
                        SELECT setval(pg_get_serial_sequence('{table}', 'id'), 
                               1, false)
                    """))
                    print(f"✅ {table}: 序列重置到 1 (表为空)")
                    
            except Exception as e:
                print(f"❌ {table}: 重置失败 - {e}")
        
        conn.commit()
    
    print("\n序列重置完成！")

if __name__ == "__main__":
    reset_all_sequences()
