"""
MSD 诊疗手册数据加载器
加载从 MSD Manuals 爬取的真实医学数据
"""
import json
import os
from typing import List, Dict, Any
from ..core import Document


def _get_data_file_path():
    """获取数据文件路径"""
    # 尝试多个可能的路径
    possible_paths = [
        # 容器内路径
        "/app/data/msd_knowledge.json",
        # 相对于当前文件的路径
        os.path.join(os.path.dirname(__file__), "../../../data/msd_knowledge.json"),
        # 相对于项目根目录的路径
        os.path.join(os.path.dirname(__file__), "../../data/msd_knowledge.json"),
        # 绝对路径（开发环境）
        "/Users/zhuxinye/Desktop/project/home-health/medical-knowledge-service/data/msd_knowledge.json",
        # 当前工作目录下的路径
        "data/msd_knowledge.json",
        "../data/msd_knowledge.json",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # 如果都不存在，返回默认路径
    return possible_paths[0]


MSD_DATA_FILE = _get_data_file_path()


def load_msd_documents() -> List[Document]:
    """
    从 MSD 诊疗手册数据加载医学知识文档

    Returns:
        医学知识文档列表
    """
    documents = []

    # 尝试加载爬取的数据
    if os.path.exists(MSD_DATA_FILE):
        with open(MSD_DATA_FILE, 'r', encoding='utf-8') as f:
            msd_data = json.load(f)

        for item in msd_data:
            doc = Document(
                id=item.get('code', ''),
                content=item['content'],
                metadata={
                    'code': item['code'],
                    'name': item['name'],
                    'keywords': item.get('keywords', []),
                    'source': item.get('source', 'msd_manuals'),
                    'source_url': item.get('source_url', ''),
                },
                specialty=item['specialty'],
                category=item.get('code', '')[:1] if item.get('code') else None
            )
            documents.append(doc)

    return documents


# 兼容性函数，保持与原有 icd10_loader 相同的接口
def load_icd10_documents() -> List[Document]:
    """
    加载 ICD-10 医学知识文档（包含 MSD 数据）

    Returns:
        医学知识文档列表
    """
    return load_msd_documents()


# 如果需要，可以在这里添加 fallback 数据
FALLBACK_KNOWLEDGE_BASE = [
    # 心内科
    {
        "code": "I10",
        "name": "原发性高血压",
        "specialty": "cardiology",
        "keywords": ["高血压", "血压高", "Hypertension"],
        "content": """
原发性高血压（I10）是以体循环动脉压升高为主要表现的慢性疾病。

【诊断标准】
- 收缩压≥140mmHg 和/或 舒张压≥90mmHg
- 排除继发性高血压

【治疗原则】
1. 生活方式干预：低盐饮食、控制体重、规律运动
2. 药物治疗：ACEI/ARB、CCB、利尿剂、β受体阻滞剂
3. 目标血压：<140/90mmHg（一般人群）
        """
    },
    # 皮肤科
    {
        "code": "L20",
        "name": "特应性皮炎",
        "specialty": "dermatology",
        "keywords": ["特应性皮炎", "湿疹", "过敏性皮炎"],
        "content": """
特应性皮炎（L20）是一种慢性、复发性、炎症性皮肤病。

【主要症状】
- 剧烈瘙痒
- 皮肤干燥、脱屑
- 红斑、丘疹

【治疗原则】
- 保湿润肤
- 外用糖皮质激素
- 避免刺激因素
        """
    },
    # 呼吸科
    {
        "code": "J45",
        "name": "哮喘",
        "specialty": "respiratory",
        "keywords": ["哮喘", "支气管哮喘"],
        "content": """
哮喘（J45）是一种慢性气道炎症性疾病。

【主要症状】
- 反复发作的喘息
- 呼吸困难
- 胸闷
- 咳嗽（夜间或晨起加重）

【治疗原则】
- 长期控制：吸入糖皮质激素
- 缓解症状：短效β2受体激动剂
- 避免触发因素
        """
    },
]
