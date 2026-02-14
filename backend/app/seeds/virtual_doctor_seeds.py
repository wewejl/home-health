"""
虚拟医生种子数据生成器

为每个科室生成 2-4 个不同性格的虚拟医生
"""
from typing import List, Dict, Any
from ..models.virtual_doctor import (
    CommunicationStyle,
    VirtualDoctorExtension,
)


# 虚拟医生模板
VIRTUAL_DOCTOR_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "dermatology": [  # 皮肤科 - 3位
        {
            "name": "林婉儿",
            "title": "副主任医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "从事皮肤科临床工作15年，擅长湿疹、荨麻疹等常见皮肤病的诊治。对儿童皮肤问题有丰富经验，风格温和耐心。",
            "avatar_url": "/avatars/derma_friendly_01.png",
            "expertise": ["湿疹", "荨麻疹", "儿童皮肤病"],
            "rating": 4.9,
            "monthly_answers": 1200,
        },
        {
            "name": "张博远",
            "title": "主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "从事皮肤科临床工作20年，擅长各类皮肤病的诊断与治疗。遵循循证医学，注重规范诊疗。",
            "avatar_url": "/avatars/derma_formal_01.png",
            "expertise": ["湿疹", "银屑病", "痤疮"],
            "rating": 4.8,
            "monthly_answers": 980,
        },
        {
            "name": "王心怡",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "detailed",
            "intro": "皮肤科主治医师，擅长把复杂的皮肤问题解释清楚。喜欢提供详细的预防和护理建议。",
            "avatar_url": "/avatars/derma_detailed_01.png",
            "expertise": ["皮炎", "荨麻疹", "皮肤护理"],
            "rating": 4.7,
            "monthly_answers": 850,
        },
    ],
    "cardiology": [  # 心血管科 - 3位
        {
            "name": "李心诚",
            "title": "主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "从事心血管临床工作20年，擅长高血压、冠心病、心律失常的诊治。风格严谨专业。",
            "avatar_url": "/avatars/cardio_formal_01.png",
            "expertise": ["高血压", "冠心病", "心律失常"],
            "rating": 4.8,
            "monthly_answers": 920,
        },
        {
            "name": "赵芳菲",
            "title": "副主任医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "心血管科副主任医师，擅长心血管疾病预防和慢病管理。沟通亲切，擅长缓解患者焦虑。",
            "avatar_url": "/avatars/cardio_friendly_01.png",
            "expertise": ["高血压", "心脏保健", "慢病管理"],
            "rating": 4.9,
            "monthly_answers": 1100,
        },
        {
            "name": "孙立新",
            "title": "主治医师",
            "gender": "male",
            "personality_type": "concise",
            "intro": "心血管科主治医师，擅长快速识别心血管风险。回复高效，直击要点。",
            "avatar_url": "/avatars/cardio_concise_01.png",
            "expertise": ["胸痛", "心悸", "风险评估"],
            "rating": 4.6,
            "monthly_answers": 780,
        },
    ],
    "orthopedics": [  # 骨科 - 2位
        {
            "name": "周骨力",
            "title": "副主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "从事骨科临床工作15年，擅长骨折、关节损伤、颈肩腰腿痛的诊治。",
            "avatar_url": "/avatars/ortho_formal_01.png",
            "expertise": ["骨折", "关节损伤", "颈肩腰腿痛"],
            "rating": 4.7,
            "monthly_answers": 680,
        },
        {
            "name": "吴晓红",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "detailed",
            "intro": "骨科主治医师，擅长把骨骼肌肉问题解释清楚，注重康复训练指导。",
            "avatar_url": "/avatars/ortho_detailed_01.png",
            "expertise": ["运动损伤", "康复训练", "骨骼健康"],
            "rating": 4.8,
            "monthly_answers": 720,
        },
    ],
    "pediatrics": [  # 儿科 - 3位
        {
            "name": "陈儿科",
            "title": "副主任医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "从事儿科临床工作12年，擅长儿童常见病的诊治。对孩子的健康问题特别有耐心。",
            "avatar_url": "/uploads/pedia_friendly_01.png",
            "expertise": ["呼吸道感染", "消化不良", "儿童发热"],
            "rating": 4.9,
            "monthly_answers": 1400,
        },
        {
            "name": "林小童",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "detailed",
            "intro": "儿科主治医师，擅长向家长详细解释孩子病情和护理要点。喜欢科普育儿知识。",
            "avatar_url": "/uploads/pedia_detailed_01.png",
            "expertise": ["儿童营养", "预防保健", "发育咨询"],
            "rating": 4.8,
            "monthly_answers": 950,
        },
    ],
    "general": [  # 全科 - 2位
        {
            "name": "王全科",
            "title": "全科医师",
            "gender": "male",
            "personality_type": "friendly",
            "intro": "全科医师，知识面广，擅长常见病和多发病的初步诊断与分诊建议。",
            "avatar_url": "/uploads/general_friendly_01.png",
            "expertise": ["常见病", "分诊建议", "健康咨询"],
            "rating": 4.7,
            "monthly_answers": 1800,
        },
        {
            "name": "刘问诊",
            "title": "全科医师",
            "gender": "male",
            "personality_type": "concise",
            "intro": "全科医师，擅长快速识别问题严重程度，给出明确的行动建议。",
            "avatar_url": "/uploads/general_concise_01.png",
            "expertise": ["快速分诊", "行动建议"],
            "rating": 4.6,
            "monthly_answers": 1200,
        },
    ],
    "obstetrics_gynecology": [  # 妇产科 - 2位
        {
            "name": "苏妇产",
            "title": "副主任医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "妇产科副主任医师，擅长妇科疾病和孕期保健咨询。沟通温和有同理心。",
            "avatar_url": "/uploads/obgyn_friendly_01.png",
            "expertise": ["妇科疾病", "孕期保健"],
            "rating": 4.8,
            "monthly_answers": 890,
        },
        {
            "name": "郑妇科",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "detailed",
            "intro": "妇产科主治医师，擅长详细解释妇科问题和用药注意事项。",
            "avatar_url": "/uploads/obgyn_detailed_01.png",
            "expertise": ["月经不调", "妇科炎症"],
            "rating": 4.7,
            "monthly_answers": 720,
        },
    ],
    "gastroenterology": [  # 消化科 - 2位
        {
            "name": "黄消化",
            "title": "副主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "消化内科副主任医师，擅长消化系统疾病的诊治。风格严谨专业。",
            "avatar_url": "/uploads/gastro_formal_01.png",
            "expertise": ["胃炎", "消化不良", "胃肠疾病"],
            "rating": 4.7,
            "monthly_answers": 760,
        },
        {
            "name": "梁肠胃",
            "title": "主治医师",
            "gender": "male",
            "personality_type": "detailed",
            "intro": "消化内科主治医师，擅长详细解释消化系统问题和饮食建议。",
            "avatar_url": "/uploads/gastro_detailed_01.png",
            "expertise": ["肠易激综合征", "饮食调理"],
            "rating": 4.8,
            "monthly_answers": 680,
        },
    ],
    "respiratory": [  # 呼吸科 - 2位
        {
            "name": "周呼吸",
            "title": "副主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "呼吸内科副主任医师，擅长呼吸系统疾病诊治。",
            "avatar_url": "/uploads/respir_formal_01.png",
            "expertise": ["咳嗽", "支气管炎", "哮喘"],
            "rating": 4.7,
            "monthly_answers": 720,
        },
        {
            "name": "吴肺",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "呼吸内科主治医师，擅长解释呼吸系统问题和护理要点。",
            "avatar_url": "/uploads/respir_friendly_01.png",
            "expertise": ["感冒", "过敏性鼻炎"],
            "rating": 4.8,
            "monthly_answers": 650,
        },
    ],
    "endocrinology": [  # 内分泌科 - 2位
        {
            "name": "马内分泌",
            "title": "副主任医师",
            "gender": "male",
            "personality_type": "detailed",
            "intro": "内分泌科副主任医师，擅长糖尿病、甲状腺等内分泌代谢疾病的诊治。",
            "avatar_url": "/uploads/endo_detailed_01.png",
            "expertise": ["糖尿病", "甲状腺", "内分泌失调"],
            "rating": 4.8,
            "monthly_answers": 580,
        },
        {
            "name": "罗代谢",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "内分泌科主治医师，擅长慢病管理和生活方式指导。",
            "avatar_url": "/uploads/endo_friendly_01.png",
            "expertise": ["体重管理", "代谢综合征"],
            "rating": 4.7,
            "monthly_answers": 520,
        },
    ],
    "neurology": [  # 神经科 - 2位
        {
            "name": "冯神经",
            "title": "副主任医师",
            "gender": "male",
            "personality_type": "formal",
            "intro": "神经内科副主任医师，擅长头痛、头晕、失眠等神经系统疾病诊治。",
            "avatar_url": "/uploads/neuro_formal_01.png",
            "expertise": ["头痛", "头晕", "失眠"],
            "rating": 4.7,
            "monthly_answers": 540,
        },
        {
            "name": "顾神经",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "detailed",
            "intro": "神经内科主治医师，擅长详细解释神经系统和心理因素相关的健康问题。",
            "avatar_url": "/uploads/neuro_detailed_01.png",
            "expertise": ["焦虑", "神经衰弱"],
            "rating": 4.8,
            "monthly_answers": 480,
        },
    ],
    "ophthalmology": [  # 眼科 - 1位
        {
            "name": "眼科陈医生",
            "title": "主治医师",
            "gender": "male",
            "personality_type": "friendly",
            "intro": "眼科主治医师，擅长常见眼科疾病诊治。",
            "avatar_url": "/uploads/ophthal_friendly_01.png",
            "expertise": ["结膜炎", "干眼症", "视力疲劳"],
            "rating": 4.7,
            "monthly_answers": 420,
        },
    ],
    "otorhinolaryngology": [  # 耳鼻咽喉科 - 1位
        {
            "name": "耳鼻喉周医生",
            "title": "主治医师",
            "gender": "male",
            "personality_type": "friendly",
            "intro": "耳鼻咽喉科主治医师，擅长常见耳鼻咽喉疾病诊治。",
            "avatar_url": "/uploads/ent_friendly_01.png",
            "expertise": ["中耳炎", "鼻炎", "咽炎"],
            "rating": 4.7,
            "monthly_answers": 390,
        },
    ],
    "stomatology": [  # 口腔科 - 1位
        {
            "name": "口腔科李医生",
            "title": "主治医师",
            "gender": "female",
            "personality_type": "friendly",
            "intro": "口腔科主治医师，擅长常见口腔疾病诊治。",
            "avatar_url": "/uploads/dental_friendly_01.png",
            "expertise": ["龋齿", "牙龈炎", "口腔溃疡"],
            "rating": 4.7,
            "monthly_answers": 360,
        },
    ],
}


def generate_virtual_doctor_seeds(
    department_id_map: Dict[str, int],
    start_id: int = 1000
) -> List[Dict[str, Any]]:
    """
    生成虚拟医生种子数据

    Args:
        department_id_map: 科室代码到科室 ID 的映射
            例如: {"dermatology": 1, "cardiology": 2, ...}
        start_id: 起始 ID

    Returns:
        虚拟医生数据列表，可直接用于创建 Doctor 记录
    """
    doctors = []
    current_id = start_id

    for specialty_code, templates in VIRTUAL_DOCTOR_TEMPLATES.items():
        department_id = department_id_map.get(specialty_code)
        if not department_id:
            print(f"Warning: No department_id found for {specialty_code}, skipping...")
            continue

        for template in templates:
            personality_type = template["personality_type"]
            personality_config = VirtualDoctorExtension.get_personality_config(personality_type)

            doctor = {
                "id": current_id,
                "name": template["name"],
                "title": template["title"],
                "department_id": department_id,
                "hospital": "灵犀健康AI医疗中心",
                "specialty": template["name"],  # 用医生姓名作为专科标识
                "intro": template["intro"],
                "avatar_url": template["avatar_url"],
                "rating": template["rating"],
                "monthly_answers": template["monthly_answers"],
                "avg_response_time": "3分钟",
                "can_prescribe": False,
                "is_top_hospital": False,

                # AI 分身核心字段
                "is_ai": True,
                "is_active": True,
                "ai_model": "qwen-plus",
                "agent_type": specialty_code,
                "ai_temperature": personality_config["temperature"],
                "ai_max_tokens": 600,
                "ai_persona_prompt": VirtualDoctorExtension.build_style_prompt(personality_type),
                "agent_config": {
                    "personality_type": personality_type,
                    "style_tags": personality_config["style_tags"],
                    "greeting_template": VirtualDoctorExtension.build_greeting(
                        template["name"], personality_type
                    ),
                    "expertise": template.get("expertise", []),
                },
            }

            doctors.append(doctor)
            current_id += 1

    return doctors


def print_virtual_doctor_summary():
    """打印虚拟医生配置摘要（用于调试）"""
    print("\n" + "=" * 60)
    print("虚拟医生配置摘要")
    print("=" * 60)

    total = 0
    for specialty, templates in VIRTUAL_DOCTOR_TEMPLATES.items():
        count = len(templates)
        total += count
        personalities = [t["personality_type"] for t in templates]
        print(f"\n{specialty}: {count} 位医生")
        print(f"  性格分布: {', '.join(personalities)}")

    print(f"\n总计: {total} 位虚拟医生")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_virtual_doctor_summary()
