-- ========== 医生工作台：添加管理的 AI 分身字段 ==========
-- 创建日期: 2026-02-09
-- 说明: 为 admin_users 表添加 managed_doctor_ids 字段，用于关联医生账号与其管理的 AI 分身
--
-- 此迁移为 admin_users 表添加：
-- 1. managed_doctor_ids - 管理的 AI 分身 ID 列表（JSONB 数组）
-- 2. 为 test_doctor 账号设置预设值

-- 1. 添加 managed_doctor_ids 字段
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS managed_doctor_ids JSONB DEFAULT '[]'::jsonb;

-- 2. 添加注释
COMMENT ON COLUMN admin_users.managed_doctor_ids IS '管理的 AI 分身 ID 列表（JSONB 数组），示例：[1, 2, 3]';

-- 3. 为 test_doctor 设置科室和 AI 分身（假设皮肤科 id=1，有 Doctor#1, #2）
-- 注意：这里使用默认值，实际部署时需要根据数据库实际情况调整
UPDATE admin_users
SET department_id = (
    SELECT id FROM departments WHERE name = '皮肤科' LIMIT 1
),
    managed_doctor_ids = (
        SELECT jsonb_agg(id)
        FROM doctors
        WHERE department_id = (SELECT id FROM departments WHERE name = '皮肤科' LIMIT 1)
    )
WHERE username = 'test_doctor';

-- 4. 验证结果
SELECT
    id,
    username,
    role,
    department_id,
    managed_doctor_ids
FROM admin_users
WHERE role = 'doctor';
