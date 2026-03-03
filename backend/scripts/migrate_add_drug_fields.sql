-- 药品表字段扩展迁移
-- 添加 Excel 导入所需的新字段

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS barcode VARCHAR(50);
CREATE INDEX IF NOT EXISTS ix_drugs_barcode ON drugs(barcode);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS approval_number VARCHAR(50);
CREATE INDEX IF NOT EXISTS ix_drugs_approval_number ON drugs(approval_number);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS specification VARCHAR(100);
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS dosage_form VARCHAR(50);
CREATE INDEX IF NOT EXISTS ix_drugs_dosage_form ON drugs(dosage_form);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS package_unit VARCHAR(20);
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS prescription_type VARCHAR(20);
CREATE INDEX IF NOT EXISTS ix_drugs_prescription_type ON drugs(prescription_type);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS drug_nature VARCHAR(20);
CREATE INDEX IF NOT EXISTS ix_drugs_drug_nature ON drugs(drug_nature);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS ingredients TEXT;
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS appearance TEXT;
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(200);
CREATE INDEX IF NOT EXISTS ix_drugs_manufacturer ON drugs(manufacturer);

ALTER TABLE drugs ADD COLUMN IF NOT EXISTS origin VARCHAR(100);
ALTER TABLE drugs ADD COLUMN IF NOT EXISTS standard_code VARCHAR(50);

COMMENT ON COLUMN drugs.barcode IS '商品条码';
COMMENT ON COLUMN drugs.approval_number IS '批准文号，如国药准字H13023351';
COMMENT ON COLUMN drugs.specification IS '规格，如10mg*12片';
COMMENT ON COLUMN drugs.dosage_form IS '剂型，如片剂、胶囊剂';
COMMENT ON COLUMN drugs.package_unit IS '包装单位，如盒、袋、支';
COMMENT ON COLUMN drugs.prescription_type IS '处方类型：处方药/非处方药';
COMMENT ON COLUMN drugs.drug_nature IS '性质分类：西药/中成药';
COMMENT ON COLUMN drugs.ingredients IS '主要成分';
COMMENT ON COLUMN drugs.appearance IS '性状';
COMMENT ON COLUMN drugs.manufacturer IS '生产厂家';
COMMENT ON COLUMN drugs.origin IS '产地';
COMMENT ON COLUMN drugs.standard_code IS '本位码';
