#!/usr/bin/env python3
"""
导入疾病详情数据
从 nuolade/disease-kb 的 medical.json 导入丰富的疾病详情
"""
import sys
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.disease import Disease
from app.models.department import Department


def load_medical_json(file_path: str) -> list:
    """加载 medical.json 数据（MongoDB export 格式）"""
    diseases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # MongoDB export 格式，每行一个 JSON 对象
            # 移除行末尾的逗号
            if line.endswith(','):
                line = line[:-1]
            try:
                data = json.loads(line)
                diseases.append(data)
            except json.JSONDecodeError as e:
                print(f"解析错误: {e}")
                continue
    return diseases


def get_or_create_department(db, dept_name: str) -> Department:
    """获取或创建科室"""
    # 常见科室映射
    dept_mapping = {
        "内科": "内科",
        "外科": "外科",
        "儿科": "儿科",
        "妇产科": "妇产科",
        "男科": "男科",
        "五官科": "耳鼻喉科",
        "耳鼻喉科": "耳鼻喉科",
        "眼科": "眼科",
        "口腔科": "口腔科",
        "皮肤性病科": "皮肤性病科",
        "性病科": "皮肤性病科",
        "肿瘤科": "肿瘤科",
        "精神科": "精神心理科",
        "心理科": "精神心理科",
        "急诊科": "急诊科",
        "麻醉科": "麻醉科",
        "康复医学科": "康复医学科",
        "中西医结合科": "中西医结合科",
        "职业病科": "职业病科",
        "地方病科": "地方病科",
        "军医科": "军医科",
        "生殖健康科": "生殖健康科",
        "医技科": "医技科",
        "其他": "其他",
    }

    # 标准化科室名称
    standard_name = dept_mapping.get(dept_name, dept_name)

    dept = db.query(Department).filter(Department.name == standard_name).first()
    if not dept:
        dept = Department(name=standard_name, description=standard_name)
        db.add(dept)
        db.commit()
    return dept


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    return text.strip()


def format_list(items: list) -> str:
    """格式化列表为字符串"""
    if not items:
        return ""
    return "、".join(items)


def import_disease_details(file_path: str, limit: int = None):
    """导入疾病详情"""
    db = SessionLocal()

    try:
        # 加载数据
        print(f"加载数据: {file_path}")
        diseases_data = load_medical_json(file_path)
        print(f"共 {len(diseases_data)} 条疾病数据")

        if limit:
            diseases_data = diseases_data[:limit]
            print(f"限制导入: {limit} 条")

        stats = {
            'total': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'error': 0
        }

        for data in diseases_data:
            stats['total'] += 1
            name = data.get('name', '').strip()
            if not name:
                stats['skipped'] += 1
                continue

            try:
                # 查找现有疾病
                existing = db.query(Disease).filter(Disease.name == name).first()

                # 获取科室
                categories = data.get('category', [])
                dept_name = "其他"
                if len(categories) >= 3:
                    dept_name = categories[2]  # 通常第三个是具体科室
                elif len(categories) >= 2:
                    dept_name = categories[1]

                department = get_or_create_department(db, dept_name)

                # 映射字段
                overview = clean_text(data.get('desc', ''))

                # 症状 - 从数组转为字符串
                symptom_list = data.get('symptom', [])
                symptoms = format_list(symptom_list) if symptom_list else ""

                # 病因
                causes = clean_text(data.get('cause', ''))

                # 预防措施
                prevention = clean_text(data.get('prevent', ''))

                # 诊断 - 从检查项目构建
                check_list = data.get('check', [])
                diagnosis = format_list(check_list) if check_list else ""

                # 治疗 - 从治疗方法构建
                cure_way_list = data.get('cure_way', [])
                treatment = format_list(cure_way_list) if cure_way_list else ""

                # 日常护理 - 从推荐食谱构建
                recommand_eat = data.get('recommand_eat', [])
                do_eat = data.get('do_eat', [])
                not_eat = data.get('not_eat', [])

                care_parts = []
                if recommand_eat:
                    care_parts.append(f"推荐食谱: {format_list(recommand_eat[:5])}")
                if do_eat:
                    care_parts.append(f"宜吃: {format_list(do_eat[:5])}")
                if not_eat:
                    care_parts.append(f"忌吃: {format_list(not_eat[:5])}")
                care = "\n".join(care_parts) if care_parts else ""

                # 其他信息
                cure_lasttime = data.get('cure_lasttime', '')
                cured_prob = data.get('cured_prob', '')
                cost_money = data.get('cost_money', '')
                get_prob = data.get('get_prob', '')

                # 补充信息到 care
                if cure_lasttime or cured_prob:
                    extra_info = []
                    if cure_lasttime:
                        extra_info.append(f"治疗周期: {cure_lasttime}")
                    if cured_prob:
                        extra_info.append(f"治愈概率: {cured_prob}")
                    if get_prob:
                        extra_info.append(f"患病概率: {get_prob}")
                    if cost_money:
                        extra_info.append(f"参考费用: {cost_money}")
                    if extra_info:
                        if care:
                            care += "\n\n" + "、".join(extra_info)
                        else:
                            care = "、".join(extra_info)

                if existing:
                    # 更新现有记录
                    updated = False
                    # 标记来源
                    if not existing.source:
                        existing.source = "medical.json"
                        updated = True
                    if not existing.overview and overview:
                        existing.overview = overview
                        updated = True
                    if not existing.symptoms and symptoms:
                        existing.symptoms = symptoms
                        updated = True
                    if not existing.causes and causes:
                        existing.causes = causes
                        updated = True
                    if not existing.diagnosis and diagnosis:
                        existing.diagnosis = diagnosis
                        updated = True
                    if not existing.treatment and treatment:
                        existing.treatment = treatment
                        updated = True
                    if not existing.prevention and prevention:
                        existing.prevention = prevention
                        updated = True
                    if not existing.care and care:
                        existing.care = care
                        updated = True
                    if not existing.recommended_department and dept_name:
                        existing.recommended_department = dept_name
                        updated = True

                    if updated:
                        stats['updated'] += 1
                        if stats['updated'] <= 10:
                            print(f"  更新: {name}")
                    else:
                        stats['skipped'] += 1
                else:
                    # 创建新记录
                    disease = Disease(
                        name=name,
                        pinyin="",  # 稍后可以生成
                        department_id=department.id,
                        recommended_department=dept_name,
                        overview=overview,
                        symptoms=symptoms,
                        causes=causes,
                        diagnosis=diagnosis,
                        treatment=treatment,
                        prevention=prevention,
                        care=care,
                        source="medical.json",  # 数据来源
                        is_hot=True,
                        is_active=True
                    )
                    db.add(disease)
                    stats['created'] += 1
                    if stats['created'] <= 10:
                        print(f"  新增: {name}")

                # 每100条提交一次
                if stats['total'] % 100 == 0:
                    db.commit()
                    print(f"进度: {stats['total']}/{len(diseases_data)}, "
                          f"新增: {stats['created']}, 更新: {stats['updated']}")

            except Exception as e:
                stats['error'] += 1
                print(f"  错误 ({name}): {e}")
                db.rollback()

        # 最终提交
        db.commit()

        print(f"\n导入完成!")
        print(f"  总计: {stats['total']}")
        print(f"  新增: {stats['created']}")
        print(f"  更新: {stats['updated']}")
        print(f"  跳过: {stats['skipped']}")
        print(f"  错误: {stats['error']}")

        # 统计数据库
        total_diseases = db.query(Disease).count()
        print(f"\n当前数据库疾病总数: {total_diseases}")

        # 检查数据完整性
        print("\n数据完整性检查:")
        print(f"  有概述: {db.query(Disease).filter(Disease.overview != '').count()}")
        print(f"  有症状: {db.query(Disease).filter(Disease.symptoms != '').count()}")
        print(f"  有病因: {db.query(Disease).filter(Disease.causes != '').count()}")
        print(f"  有治疗: {db.query(Disease).filter(Disease.treatment != '').count()}")
        print(f"  有预防: {db.query(Disease).filter(Disease.prevention != '').count()}")

    except Exception as e:
        print(f"导入失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    # 使用下载的 medical.json
    file_path = "/tmp/medical.json"

    import argparse
    parser = argparse.ArgumentParser(description='导入疾病详情数据')
    parser.add_argument('--limit', type=int, default=None, help='限制导入数量')
    parser.add_argument('--file', type=str, default=file_path, help='数据文件路径')
    args = parser.parse_args()

    import_disease_details(args.file, args.limit)


if __name__ == "__main__":
    main()
