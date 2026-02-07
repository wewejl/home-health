-- ========== Phase 0: AdminUser 模型扩展 ==========
-- 创建日期: 2026-02-07
-- 说明: 为医生工作台功能添加必要的字段
--
-- 此迁移为 admin_users 表添加：
-- 1. doctor_attributes - 医生专属属性（JSONB）
-- 2. department_id - 科室关联（外键到 departments）
-- 3. 相关索引和约束

-- 1. 添加 doctor_attributes 字段（医生专属信息）
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS doctor_attributes JSONB;

-- 2. 添加 department_id 字段（科室关联）
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS department_id INTEGER;

-- 3. 添加外键约束
ALTER TABLE admin_users
ADD CONSTRAINT fk_admin_users_department
FOREIGN KEY (department_id)
REFERENCES departments(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- 4. 创建索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_admin_users_department_id
ON admin_users(department_id);

CREATE INDEX IF NOT EXISTS idx_admin_users_role
ON admin_users(role);

-- 5. 添加注释
COMMENT ON COLUMN admin_users.doctor_attributes IS '医生专属属性（JSON）：职称、专科、执业证号、医院等';
COMMENT ON COLUMN admin_users.department_id IS '科室ID，医生角色用于关联本科室的AI分身';
