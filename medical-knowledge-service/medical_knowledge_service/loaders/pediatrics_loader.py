"""
儿科数据加载器
加载从 MSD Manuals 爬取的儿科医学数据
"""
import json
import os
from typing import List
from ..core import Document


def _get_data_file_path():
    """获取儿科数据文件路径"""
    possible_paths = [
        # 容器内路径
        "/app/data/pediatrics_knowledge.json",
        # 相对于当前文件的路径
        os.path.join(os.path.dirname(__file__), "../../../data/pediatrics_knowledge.json"),
        # 绝对路径（开发环境）
        "/Users/zhuxinye/Desktop/project/home-health/medical-knowledge-service/data/pediatrics_knowledge.json",
        # 当前工作目录下的路径
        "data/pediatrics_knowledge.json",
        "../data/pediatrics_knowledge.json",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return possible_paths[0]


PEDIATRICS_DATA_FILE = _get_data_file_path()


def load_pediatrics_documents() -> List[Document]:
    """
    从儿科数据文件加载医学知识文档

    Returns:
        医学知识文档列表
    """
    documents = []

    if not os.path.exists(PEDIATRICS_DATA_FILE):
        return documents

    with open(PEDIATRICS_DATA_FILE, 'r', encoding='utf-8') as f:
        pediatrics_data = json.load(f)

    for item in pediatrics_data:
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


def load_pediatrics_data() -> List[dict]:
    """
    加载原始儿科数据（返回原始格式）

    Returns:
        原始数据列表
    """
    if not os.path.exists(PEDIATRICS_DATA_FILE):
        return []

    with open(PEDIATRICS_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
