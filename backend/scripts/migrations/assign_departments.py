"""
自动为医脉通疾病分配科室
根据疾病名称和 sections 内容智能分类
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import re
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.department import Department


# 科室关键词映射 - 基于疾病名称和内容的分类规则
DEPARTMENT_KEYWORDS = {
    1: {  # 皮肤科
        'name': '皮肤科',
        'keywords': [
            '皮肤', '皮疹', '湿疹', '皮炎', '荨麻疹', '银屑病', '痤疮', '白癜风',
            '真菌', '癣', '疱疹', '疣', '狼疮', '硬皮病', '皮肌炎',
            'dermatitis', 'eczema', 'psoriasis', 'acne', 'vitiligo', 'skin',
            'urticaria', 'impetigo', 'scabies', 'melanoma'
        ],
        'sections': ['皮肤', '皮损']
    },
    2: {  # 儿科
        'name': '儿科',
        'keywords': [
            '小儿', '婴儿', '幼儿', '儿童', '新生儿', '早产儿', '先天性',
            'pediatric', 'neonatal', 'neonate', 'infant', 'child', 'children',
            'preterm', 'newborn', 'bronchopneumonia', 'hyperbilirubinemia'
        ],
        'sections': ['儿科', '小儿', '新生儿']
    },
    3: {  # 妇产科
        'name': '妇产科',
        'keywords': [
            '妊娠', '孕妇', '产妇', '胎儿', '分娩', '流产', '不孕', '卵巢',
            '子宫', '宫颈', '乳腺', '阴道', '盆腔', '外阴', '妇科',
            'pregnancy', 'fetal', 'maternal', 'obstetric', 'gynecologic',
            'ovarian', 'uterine', 'cervical', 'vulvar', 'breast', 'pelvic'
        ],
        'sections': ['产科', '妇科', '妊娠']
    },
    4: {  # 消化内科
        'name': '消化内科',
        'keywords': [
            '胃', '肠', '腹泻', '便秘', '肝炎', '肝硬化', '肝癌', '胰腺', '胆囊',
            '胆结石', '胃炎', '肠炎', '溃疡', '结肠炎', '脂肪肝', '消化道',
            'gastric', 'gastritis', 'ulcer', 'colitis', 'hepatitis', 'cirrhosis',
            'pancreatic', 'gallstone', 'diarrhea', 'constipation', 'gastro'
        ],
        'sections': ['消化', '胃肠', '肝胆', '胰腺']
    },
    5: {  # 呼吸内科
        'name': '呼吸内科',
        'keywords': [
            '肺', '哮喘', '肺炎', '支气管', '咳嗽', '气胸', '肺栓塞', '肺纤维化',
            '慢阻肺', 'copd', '呼吸道', '肺泡', '呼吸',
            'pulmonary', 'pneumonia', 'asthma', 'bronch', 'respiratory',
            'embolism', 'fibrosis', 'pleural'
        ],
        'sections': ['呼吸', '肺部', '肺']
    },
    6: {  # 心血管内科
        'name': '心血管内科',
        'keywords': [
            '心脏', '冠心病', '心衰', '心律失常', '心肌', '心包', '瓣膜', '高血压',
            '动脉', '静脉', '血栓', '心梗', '心力衰竭', '三尖瓣', '二尖瓣',
            'cardiac', 'cardio', 'heart', 'coronary', 'hypertension', 'arrhythmia',
            'myocardial', 'valve', 'thrombosis', 'vascular', 'atrial'
        ],
        'sections': ['心血管', '心脏', '血管']
    },
    7: {  # 内分泌科
        'name': '内分泌科',
        'keywords': [
            '糖尿病', '甲状腺', '甲亢', '甲减', '垂体', '肾上腺', '代谢',
            '肥胖', '骨质疏松', '痛风', '激素',
            'diabetes', 'thyroid', 'hyperthyroid', 'hypothyroid', 'pituitary',
            'adrenal', 'metabolic', 'obesity', 'osteoporosis', 'gout'
        ],
        'sections': ['内分泌', '代谢', '甲状腺']
    },
    8: {  # 神经内科
        'name': '神经内科',
        'keywords': [
            '头痛', '偏头痛', '癫痫', '卒中', '中风', '痴呆', '帕金森', '脑炎',
            '脑膜炎', '神经', '多发性硬化', '重症肌无力', '脑血管',
            'headache', 'migraine', 'epilepsy', 'stroke', 'dementia', 'parkinson',
            'encephalitis', 'meningitis', 'neural', 'sclerosis', 'neuralgia'
        ],
        'sections': ['神经', '脑血管', '大脑']
    },
    9: {  # 骨科
        'name': '骨科',
        'keywords': [
            '骨折', '骨', '关节', '脊柱', '腰椎', '颈椎', '骨质疏松', '扭伤',
            '脱位', '韧带', '半月板', '肩周炎', '腰痛',
            'fracture', 'bone', 'joint', 'spine', 'lumbar', 'cervical',
            'osteoporosis', 'ligament', 'dislocation', 'shoulder'
        ],
        'sections': ['骨科', '骨', '关节', '脊柱']
    },
    10: {  # 眼科
        'name': '眼科',
        'keywords': [
            '眼', '视力', '近视', '远视', '散光', '白内障', '青光眼', '视网膜',
            '结膜炎', '角膜', '眼底',
            'eye', 'ocular', 'vision', 'cataract', 'glaucoma', 'retinal',
            'conjunctivitis', 'corneal', 'fundus', 'myopia'
        ],
        'sections': ['眼科', '眼', '视力', '视网膜']
    },
    11: {  # 耳鼻咽喉科
        'name': '耳鼻咽喉科',
        'keywords': [
            '耳', '鼻', '咽', '喉', '扁桃体', '中耳炎', '鼻炎', '鼻窦', '声带',
            '听力', '耳鸣', '眩晕',
            'ear', 'nose', 'throat', 'tonsil', 'otitis', 'rhinitis', 'sinus',
            'vocal', 'hearing', 'tinnitus', 'vertigo', 'larynx'
        ],
        'sections': ['耳鼻', '咽喉', '听力', '耳', '鼻', '喉']
    },
    12: {  # 口腔科
        'name': '口腔科',
        'keywords': [
            '牙', '齿', '口腔', '牙周', '牙龈', '龋齿', '智齿', '牙髓',
            'tooth', 'dental', 'oral', 'periodontal', 'gingival', 'cavity'
        ],
        'sections': ['口腔', '牙', '齿']
    },
    # 以下是额外科室（如果数据库中有的话）
    13: {  # 小儿内科
        'name': '小儿内科',
        'keywords': [
            '小儿', '儿童', 'pediatric', 'child'
        ],
        'sections': ['小儿', '儿科']
    },
    14: {  # 急诊科
        'name': '急诊科',
        'keywords': [
            '急救', '急诊', '中毒', '休克', 'trauma', 'emergency', 'poisoning'
        ],
        'sections': ['急救', '急诊']
    },
    15: {  # 其他综合
        'name': '其他综合',
        'keywords': ['发热', '乏力', '水肿'],
        'sections': []
    },
    16: {  # 肿瘤内科
        'name': '肿瘤内科',
        'keywords': [
            '癌', '瘤', '肿瘤', '白血病', '淋巴瘤', '骨髓瘤', '化疗', '靶向',
            'cancer', 'tumor', 'carcinoma', 'sarcoma', 'leukemia', 'lymphoma', 'oncology', 'chemotherapy'
        ],
        'sections': ['肿瘤', '癌症']
    },
    17: {  # 心胸外科
        'name': '心胸外科',
        'keywords': [
            '胸', '肺手术', '心脏手术', 'chest', 'thoracic', 'cardiac surgery'
        ],
        'sections': ['胸外科']
    },
    18: {  # 感染科
        'name': '感染科',
        'keywords': [
            '感染', '病毒', '细菌', '真菌', '寄生虫', '败血症', 'infection',
            'viral', 'bacterial', 'fungal', 'sepsis', 'parasitic'
        ],
        'sections': ['感染']
    },
    19: {  # 传染科
        'name': '传染科',
        'keywords': [
            '结核', '流感', '传染', 'tuberculosis', 'infectious'
        ],
        'sections': ['传染']
    },
    20: {  # 儿科综合
        'name': '儿科综合',
        'keywords': ['小儿', '儿童', 'pediatric', 'child'],
        'sections': []
    },
    21: {  # 产科
        'name': '产科',
        'keywords': [
            '妊娠', '分娩', '产前', '产后', 'pregnancy', 'delivery', 'maternal'
        ],
        'sections': ['产科', '妊娠']
    },
    22: {  # 普外科
        'name': '普外科',
        'keywords': [
            '疝气', '阑尾', '胆囊', '脾脏', 'hernia', 'appendicitis', 'gallbladder', 'spleen'
        ],
        'sections': ['外科']
    },
    23: {  # 心内科（与心血管内科重复，优先心血管内科）
        'name': '心内科',
        'keywords': ['心脏', '心血管', 'cardiac', 'cardio'],
        'sections': []
    },
    24: {  # 肿瘤外科
        'name': '肿瘤外科',
        'keywords': ['肿瘤手术', '癌手术', 'cancer surgery', 'tumor surgery'],
        'sections': []
    },
    25: {  # 风湿免疫科
        'name': '风湿免疫科',
        'keywords': [
            '风湿', '类风湿', '红斑狼疮', '强直性脊柱炎', '干燥综合征',
            'rheumatoid', 'lupus', 'ankylosing', 'spondylitis', 'autoimmune'
        ],
        'sections': ['风湿', '免疫']
    },
    26: {  # 小儿外科
        'name': '小儿外科',
        'keywords': ['小儿手术', '儿童手术', 'pediatric surgery'],
        'sections': []
    },
    27: {  # 耳鼻喉科（与耳鼻咽喉科重复）
        'name': '耳鼻喉科',
        'keywords': ['耳', '鼻', '喉', 'ear', 'nose', 'throat'],
        'sections': []
    },
    28: {  # 妇科
        'name': '妇科',
        'keywords': [
            '卵巢', '子宫', '宫颈', '阴道', '盆腔', '外阴', '月经',
            'ovarian', 'uterine', 'cervical', 'vaginal', 'pelvic', 'vulvar', 'menstrual'
        ],
        'sections': ['妇科']
    },
    29: {  # 康复科
        'name': '康复科',
        'keywords': ['康复', 'rehabilitation'],
        'sections': ['康复']
    },
    30: {  # 肛肠科
        'name': '肛肠科',
        'keywords': [
            '痔疮', '肛裂', '肛瘘', '直肠', '肛门',
            'hemorrhoid', 'anal', 'rectal', 'anus'
        ],
        'sections': ['肛肠', '直肠', '肛门']
    },
    31: {  # 肝病
        'name': '肝病',
        'keywords': ['肝炎', '肝硬化', '肝癌', 'hepatitis', 'cirrhosis', 'liver'],
        'sections': ['肝']
    },
    32: {  # 肝胆外科
        'name': '肝胆外科',
        'keywords': ['肝手术', '胆手术', 'liver surgery', 'biliary surgery'],
        'sections': []
    },
    33: {  # 血液科
        'name': '血液科',
        'keywords': [
            '贫血', '白血病', '血友病', '血小板', '淋巴瘤', '骨髓',
            'anemia', 'leukemia', 'hemophilia', 'platelet', 'lymphoma', 'blood'
        ],
        'sections': ['血液']
    },
    34: {  # 遗传病科
        'name': '遗传病科',
        'keywords': [
            '遗传', '基因', '染色体', '先天性',
            'genetic', 'gene', 'chromosome', 'congenital', 'hereditary'
        ],
        'sections': ['遗传']
    },
    35: {  # 肾内科
        'name': '肾内科',
        'keywords': [
            '肾', '肾炎', '肾病', '肾衰竭', '尿毒症', '透析',
            'renal', 'kidney', 'nephritis', 'dialysis'
        ],
        'sections': ['肾', '肾脏']
    },
    36: {  # 泌尿外科
        'name': '泌尿外科',
        'keywords': [
            '泌尿', '前列腺', '膀胱', '尿道', '肾脏', '肾结石',
            'urology', 'prostate', 'bladder', 'urethral', 'kidney stone'
        ],
        'sections': ['泌尿']
    },
    37: {  # 泌尿内科
        'name': '泌尿内科',
        'keywords': ['肾病', '肾炎', 'nephrology'],
        'sections': []
    },
    38: {  # 中医综合
        'name': '中医综合',
        'keywords': ['中医', '中药', '针灸', 'tcm', 'acupuncture'],
        'sections': []
    },
    39: {  # 烧伤科
        'name': '烧伤科',
        'keywords': ['烧伤', '烫伤', 'burn'],
        'sections': []
    },
    40: {  # 男科
        'name': '男科',
        'keywords': [
            '男性', '阳痿', '早泄', '前列腺', '精子',
            'male', 'impotence', 'premature', 'prostate', 'sperm'
        ],
        'sections': ['男科']
    },
    41: {  # 骨外科（与骨科重复）
        'name': '骨外科',
        'keywords': ['骨折', '骨', '关节', 'fracture', 'bone', 'joint'],
        'sections': []
    },
    42: {  # 神经外科
        'name': '神经外科',
        'keywords': [
            '脑手术', '脑外伤', '脑出血', '开颅', '神经手术',
            'brain surgery', 'neurosurgery', 'craniotomy'
        ],
        'sections': ['神经外科']
    },
    43: {  # 精神心理科
        'name': '精神心理科',
        'keywords': [
            '抑郁', '焦虑', '失眠', '精神分裂', '双相', '心理',
            'depression', 'anxiety', 'insomnia', 'schizophrenia', 'bipolar', 'psychological'
        ],
        'sections': ['精神', '心理']
    },
    44: {  # 营养科
        'name': '营养科',
        'keywords': ['营养', '饮食', 'nutrition', 'diet'],
        'sections': ['营养', '饮食']
    },
    45: {  # 其他
        'name': '其他',
        'keywords': [],
        'sections': []
    },
}


def classify_disease(name: str, sections: list) -> int:
    """
    根据疾病名称和 sections 分类科室

    返回科室 ID，无法分类返回 None
    """
    text = name.lower()

    # 合并 sections 内容用于分类
    section_texts = []
    if sections:
        for section in sections:
            if isinstance(section, dict):
                title = section.get('title') or ''
                content = section.get('content') or ''
                section_texts.append(title.lower())
                section_texts.append(content.lower())

    combined_text = text + ' ' + ' '.join(section_texts)

    scores = {}  # 科室ID -> 匹配分数

    for dept_id, rules in DEPARTMENT_KEYWORDS.items():
        score = 0

        # 检查名称中的关键词
        for keyword in rules['keywords']:
            if keyword.lower() in text:
                score += 10  # 名称匹配权重高

        # 检查 sections 中的关键词
        for section_text in section_texts:
            for keyword in rules['keywords']:
                if keyword.lower() in section_text:
                    score += 3  # 内容匹配权重较低
                    break

        # 检查 section 标题
        for section in sections or []:
            if isinstance(section, dict):
                section_title = section.get('title', '')
                for section_keyword in rules.get('sections', []):
                    if section_keyword in section_title:
                        score += 5  # section 标题匹配权重中等

        if score > 0:
            scores[dept_id] = score

    if not scores:
        return None

    # 返回分数最高的科室
    return max(scores.items(), key=lambda x: x[1])[0]


def main():
    db = SessionLocal()

    # 获取所有科室
    departments = db.query(Department).all()
    dept_map = {d.id: d.name for d in departments}
    print(f"可用科室: {dept_map}\n")

    # 获取所有 MedLive 疾病
    diseases = db.query(Disease).filter(Disease.source == '医脉通').all()
    print(f"需要分类的疾病数: {len(diseases)}\n")

    # 统计分类结果
    classified = {d_id: 0 for d_id in dept_map.keys()}
    unclassified = []

    for disease in diseases:
        dept_id = classify_disease(disease.name, disease.sections)

        if dept_id:
            disease.department_id = dept_id
            classified[dept_id] += 1
        else:
            unclassified.append(disease.name)

    # 提交更改
    db.commit()

    # 打印统计
    print("=" * 50)
    print("分类统计:")
    print("=" * 50)
    for dept_id, count in classified.items():
        if count > 0:
            print(f"  {dept_map[dept_id]}: {count} 个")

    print(f"\n未分类: {len(unclassified)} 个")

    if unclassified and len(unclassified) <= 20:
        print(f"\n未分类疾病示例:")
        for name in unclassified[:20]:
            print(f"  - {name}")

    # 更新 JSON 文件
    print("\n" + "=" * 50)
    print("更新 JSON 文件...")
    print("=" * 50)

    db.close()

    # 重新导出 JSON
    db = SessionLocal()
    diseases = db.query(Disease).filter(Disease.source == '医脉通').all()

    export_data = {
        'meta': {
            'source': '医脉通 yzy.medlive.cn',
            'exported_at': '2026-01-23T00:00:00',
            'total_count': len(diseases),
            'version': '2.1'
        },
        'diseases': []
    }

    for d in diseases:
        export_data['diseases'].append({
            'id': d.id,
            'wiki_id': d.wiki_id,
            'name': d.name,
            'department_id': d.department_id,
            'department_name': dept_map.get(d.department_id),
            'url': d.url,
            'source': d.source,
            'sections': d.sections
        })

    with open('data/diseases.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"已导出 {len(diseases)} 个疾病到 data/diseases.json")

    # 验证
    still_unclassified = db.query(Disease).filter(
        Disease.source == '医脉通',
        Disease.department_id == None
    ).count()
    print(f"\n仍有 {still_unclassified} 个疾病未分类")

    db.close()


if __name__ == "__main__":
    main()
