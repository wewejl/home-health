#!/usr/bin/env python3
"""
医疗数据导入脚本
支持从 CSV/JSON 文件导入疾病和药品数据
"""

import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.drug import Drug, DrugCategory
from app.models.department import Department


class MedicalDataImporter:
    """医疗数据导入器"""

    def __init__(self, db: Session = None, default_source: str = None):
        self.db = db or SessionLocal()
        self.default_source = default_source  # 默认数据来源
        self.stats = {
            "diseases_created": 0,
            "diseases_updated": 0,
            "diseases_skipped": 0,
            "drugs_created": 0,
            "drugs_updated": 0,
            "drugs_skipped": 0,
            "errors": []
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.db:
            self.db.close()

    def _get_department_id(self, department_name: str) -> int:
        """根据科室名称获取科室 ID"""
        dept = self.db.query(Department).filter(
            Department.name == department_name
        ).first()
        if dept:
            return dept.id
        # 如果科室不存在，返回默认科室（皮肤科）
        return 1

    def import_diseases_from_csv(self, csv_path: str, encoding: str = "utf-8") -> None:
        """从 CSV 文件导入疾病数据

        CSV 格式要求：
        name, department, overview, symptoms, causes, diagnosis, treatment, prevention, care, aliases
        """
        print(f"开始从 {csv_path} 导入疾病数据...")

        with open(csv_path, "r", encoding=encoding) as f:
            reader = csv.DictReader(f)
            total = 0

            for row in reader:
                total += 1
                try:
                    self._import_disease_row(row)
                except Exception as e:
                    self.stats["errors"].append(f"行 {total}: {str(e)}")
                    self.stats["diseases_skipped"] += 1

            self.db.commit()
            print(f"疾病导入完成！处理 {total} 行，新增 {self.stats['diseases_created']} 条")

    def _import_disease_row(self, row: Dict[str, str]) -> None:
        """导入单条疾病数据"""
        name = row.get("name", "").strip()
        if not name:
            return

        # 检查是否已存在
        existing = self.db.query(Disease).filter(Disease.name == name).first()
        if existing:
            # 更新现有记录
            self._update_disease(existing, row)
            self.stats["diseases_updated"] += 1
        else:
            # 创建新记录
            disease = Disease()
            self._update_disease(disease, row)
            self.db.add(disease)
            self.stats["diseases_created"] += 1

    def _update_disease(self, disease: Disease, row: Dict[str, str]) -> None:
        """更新疾病对象"""
        disease.name = row.get("name", disease.name).strip()
        disease.aliases = row.get("aliases", disease.aliases or "").strip()
        disease.overview = row.get("overview", disease.overview or "").strip()
        disease.symptoms = row.get("symptoms", disease.symptoms or "").strip()
        disease.causes = row.get("causes", disease.causes or "").strip()
        disease.diagnosis = row.get("diagnosis", disease.diagnosis or "").strip()
        disease.treatment = row.get("treatment", disease.treatment or "").strip()
        disease.prevention = row.get("prevention", disease.prevention or "").strip()
        disease.care = row.get("care", disease.care or "").strip()

        # 科室关联
        department = row.get("department", "").strip()
        if department:
            disease.department_id = self._get_department_id(department)
            disease.recommended_department = department

        # 热门标记
        if row.get("is_hot", "").strip() == "1":
            disease.is_hot = True

        # 浏览量
        view_count = row.get("view_count", "").strip()
        if view_count.isdigit():
            disease.view_count = int(view_count)

    def import_diseases_from_json(self, json_path: str, encoding: str = "utf-8") -> None:
        """从 JSON 文件导入疾病数据

        JSON 格式：数组，每个元素包含疾病信息
        """
        print(f"开始从 {json_path} 导入疾病数据...")

        with open(json_path, "r", encoding=encoding) as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = [data]

        total = len(data)
        for item in data:
            try:
                self._import_disease_from_dict(item)
            except Exception as e:
                self.stats["errors"].append(f"{item.get('name', 'unknown')}: {str(e)}")
                self.stats["diseases_skipped"] += 1

        self.db.commit()
        print(f"疾病导入完成！处理 {total} 条，新增 {self.stats['diseases_created']} 条")

    def _import_disease_from_dict(self, item: Dict[str, Any]) -> None:
        """从字典导入单条疾病"""
        name = item.get("name", "").strip()
        if not name:
            return

        existing = self.db.query(Disease).filter(Disease.name == name).first()
        if existing:
            self._update_disease_from_dict(existing, item)
            self.stats["diseases_updated"] += 1
        else:
            disease = Disease()
            self._update_disease_from_dict(disease, item)
            self.db.add(disease)
            self.stats["diseases_created"] += 1

    def _update_disease_from_dict(self, disease: Disease, item: Dict[str, Any]) -> None:
        """从字典更新疾病对象"""
        disease.name = item.get("name", disease.name)
        disease.aliases = item.get("aliases", item.get("alias", disease.aliases or ""))
        disease.overview = item.get("overview", item.get("description", disease.overview or ""))
        disease.symptoms = item.get("symptoms", "")
        disease.causes = item.get("causes", "")
        disease.diagnosis = item.get("diagnosis", "")
        disease.treatment = item.get("treatment", "")
        disease.prevention = item.get("prevention", "")
        disease.care = item.get("care", item.get("precautions", ""))
        # 设置数据来源
        if not disease.source and self.default_source:
            disease.source = self.default_source
        # 优先使用 item 中的 source
        if item.get("source"):
            disease.source = item.get("source")

        department = item.get("department", item.get("dept", ""))
        if department:
            disease.department_id = self._get_department_id(str(department))
            disease.recommended_department = str(department)

        disease.is_hot = item.get("is_hot", False)
        disease.view_count = item.get("view_count", 0)

    def import_drugs_from_csv(self, csv_path: str, encoding: str = "utf-8") -> None:
        """从 CSV 文件导入药品数据"""
        print(f"开始从 {csv_path} 导入药品数据...")

        with open(csv_path, "r", encoding=encoding) as f:
            reader = csv.DictReader(f)
            total = 0

            for row in reader:
                total += 1
                try:
                    self._import_drug_row(row)
                except Exception as e:
                    self.stats["errors"].append(f"行 {total}: {str(e)}")
                    self.stats["drugs_skipped"] += 1

            self.db.commit()
            print(f"药品导入完成！处理 {total} 行，新增 {self.stats['drugs_created']} 条")

    def _import_drug_row(self, row: Dict[str, str]) -> None:
        """导入单条药品数据"""
        name = row.get("name", "").strip()
        if not name:
            return

        existing = self.db.query(Drug).filter(Drug.name == name).first()
        if existing:
            self._update_drug(existing, row)
            self.stats["drugs_updated"] += 1
        else:
            drug = Drug()
            self._update_drug(drug, row)
            self.db.add(drug)
            self.stats["drugs_created"] += 1

    def _update_drug(self, drug: Drug, row: Dict[str, str]) -> None:
        """更新药品对象"""
        drug.name = row.get("name", drug.name).strip()
        drug.aliases = row.get("aliases", drug.aliases or "").strip()
        drug.common_brands = row.get("common_brands", row.get("brands", "")).strip()
        drug.pregnancy_level = row.get("pregnancy_level", "").strip()
        drug.pregnancy_desc = row.get("pregnancy_desc", "").strip()
        drug.lactation_level = row.get("lactation_level", "").strip()
        drug.lactation_desc = row.get("lactation_desc", "").strip()
        drug.children_usable = row.get("children_usable", "true").lower() == "true"
        drug.children_desc = row.get("children_desc", "").strip()
        drug.indications = row.get("indications", "").strip()
        drug.contraindications = row.get("contraindications", "").strip()
        drug.dosage = row.get("dosage", "").strip()
        drug.side_effects = row.get("side_effects", "").strip()
        drug.precautions = row.get("precautions", "").strip()
        drug.storage = row.get("storage", "").strip()

        if row.get("is_hot", "1") == "1":
            drug.is_hot = True

    def import_drugs_from_json(self, json_path: str, encoding: str = "utf-8") -> None:
        """从 JSON 文件导入药品数据"""
        print(f"开始从 {json_path} 导入药品数据...")

        with open(json_path, "r", encoding=encoding) as f:
            data = json.load(f)

        if not isinstance(data, list):
            data = data.get("drugs", data.get("medicines", []))

        total = len(data)
        for item in data:
            try:
                self._import_drug_from_dict(item)
            except Exception as e:
                self.stats["errors"].append(f"{item.get('name', 'unknown')}: {str(e)}")
                self.stats["drugs_skipped"] += 1

        self.db.commit()
        print(f"药品导入完成！处理 {total} 条，新增 {self.stats['drugs_created']} 条")

    def _import_drug_from_dict(self, item: Dict[str, Any]) -> None:
        """从字典导入单条药品"""
        name = item.get("name", "").strip()
        if not name:
            return

        existing = self.db.query(Drug).filter(Drug.name == name).first()
        if existing:
            self._update_drug_from_dict(existing, item)
            self.stats["drugs_updated"] += 1
        else:
            drug = Drug()
            self._update_drug_from_dict(drug, item)
            self.db.add(drug)
            self.stats["drugs_created"] += 1

    def _update_drug_from_dict(self, drug: Drug, item: Dict[str, Any]) -> None:
        """从字典更新药品对象"""
        drug.name = item.get("name", "")
        drug.aliases = item.get("aliases", item.get("alias", ""))
        drug.common_brands = item.get("common_brands", item.get("brands", ""))
        drug.pregnancy_level = item.get("pregnancy_level", "")
        drug.pregnancy_desc = item.get("pregnancy_desc", "")
        drug.lactation_level = item.get("lactation_level", "")
        drug.lactation_desc = item.get("lactation_desc", "")
        drug.children_usable = item.get("children_usable", True)
        drug.children_desc = item.get("children_desc", "")
        drug.indications = item.get("indications", item.get("effects", ""))
        drug.contraindications = item.get("contraindications", "")
        drug.dosage = item.get("dosage", item.get("usage", ""))
        drug.side_effects = item.get("side_effects", item.get("adverse_reactions", ""))
        drug.precautions = item.get("precautions", item.get("notes", ""))
        drug.storage = item.get("storage", "")
        drug.is_hot = item.get("is_hot", False)

    def print_stats(self) -> None:
        """打印导入统计"""
        print("\n=== 导入统计 ===")
        print(f"疾病新增: {self.stats['diseases_created']} 条")
        print(f"疾病更新: {self.stats['diseases_updated']} 条")
        print(f"疾病跳过: {self.stats['diseases_skipped']} 条")
        print(f"药品新增: {self.stats['drugs_created']} 条")
        print(f"药品更新: {self.stats['drugs_updated']} 条")
        print(f"药品跳过: {self.stats['drugs_skipped']} 条")
        print(f"错误数量: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\n=== 错误详情（前10条）===")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")

    def check_current_data(self) -> None:
        """检查当前数据库中的数据量"""
        disease_count = self.db.query(Disease).count()
        drug_count = self.db.query(Drug).count()
        print(f"\n=== 当前数据量 ===")
        print(f"疾病: {disease_count} 条")
        print(f"药品: {drug_count} 条")


def main():
    parser = argparse.ArgumentParser(description="导入医疗数据")
    parser.add_argument("--diseases-csv", help="疾病 CSV 文件路径")
    parser.add_argument("--diseases-json", help="疾病 JSON 文件路径")
    parser.add_argument("--drugs-csv", help="药品 CSV 文件路径")
    parser.add_argument("--drugs-json", help="药品 JSON 文件路径")
    parser.add_argument("--check", action="store_true", help="只检查当前数据量")

    args = parser.parse_args()

    with MedicalDataImporter() as importer:
        if args.check:
            importer.check_current_data()
            return

        if args.diseases_csv:
            importer.import_diseases_from_csv(args.diseases_csv)

        if args.diseases_json:
            importer.import_diseases_from_json(args.diseases_json)

        if args.drugs_csv:
            importer.import_drugs_from_csv(args.drugs_csv)

        if args.drugs_json:
            importer.import_drugs_from_json(args.drugs_json)

        importer.print_stats()
        importer.check_current_data()


if __name__ == "__main__":
    main()
