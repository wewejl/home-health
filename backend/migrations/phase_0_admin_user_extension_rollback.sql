-- ========== Phase 0 回滚脚本 ==========
-- 创建日期: 2026-02-07
-- 说明: 回滚医生工作台 Phase 0 数据库扩展

-- ⚠️ 警告：执行此脚本将删除医生工作台 Phase 0 添加的所有字段和数据

-- 1. 删除索引
DROP INDEX IF EXISTS idx_admin_users_role;
DROP INDEX IF EXISTS idx_admin_users_department_id;

-- 2. 删除外键约束
ALTER TABLE admin_users DROP CONSTRAINT IF EXISTS fk_admin_users_department;

-- 3. 删除字段
ALTER TABLE admin_users DROP COLUMN IF EXISTS department_id;
ALTER TABLE admin_users DROP COLUMN IF EXISTS doctor_attributes;

-- 4. 删除注释
COMMENT ON COLUMN admin_users.doctor_attributes IS NULL;
COMMENT ON COLUMN admin_users.department_id IS NULL;
