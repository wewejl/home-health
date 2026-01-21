#!/bin/bash
# 医疗数据同步脚本
# 用于快速同步本地数据到服务器

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$PROJECT_DIR/backend/data"

echo "========================================="
echo "  同步医疗数据到服务器"
echo "========================================="

# 检查本地数据文件
if [ ! -f "$DATA_DIR/diseases.csv" ]; then
    echo "错误: diseases.csv 不存在"
    exit 1
fi

if [ ! -f "$DATA_DIR/drugs.csv" ]; then
    echo "错误: drugs.csv 不存在"
    exit 1
fi

echo "本地数据:"
echo "  diseases.csv: $(wc -l < "$DATA_DIR/diseases.csv") 行"
echo "  drugs.csv: $(wc -l < "$DATA_DIR/drugs.csv") 行"

# 上传到服务器
echo ""
echo "上传数据到服务器..."
scp "$DATA_DIR/diseases.csv" home-health:~/home-health/backend/data/
scp "$DATA_DIR/drugs.csv" home-health:~/home-health/backend/data/

# 在服务器上运行导入
echo ""
echo "在服务器上导入数据..."
ssh home-health bash -s <<'ENDSSH'
cd ~/home-health/backend

sudo docker exec home-health-backend python3 -c "
import sys, csv
sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.department import Department
from app.models.drug import Drug, DrugCategory

db = SessionLocal()

# 创建科室
if db.query(Department).count() == 0:
    for name in ['内科', '外科', '儿科', '妇产科', '五官科', '皮肤科', '肿瘤科', '急诊科']:
        db.add(Department(name=name, description=name))
    db.commit()

dept_map = {d.name: d.id for d in db.query(Department).all()}
default_dept = dept_map.get('内科', 1)

# 导入疾病
print('导入疾病...')
with open('/app/data/diseases.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    created = updated = 0
    for row in reader:
        name = row.get('name', '').strip()
        if not name:
            continue
        existing = db.query(Disease).filter_by(name=name).first()
        if existing:
            existing.overview = row.get('overview', '')
            existing.symptoms = row.get('symptoms', '')
            existing.causes = row.get('causes', '')
            existing.treatment = row.get('treatment', '')
            existing.prevention = row.get('prevention', '')
            existing.care = row.get('care', '')
            updated += 1
        else:
            db.add(Disease(
                name=name,
                pinyin=row.get('pinyin', ''),
                department_id=default_dept,
                overview=row.get('overview', ''),
                symptoms=row.get('symptoms', ''),
                causes=row.get('causes', ''),
                treatment=row.get('treatment', ''),
                prevention=row.get('prevention', ''),
                care=row.get('care', ''),
                is_hot=True
            ))
            created += 1
        if (created + updated) % 500 == 0:
            db.commit()
    db.commit()
    print(f'  疾病: +{created}, 更新 {updated}')

# 导入药品
print('导入药品...')
default_cat = db.query(DrugCategory).first()
if not default_cat:
    default_cat = DrugCategory(name='默认分类')
    db.add(default_cat)
    db.commit()

with open('/app/data/drugs.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    created = updated = 0
    for row in reader:
        name = row.get('name', '').strip()
        if not name:
            continue
        existing = db.query(Drug).filter_by(name=name).first()
        if existing:
            existing.indications = row.get('indications', '')
            existing.contraindications = row.get('contraindications', '')
            existing.dosage = row.get('dosage', '')
            existing.side_effects = row.get('side_effects', '')
            existing.precautions = row.get('precautions', '')
            updated += 1
        else:
            db.add(Drug(
                name=name,
                pinyin=row.get('pinyin', ''),
                indications=row.get('indications', ''),
                contraindications=row.get('contraindications', ''),
                dosage=row.get('dosage', ''),
                side_effects=row.get('side_effects', ''),
                precautions=row.get('precautions', ''),
                categories=[default_cat]
            ))
            created += 1
        if (created + updated) % 200 == 0:
            db.commit()
    db.commit()
    print(f'  药品: +{created}, 更新 {updated}')

# 验证
d = db.query(Disease).count()
dd = db.query(Drug).count()
print(f'')
print(f'✓ 服务器数据: 疾病 {d} 条, 药品 {dd} 条')

db.close()
"
ENDSSH

echo ""
echo "✓ 同步完成!"
