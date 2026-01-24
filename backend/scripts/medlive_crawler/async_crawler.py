"""
MedLive 医脉通爬虫 - 并发版本
使用 httpx 异步客户端批量爬取疾病数据
"""
import asyncio
import sys
import os
import time
import json
from pathlib import Path
from typing import List, Set, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from sqlalchemy.orm import Session
from tqdm import tqdm

from app.database import SessionLocal, engine, Base
from app.models.disease import Disease
from app.models.department import Department
from parser import parse_html_to_sections
from config import MEDLIVE_COOKIE


class AsyncMedLiveCrawler:
    """医脉通异步爬虫"""

    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
        self.results = []
        self.failed_ids = []

    async def fetch_html(self, client: httpx.AsyncClient, wiki_id: str) -> Optional[str]:
        """获取疾病页面 HTML"""
        url = f"https://yzy.medlive.cn/pc/wikiDetail?wiki_id={wiki_id}"

        for attempt in range(3):
            try:
                response = await client.get(url, timeout=30)
                if response.status_code == 200:
                    # 检查是否是登录页面
                    if "登录" in response.text[:1000] or "会员登录" in response.text[:1000]:
                        print(f"  ⚠ Cookie 已失效，需要更新 (wiki_id={wiki_id})")
                        return None
                    return response.text
                else:
                    print(f"  ⚠ HTTP {response.status_code} (wiki_id={wiki_id})")
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)

        return None

    def parse_disease(self, wiki_id: str, html: str) -> Optional[dict]:
        """解析疾病数据"""
        try:
            return parse_html_to_sections(html, wiki_id)
        except Exception as e:
            print(f"  ⚠ 解析失败 (wiki_id={wiki_id}): {e}")
            return None

    def save_to_database(self, data: dict, db: Session) -> bool:
        """保存到数据库"""
        try:
            # 截断过长的字段以适应数据库限制
            max_name_length = 100

            name = data["name"][:max_name_length] if len(data["name"]) > max_name_length else data["name"]

            existing = db.query(Disease).filter(Disease.wiki_id == data["wiki_id"]).first()

            if existing:
                existing.name = name
                existing.url = data["url"]
                existing.source = data["source"]
                existing.sections = data["sections"]
                existing.is_active = True
            else:
                disease = Disease(
                    name=name,
                    wiki_id=data["wiki_id"],
                    url=data["url"],
                    source=data["source"],
                    sections=data["sections"],
                    department_id=None,
                    is_active=True,
                    is_hot=False
                )
                db.add(disease)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"  ✗ 保存失败 (wiki_id={data['wiki_id']}): {e}")
            return False

    async def crawl_one(self, client: httpx.AsyncClient, wiki_id: str, db: Session, semaphore: asyncio.Semaphore):
        """爬取单个疾病"""
        async with semaphore:
            html = await self.fetch_html(client, wiki_id)
            if not html:
                self.failed_ids.append(wiki_id)
                return wiki_id, False

            data = self.parse_disease(wiki_id, html)
            if not data:
                self.failed_ids.append(wiki_id)
                return wiki_id, False

            # 在同步上下文中保存到数据库
            success = self.save_to_database(data, db)
            return wiki_id, success

    async def crawl_all(self, wiki_ids: List[str], db: Session):
        """并发爬取所有疾病"""
        print(f"开始并发爬取 {len(wiki_ids)} 个疾病 (并发数: {self.max_concurrent})...")
        print("-" * 50)

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # 创建异步客户端
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Cookie": MEDLIVE_COOKIE,
        }

        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            # 创建任务列表
            tasks = [
                self.crawl_one(client, wiki_id, db, semaphore)
                for wiki_id in wiki_ids
            ]

            # 使用 tqdm 显示进度
            success_count = 0
            fail_count = 0

            for coro in asyncio.as_completed(tasks):
                wiki_id, success = await coro
                if success:
                    success_count += 1
                else:
                    fail_count += 1

        print("-" * 50)
        print(f"完成! 成功: {success_count}, 失败: {fail_count}")

        if self.failed_ids:
            print(f"\n失败的 ID ({len(self.failed_ids)} 个):")
            print(f"  {self.failed_ids[:20]}...")


def load_wiki_ids(file_path: str = None) -> List[str]:
    """加载 wiki_id 列表"""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    # 默认使用 fetch_all_wiki_ids.py 生成的文件（在 backend 根目录）
    default_file = os.path.join(os.path.dirname(__file__), "..", "..", "wiki_ids.txt")
    if os.path.exists(default_file):
        with open(default_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    # 再尝试当前目录
    if os.path.exists("wiki_ids.txt"):
        with open("wiki_ids.txt", 'r') as f:
            return [line.strip() for line in f if line.strip()]

    return []


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="MedLive 疾病爬虫 (并发版)")
    parser.add_argument("--file", type=str, help="wiki_id 列表文件")
    parser.add_argument("--wiki-ids", nargs="*", help="直接指定 wiki_id 列表")
    parser.add_argument("--concurrent", type=int, default=10, help="并发数 (默认 10)")
    parser.add_argument("--limit", type=int, help="限制爬取数量 (用于测试)")

    args = parser.parse_args()

    # 获取 wiki_id 列表
    if args.wiki_ids:
        wiki_ids = args.wiki_ids
    else:
        wiki_ids = load_wiki_ids(args.file)

    if not wiki_ids:
        print("未找到 wiki_id 列表，请先运行 fetch_all_wiki_ids.py 或使用 --wiki-ids 指定")
        print("\n获取所有 wiki_id:")
        print("  python fetch_all_wiki_ids.py")
        return

    # 限制数量
    if args.limit:
        wiki_ids = wiki_ids[:args.limit]

    # 初始化数据库
    print("初始化数据库...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        crawler = AsyncMedLiveCrawler(max_concurrent=args.concurrent)
        await crawler.crawl_all(wiki_ids, db)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
