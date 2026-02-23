"""
ICD-10 疾病分类数据加载器

从国家医保局的 ICD-10 数据导入疾病分类信息
"""
import csv
import asyncio
from typing import List, Dict, Any
from ..core.vector_store import Document
from ..knowledge_service import KnowledgeService


# ICD-10 疾病分类示例数据（生产环境应从官方数据源解析）
ICD10_SAMPLE_DATA = [
    {
        "code": "L20",
        "name": "皮肤和皮下组织疾病",
        "description": "包括皮肤、皮下组织的疾病，如皮炎、湿疹、感染等",
        "keywords": ["皮肤", "皮疹", "湿疹", "皮炎", "感染"],
        "specialty": "dermatology"
    },
    {
        "code": "L30",
        "name": "皮炎和湿疹",
        "description": "各种类型的皮炎和湿疹，包括接触性皮炎、特应性皮炎等",
        "keywords": ["皮炎", "湿疹", "特应性皮炎", "接触性皮炎"],
        "specialty": "dermatology"
    },
    {
        "code": "L40",
        "name": "荨麻疹和荨",
        "description": "荨麻疹等过敏性疾病",
        "keywords": ["荨麻疹", "风团", "过敏", "瘙痒"],
        "specialty": "dermatology"
    },
    {
        "code": "I10",
        "name": "循环系统疾病",
        "description": "心脏、血管、循环系统相关疾病",
        "keywords": ["心脏", "心血管", "血压", "循环", "血管"],
        "specialty": "cardiology"
    },
    {
        "code": "I11",
        "name": "高血压病",
        "description": "原发性高血压等血压异常疾病",
        "keywords": ["高血压", "血压高", "收缩压", "舒张压"],
        "specialty": "cardiology"
    },
    {
        "code": "M00-M99",
        "name": "肌肉骨骼系统和结缔组织疾病",
        "description": "骨骼、关节、肌肉相关疾病",
        "keywords": ["骨", "关节", "肌肉", "骨科", "骨折"],
        "specialty": "orthopedics"
    },
]


async def load_icd10_data():
    """
    加载 ICD-10 疾病分类数据到知识库

    生产环境应从以下来源获取：
    - 国家医保局 ICD-10 数据：https://code.nhsa.gov.cn
    - WHO ICD-10 数据：https://icd.who.int
    """
    knowledge = KnowledgeService.get_instance()
    await knowledge.initialize()

    added_count = 0

    for item in ICD10_SAMPLE_DATA:
        content = f"{item['name']}（{item['code']}）\n{item['description']}\n关键词：{', '.join(item['keywords'])}"

        metadata = {
            "code": item["code"],
            "name": item["name"],
            "keywords": item["keywords"],
            "category": "icd10",
            "specialty": item["specialty"]
        }

        doc_id = await knowledge.add_document(
            content=content,
            metadata=metadata,
            specialty=item["specialty"],
            source="icd10"
        )

        if doc_id:
            added_count += 1
            print(f"[ICD10] 添加: {item['name']} ({item['code']})")

    print(f"[ICD10] 完成，共添加 {added_count} 条数据")


if __name__ == "__main__":
    asyncio.run(load_icd10_data())
