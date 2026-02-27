"""
MSD 诊疗手册爬虫
爬取 https://www.msdmanuals.cn/professional 的医学知识内容
"""
import asyncio
import aiohttp
import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time


class MSDManualsCrawler:
    """MSD 诊疗手册爬虫"""

    BASE_URL = "https://www.msdmanuals.cn"
    PROFESSIONAL_PATH = "/professional"

    # 医学主题分类映射到我们的专科代码
    SPECIALTY_MAPPING = {
        "心血管疾病": "cardiology",
        "皮肤科疾病": "dermatology",
        "肺部疾病": "respiratory",
        "消化道疾病": "gastroenterology",
        "神经系统疾病": "neurology",
        "内分泌及代谢紊乱": "endocrinology",
        "肌肉骨骼及结缔组织疾病": "orthopedics",
        "眼部疾病": "ophthalmology",
        "耳鼻咽喉疾病": "otorhinolaryngology",
        "妇产科学": "obstetrics_gynecology",
        "儿科学": "pediatrics",
        "传染病": "infectious_diseases",
        "泌尿生殖系统疾病": "urology",
        "血液病学及肿瘤病学": "hematology_oncology",
        "精神疾病": "psychiatry",
        "口腔疾病": "dentistry",
        "肝脏及胆道疾病": "hepatobiliary",
        "老年病学": "geriatrics",
        "急救医学": "critical_care",
        "临床药理学": "pharmacology",
        "免疫学; 过敏性疾病": "immunology",
        "损伤; 中毒": "trauma",
        "营养性疾病": "nutrition",
        "特殊问题": "special_subjects",
    }

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls = set()
        self.results: List[Dict[str, Any]] = []

    async def init_session(self):
        """初始化 HTTP 会话"""
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )

    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        if url in self.visited_urls:
            return None

        self.visited_urls.add(url)

        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"Error fetching {url}: status {response.status}")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def get_health_topics(self) -> List[Dict[str, str]]:
        """获取所有医学主题分类"""
        url = urljoin(self.BASE_URL, f"{self.PROFESSIONAL_PATH}/health-topics")
        html = await self.fetch_page(url)

        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        topics = []

        # 查找所有医学主题链接
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)

            # 检查是否是医学专业分类链接
            if href and href.startswith(f"{self.PROFESSIONAL_PATH}/") and text:
                # 排除一些非专业分类的链接
                if any(excl in href for excl in ['resourcespages', 'content/', 'pages-with']):
                    continue

                # 只取一级分类
                path_parts = href[len(self.PROFESSIONAL_PATH)+1:].split('/')
                if len(path_parts) == 1 and text:
                    full_url = urljoin(self.BASE_URL, href)
                    topics.append({
                        "name": text,
                        "url": full_url,
                        "path": path_parts[0]
                    })

        return topics

    async def get_diseases_from_section(self, section_url: str, specialty: str) -> List[Dict[str, Any]]:
        """从某个分类获取疾病列表"""
        html = await self.fetch_page(section_url)

        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        diseases = []

        # 查找疾病链接 - 在导航树中
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)

            if not href or not text:
                continue

            # 确保是当前分类下的子页面
            if href.startswith(f"{self.PROFESSIONAL_PATH}/"):
                full_url = urljoin(self.BASE_URL, href)

                # 检查是否是具体的疾病页面（通常路径较深）
                path = href[len(self.PROFESSIONAL_PATH)+1:]
                if '/' in path and path.count('/') >= 1:
                    # 避免重复
                    if full_url not in [d['url'] for d in diseases]:
                        diseases.append({
                            "name": text,
                            "url": full_url,
                            "specialty": specialty
                        })

        return diseases

    async def get_disease_content(self, disease_url: str, disease_name: str, specialty: str) -> Optional[Dict[str, Any]]:
        """获取疾病详细内容"""
        html = await self.fetch_page(disease_url)

        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # 尝试提取主要内容
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.manual-content',
        ]

        content_text = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # 获取文本，保留段落结构
                paragraphs = element.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'ul', 'ol'])
                if paragraphs:
                    content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    break

        # 如果没有找到主要内容，尝试获取所有文本
        if not content_text:
            body = soup.find('body')
            if body:
                # 移除导航、页脚等
                for elem in body.find_all(['nav', 'footer', 'header', 'aside']):
                    elem.decompose()
                content_text = body.get_text(separator='\n', strip=True)

        # 清理内容
        content_text = re.sub(r'\n{3,}', '\n\n', content_text)
        content_text = content_text[:5000]  # 限制长度

        if len(content_text) < 100:  # 内容太少，可能是无效页面
            return None

        return {
            "name": disease_name,
            "url": disease_url,
            "specialty": specialty,
            "content": content_text,
        }

    async def crawl_all(self, max_per_specialty: int = 10) -> List[Dict[str, Any]]:
        """爬取所有医学知识"""
        await self.init_session()

        print("正在获取医学主题分类...")
        topics = await self.get_health_topics()
        print(f"找到 {len(topics)} 个医学主题分类")

        all_results = []

        for topic in topics:
            specialty_code = self.SPECIALTY_MAPPING.get(topic['name'], topic['path'])

            print(f"\n正在处理分类: {topic['name']} ({specialty_code})")

            # 获取该分类下的疾病列表
            diseases = await self.get_diseases_from_section(topic['url'], specialty_code)
            print(f"  找到 {len(diseases)} 个疾病")

            # 限制每个分类爬取的数量
            diseases = diseases[:max_per_specialty]

            for i, disease in enumerate(diseases):
                print(f"  [{i+1}/{len(diseases)}] 爬取: {disease['name']}")

                content_data = await self.get_disease_content(
                    disease['url'],
                    disease['name'],
                    specialty_code
                )

                if content_data:
                    all_results.append(content_data)

                # 延迟避免请求过快
                await asyncio.sleep(0.5)

        await self.close_session()
        return all_results

    def convert_to_knowledge_base(self, crawled_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将爬取的数据转换为知识库格式"""
        knowledge_base = []

        for item in crawled_data:
            # 从内容中提取关键信息
            content = item['content']

            # 生成 ICD-10 代码（这里使用模拟代码）
            specialty_prefix = {
                'cardiology': 'I',
                'dermatology': 'L',
                'respiratory': 'J',
                'gastroenterology': 'K',
                'neurology': 'G',
                'endocrinology': 'E',
                'orthopedics': 'M',
                'ophthalmology': 'H',
                'otorhinolaryngology': 'J',
                'obstetrics_gynecology': 'O',
                'pediatrics': 'P',
            }

            prefix = specialty_prefix.get(item['specialty'], 'X')
            code = f"{prefix}{hash(item['name']) % 100:02d}"

            # 生成关键词
            keywords = [item['name']]
            # 从名称中提取一些关键词
            if '病' in item['name']:
                keywords.append(item['name'].replace('病', '').replace('疾病', ''))
            if '症' in item['name']:
                keywords.append(item['name'].replace('症', ''))

            knowledge_base.append({
                "code": code,
                "name": item['name'],
                "specialty": item['specialty'],
                "keywords": keywords,
                "content": f"""
# {item['name']} ({code})

## 概述
{content[:500]}

## 症状
{content[500:1000] if len(content) > 500 else ''}

## 诊断
{content[1000:1500] if len(content) > 1000 else ''}

## 治疗
{content[1500:2000] if len(content) > 1500 else ''}

## 预后
{content[2000:2500] if len(content) > 2000 else ''}

---
来源: MSD诊疗手册专业版
链接: {item['url']}
                """.strip(),
                "source": "msd_manuals",
                "source_url": item['url']
            })

        return knowledge_base


async def main():
    """主函数"""
    crawler = MSDManualsCrawler()

    print("=" * 60)
    print("MSD 诊疗手册爬虫")
    print("=" * 60)

    # 爬取数据（限制每个分类 5 个疾病用于测试）
    crawled_data = await crawler.crawl_all(max_per_specialty=5)

    print(f"\n共爬取 {len(crawled_data)} 条医学知识")

    # 转换为知识库格式
    knowledge_base = crawler.convert_to_knowledge_base(crawled_data)

    # 保存到文件
    output_file = "/Users/zhuxinye/Desktop/project/home-health/medical-knowledge-service/data/msd_knowledge.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    print(f"\n数据已保存到: {output_file}")

    # 按专科统计
    specialty_count = {}
    for item in knowledge_base:
        specialty = item['specialty']
        specialty_count[specialty] = specialty_count.get(specialty, 0) + 1

    print("\n按专科统计:")
    for specialty, count in sorted(specialty_count.items()):
        print(f"  {specialty}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
