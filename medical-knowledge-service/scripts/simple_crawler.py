"""
MSD 诊疗手册爬虫 - 简化版
"""
import asyncio
import json
from playwright.async_api import async_playwright

# MSD 专科映射
SPECIALTY_MAPPING = {
    '心血管疾病': 'cardiology',
    '皮肤科疾病': 'dermatology',
    '肺部疾病': 'respiratory',
    '消化道疾病': 'gastroenterology',
    '神经系统疾病': 'neurology',
    '内分泌及代谢紊乱': 'endocrinology',
    '肌肉骨骼及结缔组织疾病': 'orthopedics',
    '眼部疾病': 'ophthalmology',
    '耳鼻咽喉疾病': 'otorhinolaryngology',
    '妇产科学': 'obstetrics_gynecology',
    '儿科学': 'pediatrics',
}

# 目标专科列表
TARGET_SPECIALTIES = list(SPECIALTY_MAPPING.keys())


async def crawl_diseases(max_per_specialty=5):
    """爬取疾病数据"""
    async with async_playwright() as p:
        browser = await p.webkit.launch(headless=True)
        page = await browser.new_page()

        results = []
        base_url = 'https://www.msdmanuals.cn'

        print('正在获取专科列表...')
        await page.goto(f'{base_url}/professional/health-topics', wait_until='networkidle')
        await asyncio.sleep(2)

        # 获取专科链接
        specialty_links = await page.evaluate('''
            () => {
                const targetNames = ['心血管疾病', '皮肤科疾病', '肺部疾病', '消化道疾病',
                    '神经系统疾病', '内分泌及代谢紊乱', '肌肉骨骼及结缔组织疾病',
                    '眼部疾病', '耳鼻咽喉疾病', '妇产科学', '儿科学'];
                const links = [];
                const allLinks = Array.from(document.querySelectorAll('a[href]'));

                for (const link of allLinks) {
                    const href = link.getAttribute('href');
                    const text = link.textContent?.trim();
                    if (href && href.startsWith('/professional/') &&
                        text && targetNames.includes(text) &&
                        text.length < 20 && text.length > 2) {
                        links.push({name: text, href: href});
                    }
                }
                return links;
            }
        ''')

        print(f'找到 {len(specialty_links)} 个目标专科')

        # 对每个专科，爬取疾病
        for specialty in specialty_links:
            specialty_code = SPECIALTY_MAPPING.get(specialty['name'], 'general')
            print(f'\n处理: {specialty["name"]} ({specialty_code})')

            await page.goto(f'{base_url}{specialty["href"]}', wait_until='networkidle')
            await asyncio.sleep(2)

            # 获取该专科下的疾病链接 - 更精确的过滤
            disease_links = await page.evaluate('''
                () => {
                    const links = [];
                    const allLinks = Array.from(document.querySelectorAll('a[href]'));

                    // 排除关键词
                    const skipWords = ['skip to', '医学主题', '资源', '测验', '在该主题中',
                                      '本章节', '参考文献', '患者培训', '看法',
                                      '体格检查', '病理', '评估', '概述', '原理',
                                      '检查方法', '诊治方法', '处理', '症状'];

                    for (const link of allLinks) {
                        const href = link.getAttribute('href');
                        const text = link.textContent?.trim();

                        // 过滤掉锚点链接（关键修复：避免重复数据）
                        if (!href || href.includes('#')) continue;

                        // 过滤条件：
                        // 1. 有3级或以上路径 /professional/xxx/yyy/zzz
                        // 2. 不在排除列表中
                        // 3. 长度合适
                        if (href.split('/').filter(s => s).length < 4) continue;
                        if (!text || text.length <= 2 || text.length >= 60) continue;

                        // 检查是否包含排除词
                        let shouldSkip = false;
                        for (const skip of skipWords) {
                            if (text.toLowerCase().includes(skip.toLowerCase())) {
                                shouldSkip = true;
                                break;
                            }
                        }

                        if (!shouldSkip) {
                            links.push({name: text, href: href});
                        }
                    }

                    // 去重
                    const seen = new Set();
                    return links.filter(l => !seen.has(l.href) && seen.add(l.href));
                }
            ''')

            print(f'  找到 {len(disease_links)} 个候选疾病')

            # 爬取前N个疾病
            count = 0
            for disease in disease_links:
                if count >= max_per_specialty:
                    break

                print(f'  [{count+1}] 爬取: {disease["name"][:40]}')

                try:
                    await page.goto(f'{base_url}{disease["href"]}', wait_until='networkidle')
                    await asyncio.sleep(1)

                    # 获取内容 - 只取主要内容区域
                    content = await page.evaluate('''
                        () => {
                            // 尝试获取主要内容
                            const main = document.querySelector('article, main, [role="main"], .topic-content');
                            const text = main ? main.innerText : document.body.innerText;
                            return text;
                        }
                    ''')

                    # 清理内容
                    lines = content.split('\n')
                    cleaned_lines = []
                    skip_keywords = ['skip to', '專業的', '消费者', '默沙东',
                                   '医学主题', '资源', '测验', '在该主题中',
                                   '本章节的其他主题', '看法', '进行患者培训',
                                   'Professional edition active', ' Reviewed By',
                                   '已审核', '修改的', '作者:', '病理生理',
                                   '病因', '评价', '治疗', '关键点', '多媒体']

                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 10 and len(line) < 150:
                            if not any(kw in line for kw in skip_keywords):
                                cleaned_lines.append(line)

                    cleaned_content = '\n'.join(cleaned_lines[:100])

                    if len(cleaned_content) > 500:
                        # 生成代码
                        code = f"{specialty_code.upper()[:1]}{hash(disease['name']) % 100:02d}"

                        results.append({
                            'code': code,
                            'name': disease['name'],
                            'specialty': specialty_code,
                            'keywords': [disease['name']],
                            'content': cleaned_content,
                            'source': 'msd_manuals',
                            'source_url': f'{base_url}{disease["href"]}'
                        })
                        count += 1
                        print(f'    ✓ 成功 ({len(cleaned_content)} 字符)')
                    else:
                        print(f'    ✗ 内容太少 ({len(cleaned_content)} 字符)')
                except Exception as e:
                    print(f'    ✗ 失败: {e}')

        await browser.close()

        return results


async def main():
    """主函数"""
    print("=" * 60)
    print("MSD 诊疗手册爬虫")
    print("=" * 60)

    results = await crawl_diseases(max_per_specialty=3)

    # 保存结果
    output_file = '/Users/zhuxinye/Desktop/project/home-health/medical-knowledge-service/data/msd_knowledge.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n完成! 共爬取 {len(results)} 条数据")
    print(f"已保存到: {output_file}")

    # 统计
    specialty_count = {}
    for r in results:
        s = r['specialty']
        specialty_count[s] = specialty_count.get(s, 0) + 1
    print('\n按专科统计:')
    for s, c in specialty_count.items():
        print(f'  {s}: {c}')

    # 显示第一条数据示例
    if results:
        print('\n数据示例:')
        print(f'  名称: {results[0]["name"]}')
        print(f'  专科: {results[0]["specialty"]}')
        print(f'  内容长度: {len(results[0]["content"])} 字符')


if __name__ == '__main__':
    asyncio.run(main())
