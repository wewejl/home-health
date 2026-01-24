"""
MedLive 医脉通爬虫 - 主入口
一次性爬取疾病数据并导入数据库
"""
import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
from app.models.disease import Disease
from app.models.department import Department
from parser import parse_html_to_sections, parse_raw_text
from config import (
    MEDLIVE_COOKIE,
    BASE_URL,
    WIKI_IDS,
    REQUEST_TIMEOUT,
    DELAY_BETWEEN_REQUESTS,
    MAX_RETRIES
)


class MedLiveCrawler:
    """医脉通爬虫"""

    def __init__(self):
        self.client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Cookie": MEDLIVE_COOKIE,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
        )
        self.results = []

    def fetch_html(self, wiki_id: str) -> Optional[str]:
        """获取疾病页面 HTML"""
        url = BASE_URL.format(wiki_id=wiki_id)

        for attempt in range(MAX_RETRIES):
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
                print(f"  ⚠ 请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)

        return None

    def parse_disease(self, wiki_id: str, html: str) -> Optional[Dict]:
        """解析疾病数据"""
        try:
            data = parse_html_to_sections(html, wiki_id)
            return data
        except Exception as e:
            print(f"  ⚠ 解析失败: {e}")
            return None

    def save_to_database(self, data: Dict, db: Session) -> bool:
        """保存到数据库"""
        try:
            # 检查是否已存在
            existing = db.query(Disease).filter(Disease.wiki_id == data["wiki_id"]).first()

            if existing:
                # 更新
                existing.name = data["name"]
                existing.english_name = data.get("english_name")
                existing.aliases = data.get("aliases")
                existing.url = data["url"]
                existing.source = data["source"]
                existing.sections = data["sections"]
                existing.is_active = True
                print(f"  ✓ 更新现有记录: {data['name']}")
            else:
                # 创建新记录
                disease = Disease(
                    name=data["name"],
                    english_name=data.get("english_name"),
                    aliases=data.get("aliases"),
                    wiki_id=data["wiki_id"],
                    url=data["url"],
                    source=data["source"],
                    sections=data["sections"],
                    department_id=None,  # 可以后续映射
                    is_active=True,
                    is_hot=False
                )
                db.add(disease)
                print(f"  ✓ 新增: {data['name']}")

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"  ✗ 保存失败: {e}")
            return False

    def crawl_one(self, wiki_id: str, db: Session) -> bool:
        """爬取单个疾病"""
        print(f"正在爬取 wiki_id={wiki_id}...")

        html = self.fetch_html(wiki_id)
        if not html:
            print(f"  ✗ 获取页面失败")
            return False

        data = self.parse_disease(wiki_id, html)
        if not data:
            print(f"  ✗ 解析失败")
            return False

        return self.save_to_database(data, db)

    def crawl_all(self, wiki_ids: List[str], db: Session):
        """爬取所有疾病"""
        print(f"开始爬取 {len(wiki_ids)} 个疾病...")
        print("-" * 50)

        success_count = 0
        fail_count = 0

        for i, wiki_id in enumerate(wiki_ids, 1):
            print(f"[{i}/{len(wiki_ids)}] ", end="")

            if self.crawl_one(wiki_id, db):
                success_count += 1
            else:
                fail_count += 1

            # 延迟，避免请求过快
            if i < len(wiki_ids):
                time.sleep(DELAY_BETWEEN_REQUESTS)

        print("-" * 50)
        print(f"完成! 成功: {success_count}, 失败: {fail_count}")

    def close(self):
        """关闭客户端"""
        self.client.close()


def load_sample_data() -> List[Dict]:
    """加载示例数据（三尖瓣疾病）"""
    return [
        {
            "wiki_id": "90",
            "name": "三尖瓣疾病",
            "english_name": "Tricuspid Valve Disease",
            "aliases": "TR, TS",
            "url": "https://yzy.medlive.cn/pc/wikiDetail?wiki_id=90",
            "source": "医脉通",
            "sections": [
                {
                    "id": "overview",
                    "title": "疾病简介",
                    "icon": "info.circle",
                    "content": "三尖瓣疾病指三尖瓣的瓣膜、腱索、乳头肌和瓣环，以及右心房和右心室出现解剖结构和功能异常导致的血流动力学改变。三尖瓣不能完全闭合为三尖瓣关闭不全（TR），三尖瓣开放受限则为三尖瓣狭窄（TS）。",
                    "items": [
                        {
                            "id": "1",
                            "title": "主要症状",
                            "content": "体循环淤血，三尖瓣关闭不全晚期发生右心衰竭，TS早期即可出现。表现为颈静脉充盈和搏动、食欲不振、恶心、呕吐、上腹饱胀感、黄疸、脚踝和小腿肿胀等。",
                            "level": 0
                        },
                        {
                            "id": "2",
                            "title": "分类",
                            "content": "根据病因把三尖瓣关闭不全分为原发性（器质性，三尖瓣结构异常）和继发性（功能性，继发于肺动脉高压和右心病变）。",
                            "level": 0
                        },
                        {
                            "id": "3",
                            "title": "病因",
                            "content": "风湿热是三尖瓣狭窄最常见的病因，其他原因少见。",
                            "level": 0
                        },
                        {
                            "id": "4",
                            "title": "诊断",
                            "content": "典型的体征和超声心动图表现可明确诊断。",
                            "level": 0
                        },
                        {
                            "id": "5",
                            "title": "治疗原则",
                            "content": "改善患者的症状和心肺功能情况，控制并发症，提高生活质量，增加预期寿命。",
                            "level": 0
                        }
                    ]
                },
                {
                    "id": "definition",
                    "title": "定义",
                    "icon": "text.book.closed",
                    "content": "三尖瓣疾病指三尖瓣的瓣膜、腱索、乳头肌和瓣环，以及右心房和右心室出现解剖结构和功能异常导致的血流动力学改变。",
                    "items": [
                        {
                            "id": "tr",
                            "title": "三尖瓣关闭不全 (TR)",
                            "content": "三尖瓣不能完全闭合，导致收缩期血液从右心室反流至右心房。",
                            "level": 1
                        },
                        {
                            "id": "ts",
                            "title": "三尖瓣狭窄 (TS)",
                            "content": "三尖瓣开放受限，导致舒张期血液从右心房流入右心室受阻。",
                            "level": 1
                        }
                    ]
                },
                {
                    "id": "classification",
                    "title": "疾病分类",
                    "icon": "square.grid.2x2",
                    "items": [
                        {
                            "id": "primary",
                            "title": "原发性（器质性）TR",
                            "content": "三尖瓣结构异常，占TR的10%～30%",
                            "level": 0
                        },
                        {
                            "id": "secondary",
                            "title": "继发性（功能性）TR",
                            "content": "继发于肺动脉高压和右心病变，占TR的70%～90%。常见于左心疾病（冠心病、瓣膜性心脏病、心肌病等）晚期引发的肺动脉高压和右心室功能障碍。",
                            "level": 0
                        }
                    ]
                },
                {
                    "id": "epidemiology",
                    "title": "流行病学",
                    "icon": "chart.bar",
                    "items": [
                        {
                            "id": "incidence",
                            "title": "TR发病率",
                            "content": "TR非常常见，发生率为65%～85%。在结构正常的三尖瓣中，轻度TR可以认为是正常的。",
                            "level": 0
                        },
                        {
                            "id": "survival",
                            "title": "生存率",
                            "content": "无TR患者1年生存率为91.7%，轻度TR为90.3%，中度TR为78.9%，重度TR为63.9%。中度和重度TR的1年生存率明显下降。",
                            "level": 0
                        },
                        {
                            "id": "severe",
                            "title": "重度TR发生率",
                            "content": "在国内老年人中，重度TR发生率为1.1%。",
                            "level": 0
                        }
                    ]
                },
                {
                    "id": "causes",
                    "title": "病因",
                    "icon": "cross.case",
                    "content": "三尖瓣疾病的病因多样。",
                    "items": [
                        {
                            "id": "tr_primary",
                            "title": "原发性TR病因",
                            "content": "三尖瓣脱垂、Ebstein畸形、类癌综合征、心内膜炎、起搏器/除颤器电极相关、外伤、风湿热。",
                            "level": 1
                        },
                        {
                            "id": "tr_secondary",
                            "title": "继发性TR病因",
                            "content": "左心疾病导致的肺动脉高压、右心室梗死、右心室扩张、肺动脉栓塞、房颤。",
                            "level": 1
                        },
                        {
                            "id": "ts_cause",
                            "title": "TS病因",
                            "content": "风湿热是TS最常见的病因，其他原因少见。",
                            "level": 1
                        }
                    ]
                },
                {
                    "id": "symptoms",
                    "title": "症状与体征",
                    "icon": "stethoscope",
                    "content": "TR可长期无症状，TS早期即可出现症状。",
                    "items": [
                        {
                            "id": "sys_symptoms",
                            "title": "体循环淤血症状",
                            "content": "TR晚期发生右心衰竭，TS早期即可出现。表现为：颈静脉充盈和搏动、食欲不振、恶心、呕吐、上腹饱胀感、黄疸、脚踝和小腿肿胀等。",
                            "level": 0
                        },
                        {
                            "id": "auscultation_tr",
                            "title": "TR听诊",
                            "content": "三尖瓣区全收缩期杂音，吸气和压迫肝脏后杂音可增强。三尖瓣脱垂可闻及三尖瓣区非喷射样喀喇音。",
                            "level": 0
                        },
                        {
                            "id": "auscultation_ts",
                            "title": "TS听诊",
                            "content": "三尖瓣区舒张中晚期低调隆隆样杂音，吸气末增强，呼气或Valsalva动作时减弱，可伴震颤。",
                            "level": 0
                        }
                    ]
                },
                {
                    "id": "diagnosis",
                    "title": "诊断",
                    "icon": "stethoscope",
                    "content": "超声心动图是诊断和评估TS和TR反流程度的首选检查手段。",
                    "items": [
                        {
                            "id": "echo_m",
                            "title": "M型超声",
                            "content": "TR：室间隔运动幅度低平或与左心室后壁呈同向运动。TS：EF斜率减低，前后叶同向运动。",
                            "level": 1
                        },
                        {
                            "id": "echo_2d",
                            "title": "二维超声",
                            "content": "TR：瓣缘增厚，呈「鼓槌状」。TS：风湿性可见瓣尖增厚和交界粘连，舒张期开放受限。",
                            "level": 1
                        },
                        {
                            "id": "echo_doppler",
                            "title": "多普勒超声",
                            "content": "可测量跨瓣压差、反流束面积等参数。",
                            "level": 1
                        }
                    ]
                },
                {
                    "id": "treatment",
                    "title": "治疗",
                    "icon": "pills",
                    "content": "治疗原则是改善患者的症状和心肺功能情况，控制并发症，提高生活质量。",
                    "items": [
                        {
                            "id": "medical",
                            "title": "药物治疗",
                            "content": "主要针对右心衰竭症状进行治疗，包括利尿剂、醛固酮受体拮抗剂等。",
                            "level": 0
                        },
                        {
                            "id": "surgical",
                            "title": "手术治疗",
                            "content": "如果药物能控制好右心衰竭，不出现临床症状，不影响生活质量，那么不需要做手术。如果TR相关的右心衰竭不能控制，或者反复复发，可以经过外科手术团队评估后进行手术治疗。",
                            "level": 0
                        }
                    ]
                },
                {
                    "id": "followup",
                    "title": "复诊与随访",
                    "icon": "calendar",
                    "items": [
                        {
                            "id": "mild_followup",
                            "title": "轻度TR和TS",
                            "content": "每2年临床随访，复查超声心动图和心电图。",
                            "level": 0
                        },
                        {
                            "id": "severe_followup",
                            "title": "中重度TR和TS",
                            "content": "每年临床随访，复查超声心动图。",
                            "level": 0
                        }
                    ]
                }
            ]
        }
    ]


def import_sample_data(db: Session):
    """导入示例数据（用于测试）"""
    print("导入示例数据（三尖瓣疾病）...")

    sample_diseases = load_sample_data()

    for data in sample_diseases:
        try:
            # 检查是否已存在
            existing = db.query(Disease).filter(Disease.wiki_id == data["wiki_id"]).first()

            if existing:
                existing.name = data["name"]
                existing.english_name = data.get("english_name")
                existing.aliases = data.get("aliases")
                existing.url = data["url"]
                existing.source = data["source"]
                existing.sections = data["sections"]
                existing.is_active = True
                print(f"  ✓ 更新: {data['name']}")
            else:
                disease = Disease(
                    name=data["name"],
                    english_name=data.get("english_name"),
                    aliases=data.get("aliases"),
                    wiki_id=data["wiki_id"],
                    url=data["url"],
                    source=data["source"],
                    sections=data["sections"],
                    is_active=True
                )
                db.add(disease)
                print(f"  ✓ 新增: {data['name']}")

            db.commit()

        except Exception as e:
            db.rollback()
            print(f"  ✗ 失败: {e}")

    print("示例数据导入完成!")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MedLive 疾病爬虫")
    parser.add_argument("--mode", choices=["crawl", "sample"], default="sample",
                        help="运行模式: crawl=爬取指定ID, sample=导入示例数据")
    parser.add_argument("--wiki-ids", nargs="*", default=WIKI_IDS,
                        help="要爬取的 wiki_id 列表")
    parser.add_argument("--file", type=str,
                        help="从文件读取 wiki_id 列表（每行一个）")

    args = parser.parse_args()

    # 处理 wiki_id 列表
    if args.file:
        with open(args.file, 'r') as f:
            wiki_ids = [line.strip() for line in f if line.strip()]
    else:
        wiki_ids = args.wiki_ids

    # 创建数据库表
    print("初始化数据库...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        if args.mode == "sample":
            # 导入示例数据
            import_sample_data(db)
        else:
            # 爬取指定 ID
            crawler = MedLiveCrawler()
            try:
                crawler.crawl_all(wiki_ids, db)
            finally:
                crawler.close()

    finally:
        db.close()


if __name__ == "__main__":
    main()
