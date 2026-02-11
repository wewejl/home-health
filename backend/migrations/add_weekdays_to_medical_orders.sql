-- 添加 weekdays 字段到 medical_orders 表
-- 用于支持每周调度类型的医嘱

ALTER TABLE medical_orders 
ADD COLUMN IF NOT EXISTS weekdays JSONB DEFAULT '[]'::jsonb;

-- 添加注释
COMMENT ON COLUMN medical_orders.weekdays IS '每周调度：星期几 [0-6]，0=周日，1=周一，...，6=周六';

-- 创建索引以提高查询效率
CREATE INDEX IF NOT EXISTS idx_medical_orders_schedule_type 
ON medical_orders(schedule_type) 
WHERE status = 'active';
