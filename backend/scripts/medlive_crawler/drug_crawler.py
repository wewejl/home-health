#!/usr/bin/env python3
"""
MedLive 医脉通药品爬虫
从 drugs.medlive.cn 获取药品数据并导入数据库
"""
import sys
import os
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.drug import Drug, DrugCategory


# MedLive 药品分类映射（到我们的分类）
CATEGORY_MAPPING = {
    "解热镇痛抗炎抗风湿": "感冒发烧",
    "抗生素": "感冒发烧",
    "呼吸系统": "感冒发烧",
    "消化系统": "消化系统",
    "皮肤科": "皮肤用药",
    "心血管": "心脑血管",
    "内分泌": "其他",
    "神经系统": "其他",
    "维生素": "其他",
    "抗过敏": "皮肤用药",
    "中成药": "其他",
}


def get_pinyin_abbr(text: str) -> str:
    """简单的拼音首字母提取（仅支持常见药品）"""
    # 常见药品拼音映射
    PINYIN_MAP = {
        "布洛芬": "blf",
        "对乙酰氨基酚": "dyxajf",
        "阿奇霉素": "aqms",
        "奥司他韦": "astw",
        "奥美拉唑": "amlz",
        "蒙脱石散": "mtss",
        "莫匹罗星": "mplx",
        "炉甘石": "lgs",
        "阿司匹林": "aspl",
        "硝苯地平": "xbdp",
        "氨氯地平": "aldp",
        "厄贝沙坦": "ebst",
        "缬沙坦": "xst",
        "氯雷他定": "llld",
        "西替利嗪": "xtlq",
        "依巴斯汀": "ybld",
        "地奈德": "dnd",
        "糠酸莫米松": "kamms",
        "卤米松": "lms",
        "他克莫司": "tkms",
        "头孢拉定": "tfld",
        "头孢克肟": "tfkw",
        "阿莫西林": "amxl",
        "左氧氟沙星": "zyfslx",
        "莫西沙星": "mxslx",
        "多西环素": "dxhs",
        "米诺环素": "mnhs",
        "二甲双胍": "ejst",
        "格列美脲": "glmn",
        "阿卡波糖": "akbt",
        "辛伐他汀": "xfht",
        "阿托伐他汀": "atfht",
        "瑞舒伐他汀": "rsfht",
        "非诺贝特": "fnbt",
    }
    return PINYIN_MAP.get(text, text.lower()[:10])


def parse_pregnancy_level(text: str) -> tuple:
    """解析孕期安全等级"""
    text = text or ""
    if "A类" in text or "级A" in text:
        return "A", "A级：对照研究未显示风险，可安全使用"
    elif "B类" in text or "级B" in text:
        return "B", "B级：无人类危害证据，相对安全"
    elif "C类" in text or "级C" in text:
        return "C", "C级：不能排除风险，获益大于风险时使用"
    elif "D类" in text or "级D" in text:
        return "D", "D级：有胎儿风险证据，获益大于风险时使用"
    elif "X类" in text or "级X" in text:
        return "X", "X级：禁用于孕妇"
    elif "禁用" in text or "禁忌" in text:
        return "X", "孕妇禁用"
    return None, None


def parse_lactation_level(text: str) -> tuple:
    """解析哺乳期安全等级"""
    text = text or ""
    if "L1" in text:
        return "L1", "L1：最安全，可哺乳"
    elif "L2" in text:
        return "L2", "L2：较安全，可能可用"
    elif "L3" in text:
        return "L3", "L3：可能有效，需评估"
    elif "L4" in text:
        return "L4", "L4：有风险，慎用"
    elif "L5" in text:
        return "L5", "L5：禁用于哺乳期"
    return None, None


def extract_drug_name(soup: BeautifulSoup) -> str:
    """提取药品名称"""
    # 尝试多种选择器
    selectors = [
        "h1.drug-title",
        "h1.detail-title",
        "h1",
        ".drug-name",
        ".title"
    ]
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            # 清理标题
            text = re.sub(r"\s*-\s*医脉通.*$", "", text)
            text = re.sub(r"\s*-\s*药品参考.*$", "", text)
            if text and text not in ["药品详情", ""]:
                return text
    return "未知药品"


def extract_section_content(soup: BeautifulSoup, section_title: str) -> Optional[str]:
    """提取指定区块的内容"""
    # 查找包含标题的元素
    for elem in soup.find_all(["h2", "h3", "h4", "div"], class_=re.compile("title|heading|section", re.I)):
        if section_title in elem.get_text():
            # 获取后续内容
            content_parts = []
            current = elem.find_next_sibling()
            while current:
                if current.name in ["h1", "h2", "h3", "h4"]:
                    if current != elem:
                        break
                text = current.get_text(strip=True)
                if text and len(text) > 2:
                    content_parts.append(text)
                current = current.find_next_sibling()
                if len(content_parts) > 5:  # 限制数量
                    break
            return "\n".join(content_parts) if content_parts else None
    return None


def parse_drug_detail(html: str, detail_id: str) -> Optional[Dict]:
    """解析药品详情页面"""
    soup = BeautifulSoup(html, 'html.parser')

    # 提取药品名称
    drug_name = extract_drug_name(soup)

    # 提取通用名和商品名
    generic_name = None
    brand_names = []
    for elem in soup.find_all(text=re.compile("通用名|商品名|英文名")):
        parent = elem.parent
        if parent:
            text = parent.get_text(strip=True)
            if "通用名" in text:
                match = re.search(r"通用名[：:]\s*([^\s]+(?:\s+[^\s]+)*)", text)
                if match:
                    generic_name = match.group(1)
            if "商品名" in text:
                match = re.search(r"商品名[：:]\s*([^\n]+)", text)
                if match:
                    brands = match.group(1).strip(" 、；;，")
                    brand_names = [b.strip() for b in brands.split("、") if b.strip()]

    # 提取适应症
    indications = extract_section_content(soup, "适应症") or extract_section_content(soup, "功能主治")
    if not indications:
        # 尝试从页面内容中提取
        for elem in soup.find_all(["div", "section"], class_=re.compile("indications|indication", re.I)):
            indications = elem.get_text(strip=True)
            break

    # 提取禁忌症
    contraindications = extract_section_content(soup, "禁忌")
    # 提取用法用量
    dosage = extract_section_content(soup, "用法用量") or extract_section_content(soup, "用量")
    # 提取不良反应
    side_effects = extract_section_content(soup, "不良反应") or extract_section_content(soup, "副作用")
    # 提取注意事项
    precautions = extract_section_content(soup, "注意事项") or extract_section_content(soup, "注意")
    # 提取药物相互作用
    interactions = extract_section_content(soup, "药物相互作用") or extract_section_content(soup, "相互作用")
    # 提取贮藏
    storage = extract_section_content(soup, "贮藏") or extract_section_content(soup, "储存")

    # 提取孕妇/哺乳期信息
    pregnancy_info = extract_section_content(soup, "孕妇及哺乳期") or extract_section_content(soup, "妊娠")
    pregnancy_level, pregnancy_desc = parse_pregnancy_level(pregnancy_info)
    lactation_level, lactation_desc = parse_lactation_level(pregnancy_info)

    # 判断儿童可用性
    children_usable = None
    children_desc = None
    if pregnancy_info:
        if "儿童" in pregnancy_info or "小儿" in pregnancy_info:
            if "禁用" in pregnancy_info or "不宜" in pregnancy_info:
                children_usable = False
                children_desc = "儿童禁用或慎用"
            elif "减量" in pregnancy_info or "遵医嘱" in pregnancy_info:
                children_usable = True
                children_desc = "儿童需遵医嘱使用"

    # 提取分类
    category_elem = soup.find(text=re.compile("药品分类|类别"))
    category_name = None
    if category_elem and category_elem.parent:
        category_text = category_elem.parent.get_text(strip=True)
        match = re.search(r"药品分类[：:]\s*([^\s]+(?:\s+[^\s]+)*)", category_text)
        if match:
            raw_category = match.group(1)
            category_name = CATEGORY_MAPPING.get(raw_category, raw_category)

    return {
        "detail_id": detail_id,
        "name": drug_name,
        "generic_name": generic_name,
        "common_brands": ", ".join(brand_names) if brand_names else None,
        "indications": indications or "详见说明书",
        "contraindications": contraindications or "详见说明书",
        "dosage": dosage or "详见说明书",
        "side_effects": side_effects or "详见说明书",
        "precautions": precautions or "详见说明书",
        "interactions": interactions or "详见说明书",
        "storage": storage or "密闭，在阴凉干燥处保存",
        "pregnancy_level": pregnancy_level,
        "pregnancy_desc": pregnancy_desc,
        "lactation_level": lactation_level,
        "lactation_desc": lactation_desc,
        "children_usable": children_usable,
        "children_desc": children_desc,
        "category_name": category_name,
        "url": f"https://drugs.medlive.cn/v2/drugref/detail/info?detailId={detail_id}",
        "source": "医脉通"
    }


class MedLiveDrugCrawler:
    """医脉通药品爬虫"""

    def __init__(self, cookie: str = None):
        self.cookie = cookie or os.getenv("MEDLIVE_DRUG_COOKIE", "")
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        if self.cookie:
            self.client.headers["Cookie"] = self.cookie
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

    def fetch_drug_detail(self, detail_id: str) -> Optional[str]:
        """获取药品详情页面"""
        url = f"https://drugs.medlive.cn/v2/drugref/detail/info?detailId={detail_id}"

        for attempt in range(3):
            try:
                response = self.client.get(url)
                if response.status_code == 200:
                    # 检查是否是登录页面
                    if "登录" in response.text[:1000] or "会员登录" in response.text[:1000]:
                        print(f"  ⚠ Cookie 已失效，需要更新")
                        return None
                    return response.text
                else:
                    print(f"  ⚠ HTTP {response.status_code}")
            except Exception as e:
                print(f"  ⚠ 请求失败 (尝试 {attempt + 1}/3): {e}")
                if attempt < 2:
                    time.sleep(2)

        return None

    def save_to_database(self, data: Dict, db: Session) -> bool:
        """保存到数据库"""
        try:
            # 检查是否已存在（通过名称或 detail_id）
            existing = db.query(Drug).filter(
                (Drug.name == data["name"]) | (Drug.aliases.contains(data["detail_id"]))
            ).first()

            if existing:
                # 更新
                existing.indications = data["indications"]
                existing.contraindications = data["contraindications"]
                existing.dosage = data["dosage"]
                existing.side_effects = data["side_effects"]
                existing.precautions = data["precautions"]
                if data["pregnancy_level"]:
                    existing.pregnancy_level = data["pregnancy_level"]
                if data["lactation_level"]:
                    existing.lactation_level = data["lactation_level"]
                existing.is_active = True
                print(f"  ✓ 更新现有记录: {data['name']}")
            else:
                # 创建新药品记录
                drug = Drug(
                    name=data["name"],
                    pinyin=data["name"].lower(),
                    pinyin_abbr=get_pinyin_abbr(data["name"]),
                    common_brands=data.get("common_brands"),
                    indications=data["indications"],
                    contraindications=data["contraindications"],
                    dosage=data["dosage"],
                    side_effects=data["side_effects"],
                    precautions=data["precautions"],
                    interactions=data["interactions"],
                    storage=data["storage"],
                    pregnancy_level=data.get("pregnancy_level"),
                    pregnancy_desc=data.get("pregnancy_desc"),
                    lactation_level=data.get("lactation_level"),
                    lactation_desc=data.get("lactation_desc"),
                    children_usable=data.get("children_usable"),
                    children_desc=data.get("children_desc"),
                    is_hot=True,
                    is_active=True,
                    view_count=0
                )

                # 处理分类
                category_name = data.get("category_name")
                if category_name:
                    category = db.query(DrugCategory).filter(
                        DrugCategory.name == category_name
                    ).first()
                    if not category:
                        category = DrugCategory(
                            name=category_name,
                            description=category_name,
                            icon="pills.fill",
                            display_type="grid"
                        )
                        db.add(category)
                        db.flush()
                    drug.categories = [category]

                db.add(drug)
                print(f"  ✓ 新增: {data['name']}")

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"  ✗ 保存失败: {e}")
            return False

    def crawl_one(self, detail_id: str, db: Session) -> bool:
        """爬取单个药品"""
        print(f"正在爬取 detailId={detail_id}...")

        html = self.fetch_drug_detail(detail_id)
        if not html:
            print(f"  ✗ 获取页面失败")
            return False

        data = parse_drug_detail(html, detail_id)
        if not data or data.get("name") == "未知药品":
            print(f"  ✗ 解析失败")
            return False

        return self.save_to_database(data, db)

    def crawl_all(self, detail_ids: List[str], db: Session):
        """爬取所有药品"""
        print(f"开始爬取 {len(detail_ids)} 个药品...")
        print("-" * 50)

        success_count = 0
        fail_count = 0

        for i, detail_id in enumerate(detail_ids, 1):
            print(f"[{i}/{len(detail_ids)}] ", end="")

            if self.crawl_one(detail_id, db):
                success_count += 1
            else:
                fail_count += 1

            # 延迟，避免请求过快
            if i < len(detail_ids):
                time.sleep(1)

        print("-" * 50)
        print(f"完成! 成功: {success_count}, 失败: {fail_count}")

    def close(self):
        """关闭客户端"""
        self.client.close()


# 示例药品 detailId（需要手动收集或从搜索页面获取）
SAMPLE_DRUG_IDS = [
    "4adae13be2c445f389f058211eacca9e",  # 用户提供的示例
    # 更多 ID 需要从搜索页面收集
]


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MedLive 药品爬虫")
    parser.add_argument("--detail-ids", nargs="*", default=SAMPLE_DRUG_IDS,
                        help="要爬取的 detailId 列表")
    parser.add_argument("--file", type=str,
                        help="从文件读取 detailId 列表（每行一个）")
    parser.add_argument("--cookie", type=str,
                        help="MedLive Cookie（或设置环境变量 MEDLIVE_DRUG_COOKIE）")

    args = parser.parse_args()

    # 处理 detailId 列表
    if args.file:
        with open(args.file, 'r') as f:
            detail_ids = [line.strip() for line in f if line.strip()]
    else:
        detail_ids = args.detail_ids

    if not detail_ids:
        print("错误: 请提供至少一个 detailId")
        print("用法: python drug_crawler.py --detail-ids xxx yyy")
        print("     python drug_crawler.py --file drug_ids.txt")
        return

    # 创建数据库表
    print("初始化数据库...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 使用命令行提供的 Cookie 或环境变量
        cookie = args.cookie or os.getenv("MEDLIVE_DRUG_COOKIE")
        if not cookie:
            print("警告: 未提供 Cookie，可能无法访问")
            print("请通过 --cookie 参数或设置环境变量 MEDLIVE_DRUG_COOKIE")
            print("或者在浏览器中登录后复制 Cookie")

        crawler = MedLiveDrugCrawler(cookie=cookie)
        try:
            crawler.crawl_all(detail_ids, db)
        finally:
            crawler.close()

    finally:
        db.close()


if __name__ == "__main__":
    main()
