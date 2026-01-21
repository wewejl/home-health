#!/bin/bash
# 数据部署脚本 - 在服务器上运行
# 使用方法: bash deploy_data.sh

set -e

echo "========================================="
echo "  医疗数据部署脚本"
echo "========================================="

# 项目路径
PROJECT_DIR="$HOME/home-health"
cd "$PROJECT_DIR" || exit 1

echo "当前目录: $(pwd)"

# 1. 拉取最新代码
echo ""
echo "步骤 1: 拉取最新代码..."
git pull origin main

# 2. 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    echo "激活 venv 虚拟环境..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "激活 .venv 虚拟环境..."
    source .venv/bin/activate
fi

# 3. 安装依赖
echo ""
echo "步骤 2: 安装/更新依赖..."
pip install -r requirements.txt --quiet

# 4. 添加 source 字段（如果不存在）
echo ""
echo "步骤 3: 更新数据库结构..."
python3 migrations/add_disease_source_field.py

# 5. 导入疾病数据
echo ""
echo "步骤 4: 导入疾病数据..."
python3 -c "
import sys
import csv
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.department import Department

db = SessionLocal()

# 获取或创建科室
dept_map = {}
for name in ['内科', '外科', '儿科', '妇产科', '五官科', '皮肤科', '肿瘤科', '急诊科']:
    dept = db.query(Department).filter(Department.name == name).first()
    if not dept:
        dept = Department(name=name, description=name)
        db.add(dept)
        db.commit()
    dept_map[name] = dept.id

# 导入疾病
with open('backend/data/diseases.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    created = 0
    updated = 0

    for row in reader:
        name = row.get('name', '').strip()
        if not name:
            continue

        existing = db.query(Disease).filter(Disease.name == name).first()

        if existing:
            # 更新
            existing.overview = row.get('overview', '')
            existing.symptoms = row.get('symptoms', '')
            existing.causes = row.get('causes', '')
            existing.diagnosis = row.get('diagnosis', '')
            existing.treatment = row.get('treatment', '')
            existing.prevention = row.get('prevention', '')
            existing.care = row.get('care', '')
            existing.source = row.get('source', '')
            existing.recommended_department = row.get('recommended_department', '')
            updated += 1
        else:
            # 新增
            dept_id = dept_map.get('内科', 1)
            disease = Disease(
                name=name,
                pinyin=row.get('pinyin', ''),
                aliases=row.get('aliases', ''),
                department_id=dept_id,
                recommended_department=row.get('recommended_department', ''),
                overview=row.get('overview', ''),
                symptoms=row.get('symptoms', ''),
                causes=row.get('causes', ''),
                diagnosis=row.get('diagnosis', ''),
                treatment=row.get('treatment', ''),
                prevention=row.get('prevention', ''),
                care=row.get('care', ''),
                source=row.get('source', ''),
                is_hot=row.get('is_hot', 'False') == 'True',
                is_active=row.get('is_active', 'True') == 'True'
            )
            db.add(disease)
            created += 1

        if (created + updated) % 100 == 0:
            db.commit()

    db.commit()
    print(f'疾病导入完成: 新增 {created} 条, 更新 {updated} 条')

db.close()
"

# 6. 导入药品数据
echo ""
echo "步骤 5: 导入药品数据..."
python3 -c "
import sys
import csv
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.drug import Drug, DrugCategory

db = SessionLocal()

# 获取或创建默认分类
default_category = db.query(DrugCategory).first()
if not default_category:
    default_category = DrugCategory(name='默认分类')
    db.add(default_category)
    db.commit()

# 导入药品
with open('backend/data/drugs.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    created = 0
    updated = 0

    for row in reader:
        name = row.get('name', '').strip()
        if not name:
            continue

        existing = db.query(Drug).filter(Drug.name == name).first()

        if existing:
            existing.indications = row.get('indications', '')
            existing.contraindications = row.get('contraindications', '')
            existing.dosage = row.get('dosage', '')
            existing.side_effects = row.get('side_effects', '')
            existing.precautions = row.get('precautions', '')
            existing.storage = row.get('storage', '')
            existing.pregnancy_level = row.get('pregnancy_level', '')
            existing.pregnancy_desc = row.get('pregnancy_desc', '')
            existing.lactation_level = row.get('lactation_level', '')
            existing.lactation_desc = row.get('lactation_desc', '')
            existing.children_usable = row.get('children_usable', 'True') == 'True'
            existing.children_desc = row.get('children_desc', '')
            updated += 1
        else:
            drug = Drug(
                name=name,
                pinyin=row.get('pinyin', ''),
                aliases=row.get('aliases', ''),
                common_brands=row.get('common_brands', ''),
                indications=row.get('indications', ''),
                contraindications=row.get('contraindications', ''),
                dosage=row.get('dosage', ''),
                side_effects=row.get('side_effects', ''),
                precautions=row.get('precautions', ''),
                storage=row.get('storage', ''),
                pregnancy_level=row.get('pregnancy_level', ''),
                pregnancy_desc=row.get('pregnancy_desc', ''),
                lactation_level=row.get('lactation_level', ''),
                lactation_desc=row.get('lactation_desc', ''),
                children_usable=row.get('children_usable', 'True') == 'True',
                children_desc=row.get('children_desc', ''),
                is_hot=row.get('is_hot', 'False') == 'True',
                is_active=row.get('is_active', 'True') == 'True',
                categories=[default_category]
            )
            db.add(drug)
            created += 1

        if (created + updated) % 100 == 0:
            db.commit()

    db.commit()
    print(f'药品导入完成: 新增 {created} 条, 更新 {updated} 条')

db.close()
"

# 7. 验证数据
echo ""
echo "步骤 6: 验证数据..."
python3 -c "
import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.drug import Drug

db = SessionLocal()
diseases = db.query(Disease).count()
drugs = db.query(Drug).count()

print(f'✓ 疾病: {diseases} 条')
print(f'✓ 药品: {drugs} 条')

if diseases >= 1000:
    print('✓ 疾病数据达标 (≥1000)')
else:
    print(f'⚠ 疾病数据不足，还需 {1000-diseases} 条')

if drugs >= 500:
    print('✓ 药品数据达标 (≥500)')
else:
    print(f'⚠ 药品数据不足，还需 {500-drugs} 条')

db.close()
"

echo ""
echo "========================================="
echo "  部署完成!"
echo "========================================="
