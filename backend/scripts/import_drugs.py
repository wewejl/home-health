#!/usr/bin/env python3
"""
药品数据导入脚本
从 CSV 文件导入药品数据到数据库
"""
import csv
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.drug import Drug, DrugCategory


def create_categories(db: Session) -> list[DrugCategory]:
    """创建药品分类"""
    categories_data = [
        {"name": "热门药品", "icon": "flame", "description": "常用热门药品", "display_type": "grid", "sort_order": 1, "is_active": True},
        {"name": "感冒发烧", "icon": "thermometer", "description": "感冒发烧相关药品", "display_type": "grid", "sort_order": 2, "is_active": True},
        {"name": "消化系统", "icon": "pills", "description": "消化系统用药", "display_type": "grid", "sort_order": 3, "is_active": True},
        {"name": "皮肤用药", "icon": "hand.raised", "description": "皮肤病用药", "display_type": "grid", "sort_order": 4, "is_active": True},
        {"name": "心脑血管", "icon": "heart", "description": "心脑血管用药", "display_type": "grid", "sort_order": 5, "is_active": True},
        {"name": "孕期/哺乳期", "icon": "figure.and.child.holdinghands", "description": "孕期哺乳期安全用药", "display_type": "grid", "sort_order": 6, "is_active": True},
        {"name": "儿童用药", "icon": "figure.child", "description": "儿童安全用药", "display_type": "grid", "sort_order": 7, "is_active": True},
    ]

    categories = []
    for data in categories_data:
        # 检查分类是否已存在
        existing = db.query(DrugCategory).filter(DrugCategory.name == data["name"]).first()
        if existing:
            categories.append(existing)
        else:
            cat = DrugCategory(**data)
            db.add(cat)
            categories.append(cat)

    db.commit()
    print(f"✓ 创建/更新了 {len(categories)} 个药品分类")
    return categories


def import_drugs_from_csv(db: Session, csv_path: str, categories: list[DrugCategory]) -> int:
    """从 CSV 文件导入药品数据"""
    if not os.path.exists(csv_path):
        print(f"✗ CSV 文件不存在: {csv_path}")
        return 0

    imported_count = 0
    skipped_count = 0

    # 分类映射（根据药品关键词自动分配分类）
    category_keywords = {
        "感冒发烧": ["感冒", "发烧", "退热", "解热", "镇痛", "布洛芬", "对乙酰", "阿司匹林", "奥司他韦", "连花", "感冒灵"],
        "消化系统": ["胃", "肠", "消化", "腹泻", "便秘", "奥美拉唑", "蒙脱石", "多潘", "莫沙", "铝碳酸"],
        "皮肤用药": ["皮肤", "湿疹", "痤疮", "皮炎", "软膏", "乳膏", "洗剂", "莫匹罗星", "炉甘石", "地奈德"],
        "心脑血管": ["血压", "心脏", "心血管", "阿司匹林", "硝苯地", "氨氯地", "美托洛", "阿托伐", "辛伐"],
    }

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        total_rows = sum(1 for _ in reader)  # 计算总行数
        f.seek(0)  # 重置文件指针
        next(reader)  # 跳过表头

        for row_num, row in enumerate(reader, 1):
            try:
                # 检查药品是否已存在
                existing = db.query(Drug).filter(Drug.name == row["name"]).first()
                if existing:
                    skipped_count += 1
                    continue

                # 解析布尔值
                is_hot = row.get("is_hot", "False").strip() in ["True", "true", "1", "yes"]
                is_active = row.get("is_active", "True").strip() in ["True", "true", "1", "yes"]
                children_usable = row.get("children_usable", "True").strip() in ["True", "true", "1", "yes"]

                # 创建药品对象
                drug = Drug(
                    name=row["name"],
                    pinyin=row.get("pinyin", ""),
                    pinyin_abbr=row.get("pinyin_abbr", ""),
                    aliases=row.get("aliases", ""),
                    common_brands=row.get("common_brands", ""),
                    pregnancy_level=row.get("pregnancy_level", ""),
                    pregnancy_desc=row.get("pregnancy_desc", ""),
                    lactation_level=row.get("lactation_level", ""),
                    lactation_desc=row.get("lactation_desc", ""),
                    children_usable=children_usable,
                    children_desc=row.get("children_desc", ""),
                    indications=row.get("indications", ""),
                    contraindications=row.get("contraindications", ""),
                    dosage=row.get("dosage", ""),
                    side_effects=row.get("side_effects", ""),
                    precautions=row.get("precautions", ""),
                    storage=row.get("storage", ""),
                    is_hot=is_hot,
                    sort_order=int(row.get("sort_order", 0)) if row.get("sort_order", "").isdigit() else 0,
                    is_active=is_active,
                    view_count=int(row.get("view_count", 0)) if row.get("view_count", "").isdigit() else 0,
                )

                db.add(drug)
                db.flush()  # 获取 drug.id

                # 自动分配分类
                drug_name = row["name"]
                for cat in categories:
                    cat_name = cat.name
                    if cat_name in category_keywords:
                        keywords = category_keywords[cat_name]
                        if any(keyword in drug_name for keyword in keywords):
                            drug.categories.append(cat)

                # 如果是热门药品，添加到热门分类
                if is_hot:
                    hot_category = next((c for c in categories if c.name == "热门药品"), None)
                    if hot_category and hot_category not in drug.categories:
                        drug.categories.append(hot_category)

                # 儿童可用药品添加到儿童用药分类
                if children_usable:
                    child_category = next((c for c in categories if c.name == "儿童用药"), None)
                    if child_category and child_category not in drug.categories:
                        drug.categories.append(child_category)

                imported_count += 1

                # 每 100 条提交一次
                if imported_count % 100 == 0:
                    db.commit()
                    print(f"  进度: {imported_count}/{total_rows}")

            except Exception as e:
                print(f"  ✗ 第 {row_num} 行导入失败: {row.get('name', 'unknown')} - {e}")
                continue

        db.commit()
        print(f"✓ 导入药品: {imported_count} 条")
        if skipped_count > 0:
            print(f"  跳过已存在: {skipped_count} 条")

        return imported_count


def main():
    """主函数"""
    print("=" * 50)
    print("药品数据导入工具")
    print("=" * 50)

    # 创建表（如果不存在）
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 1. 创建分类
        print("\n1. 创建药品分类...")
        categories = create_categories(db)

        # 2. 导入药品数据
        csv_path = os.path.join(os.path.dirname(__file__), "../data/drugs.csv")
        print(f"\n2. 从 CSV 导入药品数据: {csv_path}")
        imported = import_drugs_from_csv(db, csv_path, categories)

        # 3. 统计结果
        print("\n" + "=" * 50)
        print("导入完成！")
        print("=" * 50)
        print(f"药品分类: {db.query(DrugCategory).count()} 个")
        print(f"药品数据: {db.query(Drug).count()} 条")

    except Exception as e:
        print(f"\n✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
