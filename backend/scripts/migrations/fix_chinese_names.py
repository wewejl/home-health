"""
将英文疾病名称替换为中文
从 sections 内容中提取中文名称
"""
import sys
import os
import re
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.disease import Disease
from app.models.department import Department


def extract_chinese_name(sections: list) -> str:
    """
    从 sections 中提取中文名称

    模式匹配：
    - 甲状腺癌（thyroid cancer
    - 三尖瓣疾病
    - 类风湿关节炎
    """
    if not sections:
        return None

    # 优先从"疾病简介"或"基础知识" section 中提取
    priority_sections = ['overview', 'basics', 'definition']

    for section in sections:
        if section.get('id') in priority_sections or section.get('title') in ['疾病简介', '基础知识', '定义']:
            content = section.get('content', '')
            if not content:
                continue

            # 按行查找
            lines = content.split('\n')
            for line in lines[:10]:  # 只看前10行
                line = line.strip()

                # 模式1: 中文名（英文缩写）
                # 例如: 甲状腺癌
                match = re.search(r'([^\（(\s]+)[（(]', line)
                if match:
                    name = match.group(1).strip()
                    # 简单验证：包含中文且不是过长的句子
                    if any('\u4e00' <= c <= '\u9fff' for c in name) and len(name) < 20:
                        # 去除序号
                        name = re.sub(r'^[一二三四五六七八九十]+[、.]?\s*', '', name)
                        if name:
                            return name

                # 模式2: 直接以中文开头后跟空格和英文
                # 例如: 甲状腺癌 thyroid cancer
                match = re.search(r'([\u4e00-\u9fff]+(?:病|症|炎|癌|瘤|损伤|综合征|障碍|异常|不全|畸形))\s+[a-zA-Z]', line)
                if match:
                    name = match.group(1).strip()
                    if len(name) < 20:
                        return name

    return None


# 常见疾病英中映射表（针对无法从内容提取的情况)
EN_TO_ZH_MAPPING = {
    'thyroid carcinoma': '甲状腺癌',
    'tricuspid valve disease': '三尖瓣疾病',
    'rheumatoid arthritis': '类风湿性关节炎',
    'soft tissue sarcoma': '软组织肉瘤',
    'allergic rhinitis': '变应性鼻炎',
    'pulmonary embolism': '肺栓塞',
    'osteogenesis imperfecta': '成骨不全症',
    'sudden sensorineural hearing loss': '突发性感音神经性听力损失',
    'osteoporosis': '骨质疏松症',
    'gout': '痛风',
    'anemia': '贫血',
    'pneumonia': '肺炎',
    'diabetes mellitus': '糖尿病',
    'hypertension': '高血压',
    'myocardial infarction': '心肌梗死',
    'stroke': '卒中',
    'parkinson disease': '帕金森病',
    'alzheimer disease': '阿尔茨海默病',
    'epilepsy': '癫痫',
    'asthma': '哮喘',
    'copd': '慢性阻塞性肺疾病',
    'appendicitis': '阑尾炎',
    'cholecystitis': '胆囊炎',
    'pancreatitis': '胰腺炎',
    'hepatitis': '肝炎',
    'cirrhosis': '肝硬化',
    'nephritis': '肾炎',
    'gastritis': '胃炎',
    'enteritis': '肠炎',
    'conjunctivitis': '结膜炎',
    'otitis media': '中耳炎',
    'sinusitis': '鼻窦炎',
    'dermatitis': '皮炎',
    'eczema': '湿疹',
    'psoriasis': '银屑病',
    'urticaria': '荨麻疹',
    # 额外翻译
    'blastomyces dermatitidis': '皮炎芽生菌病',
    'sporothrix schenckii': '申克孢子丝菌病',
    'b. cepacia': '洋葱伯克霍尔德菌',
    'preterm infant': '早产儿',
    'premature infant': '早产儿',
    'infantile vulvovaginiti': '婴幼儿外阴阴道炎',
    'familial dysbetalipoproteinemia': '家族性异常β脂蛋白血症',
    'familial hypobetalipoproteinemia': '家族性无β脂蛋白血症',
    'mental disorders': '精神障碍',
    'infantile abdominal pain': '婴幼儿腹痛',
    'mucor': '毛霉',
    'plexus syndromes': '神经丛综合征',
    'rosacea': '酒渣鼻',
    'cerebral autosomal dominant arteriopathy': '常染色体显性脑动脉病',
    'chest pain': '胸痛',
    'chlamydophila psittaci': '鹦鹉热衣原体',
    'gastric bezoar': '胃石',
    'ethmoid sinus': '筛窦',
    'acne': '痤疮',
    'vitiligo': '白癜风',
    'impetigo': '脓疱疮',
    'scabies': '疥疮',
    'melanoma': '黑色素瘤',
    'lupus': '狼疮',
    'scleroderma': '硬皮病',
    'dermatomyositis': '皮肌炎',
    'cellulitis': '蜂窝织炎',
    'abscess': '脓肿',
    # 额外翻译 - 第2批
    'hypernatremia': '高钠血症',
    'general paresis': '全身麻痹性痴呆',
    'colonic diverticulosis': '结肠憩室病',
    'scleredema neonatorum': '新生儿硬化病',
    'hip fracture': '髋部骨折',
    'emaciation': '消瘦',
    'cysticercosis': '囊尾蚴病',
    'endometriosis': '子宫内膜异位症',
    'd-dimer': 'D-二聚体',
    'scarlet fever': '猩红热',
    'pneumoconiosis': '尘肺',
    'delusional disorder': '妄想障碍',
    'oral cancer': '口腔癌',
    'hypopharyngeal carcinoma': '下咽癌',
    'diffuse astrocytoma': '弥漫性星形细胞瘤',
    'penile cancer': '阴茎癌',
    'carcinoma of the tongue': '舌癌',
    'hemochromatosis': '血色病',
    'leber hereditary optic neuropathy': '莱伯遗传性视神经病变',
    'endemic typhus': '地方性斑疹伤寒',
    'familial chylomicronemia syndrome': '家族性乳糜微粒综合征',
    'familial hypertriglyceridemia': '家族性高甘油三酯血症',
    'homocysteinemia': '高同型半胱氨酸血症',
    'pituitary apoplexy': '垂体卒中',
    'prolapse of umbilical cord': '脐带脱垂',
    'sputum culture': '痰培养',
    'fever in children': '儿童发热',
    'hemorrhagic tendency': '出血倾向',
    'long covid': '长新冠',
    'campylobacter jejuni': '空肠弯曲杆菌',
    'bacteroides fragilis': '脆弱拟杆菌',
    'aeromonas': '气单胞菌',
    'coccidiodes immitis': '粗球孢子菌',
    'histoplasma capsulatum': '荚膜组织胞浆菌',
    'malignant transformation': '恶性变',
    'immunosuppressive drugs': '免疫抑制剂',
    'glucocorticoid': '糖皮质激素',
    'audiometry': '听力测定',
    'vasopressin': '血管加压素',
    'folic acid': '叶酸',
    'fludrocortisone': '氟氢可的松',
    'dynamic visual acuity': '动态视力',
    'stomach lavage': '洗胃',
    'morita therapy': '森田疗法',
    'minimally invasive surgery': '微创手术',
    # 额外翻译 - 第3批
    'suicide': '自杀',
    'infantile acute upper respiratory tract infection': '婴幼儿急性上呼吸道感染',
    'human leucocyte antigen antibody': '人类白细胞抗原抗体',
    'hereditary multi-infarct dementia': '遗传性多发梗死性痴呆',
    'saline infusion test': '盐水输注试验',
    'oral salt loading test': '口服盐水负荷试验',
    'hemo chromatosis': '血色病',
}


def get_chinese_name(original_name: str, sections: list) -> str:
    """获取疾病的中文名称"""

    # 首先尝试从 sections 中提取
    chinese_name = extract_chinese_name(sections)
    if chinese_name:
        return chinese_name

    # 其次使用映射表
    name_lower = original_name.lower().strip()
    for en, zh in EN_TO_ZH_MAPPING.items():
        if en in name_lower:
            return zh

    # 如果是纯英文名称，尝试从关键词翻译
    # 检查是否包含常见的疾病后缀
    suffixes = {
        'carcinoma': '癌',
        'cancer': '癌',
        'sarcoma': '肉瘤',
        'syndrome': '综合征',
        'disease': '病',
        'deficiency': '缺乏症',
        'infection': '感染',
        'inflammation': '炎',
        'virus': '病毒',
    }

    for en_suffix, zh_suffix in suffixes.items():
        if name_lower.endswith(en_suffix):
            # 提取词根
            root = name_lower[:-len(en_suffix)]
            # 如果是常见疾病词根
            root_map = {
                'thyroid': '甲状腺',
                'pulmonary': '肺',
                'renal': '肾',
                'hepatic': '肝',
                'cardiac': '心脏',
                'gastric': '胃',
                'neural': '神经',
            }
            if root in root_map:
                return root_map[root] + zh_suffix

    return None


def main():
    db = SessionLocal()

    # 获取所有 MedLive 疾病
    diseases = db.query(Disease).filter(Disease.source == '医脉通').all()

    updated_count = 0
    no_change_count = 0

    for disease in diseases:
        # 检查是否有中文
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in disease.name)

        if not has_chinese:
            # 尝试获取中文名称
            chinese_name = get_chinese_name(disease.name, disease.sections)

            if chinese_name:
                old_name = disease.name
                disease.name = chinese_name
                updated_count += 1

                if updated_count <= 10:
                    print(f'{old_name} -> {chinese_name}')
            else:
                no_change_count += 1

    db.commit()

    print(f'\n总计:')
    print(f'  已更新: {updated_count}')
    print(f'  保持英文: {no_change_count}')

    # 更新 JSON 文件
    print('\n更新 JSON 文件...')
    db.close()

    db = SessionLocal()
    diseases = db.query(Disease).filter(Disease.source == '医脉通').all()

    dept_map = {d.id: d.name for d in db.query(Department).all()}

    export_data = {
        'meta': {
            'source': '医脉通 yzy.medlive.cn',
            'exported_at': '2026-01-23T00:00:00',
            'total_count': len(diseases),
            'version': '2.2'
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

    print(f'已导出 {len(diseases)} 个疾病到 data/diseases.json')

    # 统计
    chinese_count = sum(1 for d in diseases if any('\u4e00' <= c <= '\u9fff' for c in d.name))
    english_count = len(diseases) - chinese_count
    print(f'\n更新后统计:')
    print(f'  中文名: {chinese_count}')
    print(f'  英文名: {english_count}')

    db.close()


if __name__ == "__main__":
    main()
