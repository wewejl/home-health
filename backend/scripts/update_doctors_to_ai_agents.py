#!/usr/bin/env python3
"""
数据库迁移脚本：将所有科室的医生更新为专业AI智能体
执行方式：python scripts/update_doctors_to_ai_agents.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.doctor import Doctor
from app.models.department import Department


# 各科室AI智能体配置
AI_AGENTS_CONFIG = {
    1: {  # 皮肤科
        "name": "皮肤科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "真菌性皮肤病、湿疹、痤疮、皮肤过敏、荨麻疹、银屑病、白癜风等各类皮肤疾病的智能诊断与治疗建议",
        "intro": "由多位资深皮肤科专家知识库训练的AI智能体，专注于皮肤疾病的诊断、治疗建议和健康咨询。支持皮肤影像分析和检查报告解读，为您提供专业、及时的皮肤健康管理服务。",
        "rating": 5.0,
        "monthly_answers": 1200,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "dermatology"
    },
    2: {  # 儿科
        "name": "儿科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "小儿感冒、发热、腹泻、手足口病、小儿肺炎、小儿哮喘、生长发育等儿童常见疾病的智能诊断与健康管理",
        "intro": "由多位资深儿科专家知识库训练的AI智能体，专注于儿童疾病的诊断、治疗建议和生长发育咨询。为家长提供专业、贴心的儿童健康管理服务。",
        "rating": 5.0,
        "monthly_answers": 1500,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    3: {  # 妇产科
        "name": "妇产科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "妇科炎症、月经不调、子宫肌瘤、盆腔炎、多囊卵巢综合征、孕期保健、产后康复等妇产科疾病的智能诊断与健康管理",
        "intro": "由多位资深妇产科专家知识库训练的AI智能体，专注于妇科疾病诊断、孕期保健和女性健康管理。为女性提供专业、私密的医疗咨询服务。",
        "rating": 5.0,
        "monthly_answers": 1100,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    4: {  # 消化内科
        "name": "消化内科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "胃炎、胃溃疡、肠炎、脂肪肝、胆囊炎、消化不良等消化系统疾病的智能诊断与治疗建议",
        "intro": "由多位资深消化内科专家知识库训练的AI智能体，专注于消化系统疾病的诊断、治疗建议和饮食指导。为您提供专业的消化健康管理服务。",
        "rating": 5.0,
        "monthly_answers": 980,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    5: {  # 呼吸内科
        "name": "呼吸内科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "感冒、支气管炎、肺炎、哮喘、慢性阻塞性肺疾病等呼吸系统疾病的智能诊断与治疗建议",
        "intro": "由多位资深呼吸内科专家知识库训练的AI智能体，专注于呼吸系统疾病的诊断、治疗建议和呼吸健康管理。为您提供专业的呼吸道疾病咨询服务。",
        "rating": 5.0,
        "monthly_answers": 1300,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    6: {  # 心血管内科
        "name": "心血管科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "高血压、冠心病、心律失常、心力衰竭、心肌炎等心血管疾病的智能诊断、风险评估与治疗建议",
        "intro": "由多位资深心血管专家知识库训练的AI智能体，专注于心血管疾病的诊断、风险评估和健康管理。支持心电图解读和心血管风险评估，为您提供专业的心脏健康管理服务。",
        "rating": 5.0,
        "monthly_answers": 850,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "cardiology"
    },
    7: {  # 内分泌科
        "name": "内分泌科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "糖尿病、甲状腺功能亢进症、甲状腺功能减退症、骨质疏松症、痛风等内分泌代谢疾病的智能诊断与治疗建议",
        "intro": "由多位资深内分泌科专家知识库训练的AI智能体，专注于内分泌代谢疾病的诊断、治疗建议和健康管理。为您提供专业的内分泌健康咨询服务。",
        "rating": 5.0,
        "monthly_answers": 720,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    8: {  # 神经内科
        "name": "神经内科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "头痛、失眠症、脑梗死、癫痫、帕金森病等神经系统疾病的智能诊断与治疗建议",
        "intro": "由多位资深神经内科专家知识库训练的AI智能体，专注于神经系统疾病的诊断、治疗建议和神经健康管理。为您提供专业的神经系统疾病咨询服务。",
        "rating": 5.0,
        "monthly_answers": 650,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    9: {  # 骨科
        "name": "骨科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "颈椎病、腰椎间盘突出症、骨关节炎、骨折、肩周炎等骨科疾病的智能诊断与治疗建议",
        "intro": "由多位资深骨科专家知识库训练的AI智能体，专注于骨科疾病的诊断、治疗建议和康复指导。支持X光片解读，为您提供专业的骨骼健康管理服务。",
        "rating": 5.0,
        "monthly_answers": 890,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "orthopedics"
    },
    10: {  # 眼科
        "name": "眼科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "近视、白内障、青光眼、干眼症、结膜炎等眼科疾病的智能诊断与治疗建议",
        "intro": "由多位资深眼科专家知识库训练的AI智能体，专注于眼科疾病的诊断、治疗建议和视力健康管理。为您提供专业的眼部健康咨询服务。",
        "rating": 5.0,
        "monthly_answers": 760,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    11: {  # 耳鼻咽喉科
        "name": "耳鼻咽喉科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "鼻炎、咽喉炎、中耳炎、鼻窦炎、扁桃体炎等耳鼻咽喉疾病的智能诊断与治疗建议",
        "intro": "由多位资深耳鼻咽喉科专家知识库训练的AI智能体，专注于耳鼻咽喉疾病的诊断、治疗建议和健康管理。为您提供专业的耳鼻喉健康咨询服务。",
        "rating": 5.0,
        "monthly_answers": 680,
        "avg_response_time": "即时响应",
        "can_prescribe": True,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    },
    12: {  # 口腔科
        "name": "口腔科AI智能体",
        "title": "AI专家团队",
        "hospital": "心灵医生AI智能诊疗平台",
        "specialty": "龋齿、牙周炎、口腔溃疡、智齿冠周炎、牙髓炎等口腔疾病的智能诊断与治疗建议",
        "intro": "由多位资深口腔科专家知识库训练的AI智能体，专注于口腔疾病的诊断、治疗建议和口腔健康管理。为您提供专业的口腔健康咨询服务。",
        "rating": 4.9,
        "monthly_answers": 580,
        "avg_response_time": "即时响应",
        "can_prescribe": False,
        "is_top_hospital": True,
        "is_ai": True,
        "is_active": True,
        "ai_model": "qwen-plus",
        "ai_temperature": 0.7,
        "agent_type": "general"
    }
}


def update_doctors_to_ai_agents():
    """更新所有科室的医生为专业AI智能体"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("开始更新医生数据为AI智能体...")
        print("=" * 60)
        
        # 获取所有科室
        departments = db.query(Department).all()
        print(f"\n找到 {len(departments)} 个科室")
        
        updated_count = 0
        
        for dept in departments:
            if dept.id not in AI_AGENTS_CONFIG:
                print(f"⚠️  科室 [{dept.name}] (ID: {dept.id}) 没有配置AI智能体，跳过")
                continue
            
            # 获取该科室的医生
            doctors = db.query(Doctor).filter(Doctor.department_id == dept.id).all()
            
            if not doctors:
                print(f"⚠️  科室 [{dept.name}] 没有医生，跳过")
                continue
            
            # 获取AI智能体配置
            ai_config = AI_AGENTS_CONFIG[dept.id]
            
            # 更新第一个医生为AI智能体，删除其他医生
            for idx, doctor in enumerate(doctors):
                if idx == 0:
                    # 更新第一个医生
                    print(f"\n✅ 更新科室 [{dept.name}] 的医生:")
                    print(f"   原医生: {doctor.name} ({doctor.title})")
                    
                    for key, value in ai_config.items():
                        setattr(doctor, key, value)
                    
                    print(f"   新医生: {doctor.name} ({doctor.title})")
                    print(f"   专长: {doctor.specialty[:50]}...")
                    updated_count += 1
                else:
                    # 删除其他医生
                    print(f"   删除多余医生: {doctor.name}")
                    db.delete(doctor)
        
        # 提交更改
        db.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ 更新完成！共更新 {updated_count} 个科室的医生为AI智能体")
        print("=" * 60)
        
        # 显示更新后的医生列表
        print("\n更新后的医生列表:")
        print("-" * 60)
        all_doctors = db.query(Doctor).order_by(Doctor.department_id).all()
        for doctor in all_doctors:
            dept = db.query(Department).filter(Department.id == doctor.department_id).first()
            print(f"[{dept.name}] {doctor.name} - {doctor.title}")
            print(f"  专长: {doctor.specialty[:60]}...")
            print(f"  智能体类型: {doctor.agent_type}")
            print()
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 更新失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_doctors_to_ai_agents()
