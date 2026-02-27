"""
MSD 诊疗手册爬虫 V2
使用 Playwright 来爬取动态内容
"""
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page
import time


class MSDManualsCrawlerV2:
    """MSD 诊疗手册爬虫 V2 - 使用 Playwright"""

    BASE_URL = "https://www.msdmanuals.cn"
    PROFESSIONAL_PATH = "/professional"

    # 医学主题分类映射
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
    }

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.results: List[Dict[str, Any]] = []

    async def init_browser(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.webkit.launch(
            headless=True,
        )
        self.page = await self.browser.new_page()

        # 设置用户代理
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
        })

    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_health_topics(self) -> List[Dict[str, str]]:
        """获取所有医学主题分类"""
        url = f"{self.BASE_URL}{self.PROFESSIONAL_PATH}/health-topics"
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)  # 等待动态内容加载

        # 获取页面内容
        topics = []

        # 尝试通过 JavaScript 获取链接
        links_data = await self.page.evaluate("""
            () => {
                const links = [];
                const elements = document.querySelectorAll('a[href*="/professional/"]');
                elements.forEach(el => {
                    const href = el.getAttribute('href');
                    const text = el.textContent?.trim();
                    if (href && text && text.length > 0 && text.length < 50) {
                        links.push({ href, text });
                    }
                });
                return links;
            }
        """)

        # 过滤出医学专业分类
        seen = set()
        for link in links_data:
            href = link['href']
            text = link['text']

            # 只取一级分类
            if href.startswith(self.PROFESSIONAL_PATH + '/'):
                path = href[len(self.PROFESSIONAL_PATH)+1:]

                # 检查是否是一级分类（只有一个路径段）
                if '/' not in path and '?' not in path and '#' not in path:
                    if text not in seen and text not in ['医学主题', '资源', '测验']:
                        seen.add(text)
                        topics.append({
                            "name": text,
                            "url": f"{self.BASE_URL}{href}",
                            "path": path
                        })

        return topics

    async def get_diseases_from_section(self, section_url: str, specialty: str) -> List[Dict[str, Any]]:
        """从某个分类获取疾病列表"""
        await self.page.goto(section_url, wait_until="networkidle")
        await asyncio.sleep(2)

        # 展开全部
        try:
            expand_button = await self.page.query_selector('button:has-text("展开全部")')
            if expand_button:
                await expand_button.click()
                await asyncio.sleep(1)
        except:
            pass

        # 获取导航树中的所有链接
        diseases_data = await self.page.evaluate("""
            () => {
                const diseases = [];
                const nav = document.querySelector('[role="navigation"] nav, nav tree, .navigation');
                if (nav) {
                    const links = nav.querySelectorAll('a[href]');
                    links.forEach(el => {
                        const href = el.getAttribute('href');
                        const text = el.textContent?.trim();
                        if (href && text && text.length > 1 && text.length < 100) {
                            // 排除通用链接
                            if (!['关于', '测验', '免责声明', '许可权限'].includes(text)) {
                                diseases.push({ href, text });
                            }
                        }
                    });
                }
                return diseases;
            }
        """)

        diseases = []
        seen = set()

        for disease_data in diseases_data:
            href = disease_data['href']
            text = disease_data['text']

            # 确保是当前分类下的子页面
            if href.startswith(self.PROFESSIONAL_PATH + '/'):
                full_url = f"{self.BASE_URL}{href}"

                # 只取二级及以上页面
                path = href[len(self.PROFESSIONAL_PATH)+1:]
                if '/' in path and full_url not in seen:
                    seen.add(full_url)
                    diseases.append({
                        "name": text,
                        "url": full_url,
                        "specialty": specialty
                    })

        return diseases

    async def get_disease_content(self, disease_url: str, disease_name: str, specialty: str) -> Optional[Dict[str, Any]]:
        """获取疾病详细内容"""
        try:
            await self.page.goto(disease_url, wait_until="networkidle")
            await asyncio.sleep(1)

            # 获取主要内容
            content_data = await self.page.evaluate("""
                () => {
                    // 尝试多种选择器
                    const selectors = [
                        'article',
                        'main [role="main"]',
                        '.manual-content',
                        '.topic-content',
                        '#mainContent',
                        'main'
                    ];

                    for (const selector of selectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            // 获取所有段落
                            const paragraphs = el.querySelectorAll('p, h1, h2, h3, h4, li');
                            if (paragraphs.length > 3) {
                                const text = Array.from(paragraphs)
                                    .map(p => p.textContent?.trim())
                                    .filter(t => t && t.length > 5)
                                    .join('\\n\\n');
                                return text;
                            }
                        }
                    }

                    // 如果上面没找到，尝试获取 body 内容
                    const body = document.querySelector('body');
                    if (body) {
                        // 移除导航和页脚
                        const toRemove = body.querySelectorAll('nav, footer, header, [role="navigation"], [role="banner"], [role="contentinfo"]');
                        toRemove.forEach(el => el.remove());

                        const paragraphs = body.querySelectorAll('p, h1, h2, h3, h4, li, div');
                        const text = Array.from(paragraphs)
                            .map(p => p.textContent?.trim())
                            .filter(t => t && t.length > 5)
                            .join('\\n\\n');
                        return text;
                    }

                    return '';
                }
            """)

            if not content_data or len(content_data) < 100:
                return None

            # 清理内容
            content_text = re.sub(r'\n{3,}', '\n\n', content_data)
            content_text = content_text[:5000]  # 限制长度

            return {
                "name": disease_name,
                "url": disease_url,
                "specialty": specialty,
                "content": content_text,
            }

        except Exception as e:
            print(f"    Error: {e}")
            return None

    async def crawl_all(self, max_per_specialty: int = 10) -> List[Dict[str, Any]]:
        """爬取所有医学知识"""
        await self.init_browser()

        print("正在获取医学主题分类...")
        topics = await self.get_health_topics()
        print(f"找到 {len(topics)} 个医学主题分类")

        # 过滤出我们需要的专科
        target_specialties = set(self.SPECIALTY_MAPPING.keys())
        topics = [t for t in topics if t['name'] in target_specialties]

        print(f"其中目标专科: {len(topics)} 个\n")

        all_results = []

        for topic in topics:
            specialty_code = self.SPECIALTY_MAPPING.get(topic['name'], topic['path'])

            print(f"正在处理分类: {topic['name']} ({specialty_code})")

            # 获取该分类下的疾病列表
            diseases = await self.get_diseases_from_section(topic['url'], specialty_code)
            print(f"  找到 {len(diseases)} 个疾病")

            # 限制每个分类爬取的数量
            diseases = diseases[:max_per_specialty]

            for i, disease in enumerate(diseases):
                print(f"  [{i+1}/{len(diseases)}] 爬取: {disease['name'][:30]}")

                content_data = await self.get_disease_content(
                    disease['url'],
                    disease['name'],
                    specialty_code
                )

                if content_data:
                    all_results.append(content_data)
                    print(f"    ✓ 成功")
                else:
                    print(f"    ✗ 失败")

                # 延迟避免请求过快
                await asyncio.sleep(0.3)

        await self.close_browser()
        return all_results

    def convert_to_knowledge_base(self, crawled_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将爬取的数据转换为知识库格式"""
        knowledge_base = []

        for item in crawled_data:
            # 生成 ICD-10 代码（使用模拟代码）
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

            knowledge_base.append({
                "code": code,
                "name": item['name'],
                "specialty": item['specialty'],
                "keywords": keywords,
                "content": f"""
# {item['name']} ({code})

{item['content']}

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
    crawler = MSDManualsCrawlerV2()

    print("=" * 60)
    print("MSD 诊疗手册爬虫 V2 (Playwright)")
    print("=" * 60)

    # 爬取数据
    crawled_data = await crawler.crawl_all(max_per_specialty=5)

    print(f"\n共爬取 {len(crawled_data)} 条医学知识")

    if not crawled_data:
        print("没有成功爬取到数据，请检查网络或爬虫逻辑")
        return

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
