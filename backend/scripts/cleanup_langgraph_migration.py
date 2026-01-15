"""
清理数据库旧数据 - LangGraph 迁移

删除所有旧的会话数据，因为状态结构已变更
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import SessionLocal, engine


def cleanup_old_sessions():
    """清理所有旧会话数据"""
    db = SessionLocal()
    
    try:
        print("🗑️  开始清理旧会话数据...")
        
        # 1. 删除所有消息
        result = db.execute(text("DELETE FROM messages"))
        message_count = result.rowcount
        print(f"   ✅ 删除 {message_count} 条消息")
        
        # 2. 删除所有会话
        result = db.execute(text("DELETE FROM sessions"))
        session_count = result.rowcount
        print(f"   ✅ 删除 {session_count} 个会话")
        
        # 3. 删除所有会话反馈
        result = db.execute(text("DELETE FROM session_feedbacks"))
        feedback_count = result.rowcount
        print(f"   ✅ 删除 {feedback_count} 条反馈")
        
        # 4. 可选：删除旧的皮肤科会话表（如果存在）
        try:
            result = db.execute(text("DELETE FROM derma_sessions"))
            derma_count = result.rowcount
            print(f"   ✅ 删除 {derma_count} 个旧皮肤科会话")
        except Exception:
            print(f"   ℹ️  derma_sessions 表不存在或已清空")
        
        # 5. 可选：删除旧的诊断会话表（如果存在）
        try:
            result = db.execute(text("DELETE FROM diagnosis_sessions"))
            diagnosis_count = result.rowcount
            print(f"   ✅ 删除 {diagnosis_count} 个旧诊断会话")
        except Exception:
            print(f"   ℹ️  diagnosis_sessions 表不存在或已清空")
        
        db.commit()
        print("\n✅ 数据清理完成！")
        print("\n📝 说明：")
        print("   - 所有旧会话和消息已删除")
        print("   - 用户数据、医生数据、病历事件数据保持不变")
        print("   - 现在可以使用新的 LangGraph 实现创建会话")
        
    except Exception as e:
        print(f"\n❌ 清理失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_cleanup():
    """验证清理结果"""
    db = SessionLocal()
    
    try:
        print("\n🔍 验证清理结果...")
        
        result = db.execute(text("SELECT COUNT(*) FROM sessions"))
        session_count = result.scalar()
        print(f"   - 剩余会话数: {session_count}")
        
        result = db.execute(text("SELECT COUNT(*) FROM messages"))
        message_count = result.scalar()
        print(f"   - 剩余消息数: {message_count}")
        
        if session_count == 0 and message_count == 0:
            print("\n✅ 验证通过：数据库已清空")
        else:
            print("\n⚠️  警告：仍有残留数据")
            
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph 迁移 - 数据库清理脚本")
    print("=" * 60)
    print("\n⚠️  警告：此操作将删除所有会话和消息数据！")
    print("   用户、医生、病历事件数据不会被删除。")
    
    confirm = input("\n确认执行清理？(yes/no): ")
    
    if confirm.lower() == "yes":
        cleanup_old_sessions()
        verify_cleanup()
    else:
        print("\n❌ 已取消清理操作")
