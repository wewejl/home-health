"""
数据库验证脚本
运行方式: python -m scripts.verify_db
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import (
    User, Department, Doctor, Session, Message,
    AdminUser, Disease, Drug, DrugCategory
)
from sqlalchemy import text


def verify_connection():
    """验证数据库连接"""
    settings = get_settings()
    print(f"[验证] 数据库 URL: {settings.DATABASE_URL[:50]}...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[验证] ✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"[验证] ❌ 数据库连接失败: {e}")
        return False


def verify_tables():
    """验证表结构"""
    print("\n[验证] 检查表结构...")
    
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "users", "departments", "doctors", "sessions", "messages",
        "admin_users", "audit_logs", "diseases", "drugs", "drug_categories",
        "knowledge_bases", "knowledge_documents", "session_feedbacks",
        "diagnosis_sessions", "derma_sessions", "drug_category_association"
    ]
    
    missing = set(expected_tables) - set(tables)
    if missing:
        print(f"[验证] ❌ 缺少表: {missing}")
        return False
    
    print(f"[验证] ✅ 所有 {len(expected_tables)} 张表存在")
    return True


def verify_crud():
    """验证基础 CRUD 操作"""
    print("\n[验证] 测试 CRUD 操作...")
    
    db = SessionLocal()
    try:
        # READ 测试
        users = db.query(User).limit(5).all()
        print(f"  - READ User: {len(users)} 条")
        
        doctors = db.query(Doctor).limit(5).all()
        print(f"  - READ Doctor: {len(doctors)} 条")
        
        departments = db.query(Department).all()
        print(f"  - READ Department: {len(departments)} 条")
        
        # 测试关联查询
        if doctors:
            doc = doctors[0]
            dept_name = doc.department.name if doc.department else "N/A"
            print(f"  - JOIN 测试: Doctor '{doc.name}' -> Department '{dept_name}'")
        
        print("[验证] ✅ CRUD 操作正常")
        return True
        
    except Exception as e:
        print(f"[验证] ❌ CRUD 操作失败: {e}")
        return False
    finally:
        db.close()


def verify_data_counts():
    """验证数据统计"""
    print("\n[验证] 数据统计:")
    
    db = SessionLocal()
    try:
        counts = {
            "users": db.query(User).count(),
            "doctors": db.query(Doctor).count(),
            "departments": db.query(Department).count(),
            "diseases": db.query(Disease).count(),
            "drugs": db.query(Drug).count(),
            "sessions": db.query(Session).count(),
            "messages": db.query(Message).count(),
        }
        
        for table, count in counts.items():
            print(f"  - {table}: {count} 条")
        
        return True
    except Exception as e:
        print(f"[验证] ❌ 统计失败: {e}")
        return False
    finally:
        db.close()


def main():
    print("=" * 50)
    print("  灵犀医生 - 数据库验证工具")
    print("=" * 50)
    
    results = []
    results.append(("连接测试", verify_connection()))
    results.append(("表结构", verify_tables()))
    results.append(("CRUD 操作", verify_crud()))
    results.append(("数据统计", verify_data_counts()))
    
    print("\n" + "=" * 50)
    print("验证结果汇总:")
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("\n🎉 所有验证通过！数据库运行正常。")
        return 0
    else:
        print("\n⚠️  部分验证失败，请检查配置。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
