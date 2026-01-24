# 数据库迁移 v1：SQLite → PostgreSQL

**项目**: 灵犀医生  
**日期**: 2026-01-12  
**版本**: v1.0  

---

## 1. 迁移概述

| 项目 | 内容 |
|------|------|
| 源数据库 | SQLite 3 (`app.db`) |
| 目标数据库 | PostgreSQL 17 |
| 迁移表数量 | 16 张 |
| 迁移数据量 | 约 120 条记录 |
| 迁移耗时 | < 1 分钟 |

---

## 2. PostgreSQL 配置

### 2.1 安装
```bash
brew install postgresql@17
brew services start postgresql@17
```

### 2.2 数据库与用户
```sql
-- 创建用户
CREATE USER xinlin_prod WITH PASSWORD 'wszxy123';

-- 创建数据库
CREATE DATABASE xinlin_prod OWNER xinlin_prod;
```

### 2.3 连接信息
| 参数 | 值 |
|------|------|
| Host | localhost |
| Port | 5432 |
| Database | xinlin_prod |
| User | xinlin_prod |
| Password | wszxy123 |

---

## 3. 迁移过程

### 3.1 表结构
共 16 张表，按外键依赖顺序迁移：

1. `departments` - 科室
2. `users` - 用户
3. `admin_users` - 管理员
4. `doctors` - 医生
5. `drug_categories` - 药品分类
6. `drugs` - 药品
7. `drug_category_association` - 药品-分类关联
8. `diseases` - 疾病
9. `knowledge_bases` - 知识库
10. `knowledge_documents` - 知识文档
11. `sessions` - 会话
12. `messages` - 消息
13. `session_feedbacks` - 会话反馈
14. `diagnosis_sessions` - 诊断会话
15. `derma_sessions` - 皮肤科会话
16. `audit_logs` - 审计日志

### 3.2 数据迁移结果

| 表名 | SQLite | PostgreSQL | 状态 |
|------|--------|------------|------|
| departments | 12 | 12 | ✅ |
| users | 1 | 1 | ✅ |
| admin_users | 1 | 1 | ✅ |
| doctors | 12 | 12 | ✅ |
| drug_categories | 6 | 6 | ✅ |
| drugs | 10 | 10 | ✅ |
| drug_category_association | 16 | 16 | ✅ |
| diseases | 60 | 60 | ✅ |
| sessions | 4 | 4 | ✅ |
| messages | 18 | 18 | ✅ |

---

## 4. 遇到的问题与解决

### 4.1 JSON 字段迁移失败
**问题**: sessions 表的 `agent_state` 字段（JSON 类型）迁移时报错 `cannot adapt type 'dict'`

**原因**: psycopg 需要使用 `Json` 适配器处理 JSON 数据

**解决**: 
```python
from psycopg.types.json import Json
# 将 JSON 值包装为 Json(value)
```

### 4.2 外键约束导致消息迁移失败
**问题**: messages 表因 sessions 未成功迁移，导致外键约束失败

**解决**: 先修复 sessions 迁移，再迁移 messages

---

## 5. 配置变更

### 5.1 依赖更新 (`requirements.txt`)
```diff
+ psycopg[binary]==3.1.17
```

### 5.2 环境变量 (`.env`)
```diff
- DATABASE_URL=sqlite:///./app.db
+ DATABASE_URL=postgresql+psycopg://xinlin_prod:wszxy123@localhost:5432/xinlin_prod
```

---

## 6. 验证清单

运行验证脚本：
```bash
source venv/bin/activate
python -m scripts.verify_db
```

验证项目：
- [x] 数据库连接
- [x] 16 张表结构完整
- [x] CRUD 操作正常
- [x] 外键关联查询正常
- [x] 数据计数一致

---

## 7. 回滚方案

### 7.1 自动回滚
```bash
python -m scripts.rollback_to_sqlite
```

### 7.2 手动回滚
1. 恢复 SQLite 备份：
   ```bash
   cp app.db.backup_20260112_121753 app.db
   ```

2. 修改 `.env`：
   ```
   DATABASE_URL=sqlite:///./app.db
   ```

3. 重启服务

### 7.3 备份文件位置
- SQLite 备份: `backend/app.db.backup_20260112_121753`

---

## 8. 后续优化建议

### 8.1 连接池配置
```python
# database.py 可添加连接池参数
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

### 8.2 备份方案
```bash
# 每日自动备份
pg_dump -U xinlin_prod xinlin_prod > backup_$(date +%Y%m%d).sql

# 恢复
psql -U xinlin_prod xinlin_prod < backup_20260112.sql
```

### 8.3 监控建议
- 配置 pg_stat_statements 监控慢查询
- 设置连接数告警阈值

---

## 9. 文件清单

| 文件 | 说明 |
|------|------|
| `migrations/sqlite_to_postgres.py` | 迁移脚本 |
| `scripts/verify_db.py` | 验证脚本 |
| `scripts/rollback_to_sqlite.py` | 回滚脚本 |
| `app.db.backup_*` | SQLite 备份 |

---

**迁移状态**: ✅ 完成  
**验证状态**: ✅ 通过  
**服务状态**: 可正常运行
