"""
删除废弃的专用会话表
- derma_sessions
- diagnosis_sessions

执行前请确保：
1. 数据已备份（如需要）
2. iOS App 使用的是统一的 sessions 表
3. 后端已删除相关路由和模型代码
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)


def drop_tables():
    """删除废弃的会话表"""
    with engine.connect() as conn:
        print("🗑️  开始删除废弃的会话表...")
        
        # 删除 diagnosis_sessions 表
        try:
            conn.execute(text("DROP TABLE IF EXISTS diagnosis_sessions CASCADE"))
            print("✅ 已删除 diagnosis_sessions 表")
        except Exception as e:
            print(f"❌ 删除 diagnosis_sessions 失败: {e}")
        
        # 删除 derma_sessions 表
        try:
            conn.execute(text("DROP TABLE IF EXISTS derma_sessions CASCADE"))
            print("✅ 已删除 derma_sessions 表")
        except Exception as e:
            print(f"❌ 删除 derma_sessions 失败: {e}")
        
        conn.commit()
        print("✅ 废弃表删除完成！")


def verify_unified_table():
    """验证统一的 sessions 表存在"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'sessions'
        """))
        count = result.fetchone()[0]
        
        if count > 0:
            print("✅ 统一的 sessions 表存在")
            
            # 显示 sessions 表的记录数
            result = conn.execute(text("SELECT COUNT(*) FROM sessions"))
            session_count = result.fetchone()[0]
            print(f"📊 sessions 表当前有 {session_count} 条记录")
        else:
            print("⚠️  警告：统一的 sessions 表不存在！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="删除废弃的专用会话表")
    parser.add_argument("--confirm", action="store_true", help="确认删除")
    parser.add_argument("--verify-only", action="store_true", help="仅验证，不删除")
    args = parser.parse_args()
    
    if args.verify_only:
        print("🔍 验证模式：检查表状态")
        verify_unified_table()
    elif args.confirm:
        print("⚠️  即将删除废弃的会话表！")
        print("   - derma_sessions")
        print("   - diagnosis_sessions")
        print()
        
        verify_unified_table()
        print()
        
        response = input("确认删除？(yes/no): ")
        if response.lower() == "yes":
            drop_tables()
        else:
            print("❌ 取消删除")
    else:
        print("使用方法:")
        print("  python -m migrations.drop_deprecated_sessions_tables --confirm  # 删除表")
        print("  python -m migrations.drop_deprecated_sessions_tables --verify-only  # 仅验证")
