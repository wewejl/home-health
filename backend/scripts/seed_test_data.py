#!/usr/bin/env python3
"""
测试数据种子脚本

用于开发/测试环境，添加：
- 测试医生账号
- 测试患者数据
- 医嘱模板示例
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date, datetime, timedelta
from app.database import SessionLocal
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.doctor_patient_relationship import DoctorPatientRelationship, RelationshipType
from app.models.medical_order import MedicalOrder, OrderType, ScheduleType, OrderStatus, OrderTemplate


def seed_test_data():
    """添加测试数据"""
    db = SessionLocal()

    try:
        print("🌱 开始添加测试数据...")

        # 1. 确保测试医生存在
        test_doctor = db.query(AdminUser).filter(
            AdminUser.username == "test_doctor"
        ).first()

        if not test_doctor:
            print("⚠️  测试医生不存在，跳过其他测试")
            return

        print(f"✅ 测试医生: {test_doctor.username} (ID: {test_doctor.id})")

        # 2. 创建测试患者
        test_patients = [
            {
                "nickname": "张三",
                "phone": "13800138001",
                "gender": "male",
                "birthday": date(1965, 5, 15),
                "is_active": True,
            },
            {
                "nickname": "李四",
                "phone": "13800138002",
                "gender": "female",
                "birthday": date(1970, 8, 20),
                "is_active": True,
            },
            {
                "nickname": "王五",
                "phone": "13800138003",
                "gender": "male",
                "birthday": date(1980, 3, 10),
                "is_active": True,
            },
        ]

        added_count = 0
        for patient_data in test_patients:
            # 检查是否已存在
            existing = db.query(User).filter(
                User.phone == patient_data["phone"]
            ).first()

            if not existing:
                patient = User(
                    nickname=patient_data["nickname"],
                    phone=patient_data["phone"],
                    gender=patient_data["gender"],
                    birthday=patient_data["birthday"],
                    is_active=True,
                    is_profile_completed=False,
                )
                db.add(patient)
                added_count += 1
                print(f"  ✅ 添加患者: {patient_data['nickname']} ({patient_data['phone']})")

        db.commit()
        print(f"✅ 添加了 {added_count} 个测试患者")

        # 3. 创建医生-患者关联
        patients = db.query(User).filter(
            User.phone.in_([p["phone"] for p in test_patients])
        ).all()

        for patient in patients:
            # 检查是否已有关联
            existing_rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == test_doctor.id,
                DoctorPatientRelationship.patient_id == patient.id,
                DoctorPatientRelationship.is_active == True
            ).first()

            if not existing_rel:
                rel = DoctorPatientRelationship(
                    doctor_id=test_doctor.id,
                    patient_id=patient.id,
                    relationship_type=RelationshipType.PRIMARY,
                    is_active=True
                )
                db.add(rel)
                print(f"  ✅ 关联医生-患者: {patient.nickname}")

        db.commit()
        print(f"✅ 创建了 {len(patients)} 个医生-患者关联")

        # 4. 创建医嘱模板示例
        existing_templates = db.query(OrderTemplate).filter(
            OrderTemplate.doctor_id == test_doctor.id
        ).count()

        if existing_templates == 0:
            templates = [
                {
                    "name": "高血压常用处方",
                    "description": "降压药每日一次",
                    "order_type": "medication",
                    "template_data": {
                        "basicInfo": {
                            "order_type": "medication",
                            "title": "氨氯地平口服",
                            "description": "每日一次，监测血压",
                        },
                        "scheduleData": {
                            "schedule_type": "daily",
                            "start_date": date.today().isoformat(),
                            "reminder_times": ["08:00"],
                        }
                    }
                },
                {
                    "name": "糖尿病监测",
                    "description": "每日血糖监测",
                    "order_type": "monitoring",
                    "template_data": {
                        "basicInfo": {
                            "order_type": "monitoring",
                            "title": "空腹血糖",
                            "description": "每日早上测量",
                        },
                        "scheduleData": {
                            "schedule_type": "daily",
                            "start_date": date.today().isoformat(),
                            "reminder_times": ["07:00"],
                        }
                    }
                },
            ]

            for tmpl in templates:
                template = OrderTemplate(
                    doctor_id=test_doctor.id,
                    name=tmpl["name"],
                    description=tmpl["description"],
                    order_type=OrderType(tmpl["order_type"]),
                    template_data=tmpl["template_data"],
                    is_active=True,
                    is_system=False,
                )
                db.add(template)

            db.commit()
            print(f"✅ 创建了 {len(templates)} 个医嘱模板")

        print("\n✅ 测试数据添加完成！")
        print("\n📋 可用的测试账号：")
        print(f"  医生: test_doctor / 123456")
        print(f"  患者: {[p['phone'] for p in test_patients]}")

    except Exception as e:
        print(f"❌ 添加测试数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
