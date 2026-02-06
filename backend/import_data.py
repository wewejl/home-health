#!/usr/bin/env python3
"""
从生产服务器导入数据到本地 SQLite 数据库
"""
import sqlite3
import requests
import json
from datetime import datetime
import os

# 生产 API 配置
PROD_API_BASE = "http://123.206.232.231/api"
LOCAL_DB_PATH = "./app.db"

def create_connection():
    """创建数据库连接"""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def import_departments():
    """导入科室数据"""
    print("导入科室数据...")
    try:
        response = requests.get(f"{PROD_API_BASE}/departments", timeout=30)
        response.raise_for_status()
        departments = response.json()

        conn = create_connection()
        cursor = conn.cursor()

        # 清空现有数据
        cursor.execute("DELETE FROM departments")

        for dept in departments:
            cursor.execute("""
                INSERT OR REPLACE INTO departments (id, name, description, icon, sort_order, is_primary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                dept['id'],
                dept['name'],
                dept.get('description'),
                dept.get('icon'),
                dept.get('sort_order', 0),
                dept.get('is_primary', False)
            ))

        conn.commit()
        conn.close()
        print(f"✓ 导入 {len(departments)} 个科室")
        return len(departments)
    except Exception as e:
        print(f"✗ 导入科室失败: {e}")
        return 0

def import_diseases():
    """导入疾病数据"""
    print("导入疾病数据...")
    try:
        response = requests.get(f"{PROD_API_BASE}/diseases", timeout=60)
        response.raise_for_status()
        diseases = response.json()

        conn = create_connection()
        cursor = conn.cursor()

        # 清空现有数据
        cursor.execute("DELETE FROM diseases")

        for disease in diseases:
            cursor.execute("""
                INSERT OR REPLACE INTO diseases (
                    id, name, department_id, category, description,
                    symptoms, causes, diagnosis, treatment, prevention,
                    wiki_id, medlive_content, tags, is_hot
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                disease['id'],
                disease['name'],
                disease.get('department_id'),
                disease.get('category'),
                disease.get('description'),
                disease.get('symptoms'),
                disease.get('causes'),
                disease.get('diagnosis'),
                disease.get('treatment'),
                disease.get('prevention'),
                disease.get('wiki_id'),
                disease.get('medlive_content'),
                json.dumps(disease.get('tags', [])),
                disease.get('is_hot', False)
            ))

        conn.commit()
        conn.close()
        print(f"✓ 导入 {len(diseases)} 个疾病")
        return len(diseases)
    except Exception as e:
        print(f"✗ 导入疾病失败: {e}")
        return 0

def import_drugs():
    """导入药物数据"""
    print("导入药物数据...")
    try:
        response = requests.get(f"{PROD_API_BASE}/drugs/categories", timeout=60)
        response.raise_for_status()
        categories = response.json()

        conn = create_connection()
        cursor = conn.cursor()

        # 清空现有数据
        cursor.execute("DELETE FROM drug_categories")
        cursor.execute("DELETE FROM drugs")

        for category in categories:
            cursor.execute("""
                INSERT OR REPLACE INTO drug_categories (id, name, description)
                VALUES (?, ?, ?)
            """, (
                category['id'],
                category['name'],
                category.get('description')
            ))

            # 获取该分类下的药物
            try:
                drugs_response = requests.get(f"{PROD_API_BASE}/drugs?category_id={category['id']}", timeout=60)
                drugs_response.raise_for_status()
                drugs = drugs_response.json()

                for drug in drugs:
                    cursor.execute("""
                        INSERT OR REPLACE INTO drugs (
                            id, name, category_id, generic_name, specification,
                            manufacturer, price, description, indications, dosage,
                            adverse_reactions, contraindications, precautions, is_hot
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        drug['id'],
                        drug['name'],
                        drug.get('category_id'),
                        drug.get('generic_name'),
                        drug.get('specification'),
                        drug.get('manufacturer'),
                        drug.get('price'),
                        drug.get('description'),
                        drug.get('indications'),
                        drug.get('dosage'),
                        drug.get('adverse_reactions'),
                        drug.get('contraindications'),
                        drug.get('precautions'),
                        drug.get('is_hot', False)
                    ))
            except:
                pass  # 跳过获取药物失败的情况

        conn.commit()
        conn.close()
        print(f"✓ 导入 {len(categories)} 个药物分类")
        return len(categories)
    except Exception as e:
        print(f"✗ 导入药物失败: {e}")
        return 0

def import_users():
    """导入用户数据 (仅测试用户)"""
    print("导入用户数据...")
    conn = create_connection()
    cursor = conn.cursor()

    # 确保测试用户存在
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, phone_number, verification_code, verified_at, created_at)
        VALUES (1, '13800000000', '000000', datetime('now'), datetime('now'))
    """)

    conn.commit()
    conn.close()
    print("✓ 导入测试用户")
    return 1

def main():
    print("=" * 50)
    print("从生产服务器导入数据到本地数据库")
    print("=" * 50)

    # 检查生产 API 是否可访问
    try:
        response = requests.get(f"{PROD_API_BASE}/departments", timeout=10)
        if response.status_code != 200:
            print("✗ 生产 API 不可访问")
            return
    except Exception as e:
        print(f"✗ 无法连接到生产 API: {e}")
        return

    print(f"✓ 生产 API 连接正常: {PROD_API_BASE}")
    print()

    # 导入数据
    counts = {
        'users': import_users(),
        'departments': import_departments(),
        'diseases': import_diseases(),
        'drugs': import_drugs(),
    }

    print()
    print("=" * 50)
    print("导入完成!")
    print(f"  用户: {counts['users']}")
    print(f"  科室: {counts['departments']}")
    print(f"  疾病: {counts['diseases']}")
    print(f"  药物分类: {counts['drugs']}")
    print("=" * 50)

if __name__ == "__main__":
    main()
