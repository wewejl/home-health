"""
MSD 儿科诊疗手册爬虫 - 爬取全部儿科数据
"""
import asyncio
import json
from playwright.async_api import async_playwright


async def crawl_pediatrics():
    """爬取儿科全部疾病数据"""
    async with async_playwright() as p:
        browser = await p.webkit.launch(headless=True)
        page = await browser.new_page()

        results = []
        base_url = 'https://www.msdmanuals.cn'
        specialty_code = 'pediatrics'
        specialty_url = f'{base_url}/professional/pediatrics'

        print('=' * 60)
        print('MSD 儿科诊疗手册爬虫')
        print('=' * 60)
        print(f'\n正在访问儿科页面: {specialty_url}')

        await page.goto(specialty_url, wait_until='domcontentloaded', timeout=120000)
        await asyncio.sleep(2)

        # 获取该专科下的疾病链接
        print('\n正在获取疾病列表...')
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

        print(f'找到 {len(disease_links)} 个候选疾病')

        # 爬取所有疾病
        success_count = 0
        fail_count = 0
        skip_count = 0

        for i, disease in enumerate(disease_links):
            print(f'\n[{i+1}/{len(disease_links)}] 爬取: {disease["name"][:50]}')

            try:
                await page.goto(f'{base_url}{disease["href"]}', wait_until='domcontentloaded', timeout=60000)
                await asyncio.sleep(1)

                # 获取内容
                content = await page.evaluate('''
                    () => {
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

                cleaned_content = '\n'.join(cleaned_lines[:150])

                if len(cleaned_content) > 500:
                    # 生成代码
                    code = f"P{hash(disease['name']) % 1000:03d}"

                    results.append({
                        'code': code,
                        'name': disease['name'],
                        'specialty': specialty_code,
                        'keywords': [disease['name']],
                        'content': cleaned_content,
                        'source': 'msd_manuals',
                        'source_url': f'{base_url}{disease["href"]}'
                    })
                    success_count += 1
                    print(f'  ✓ 成功 ({len(cleaned_content)} 字符)')
                else:
                    skip_count += 1
                    print(f'  ✗ 内容太少，跳过 ({len(cleaned_content)} 字符)')
            except Exception as e:
                fail_count += 1
                print(f'  ✗ 失败: {e}')

        await browser.close()

        return results, success_count, fail_count, skip_count


async def main():
    """主函数"""
    results, success, fail, skip = await crawl_pediatrics()

    # 保存结果
    output_file = '/Users/zhuxinye/Desktop/project/home-health/medical-knowledge-service/data/pediatrics_knowledge.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n' + '=' * 60)
    print('爬取完成!')
    print('=' * 60)
    print(f'总计: {len(results)} 条数据')
    print(f'  成功: {success}')
    print(f'  失败: {fail}')
    print(f'  跳过: {skip}')
    print(f'\n已保存到: {output_file}')

    # 数据质量分析
    if results:
        total_length = sum(len(r['content']) for r in results)
        avg_length = total_length / len(results)

        print('\n数据质量分析:')
        print(f'  平均内容长度: {avg_length:.0f} 字符')
        print(f'  最长: {max(len(r['content']) for r in results)} 字符')
        print(f'  最短: {min(len(r['content']) for r in results)} 字符')

        # 显示前5条数据示例
        print('\n前5条数据:')
        for i, r in enumerate(results[:5]):
            print(f'  {i+1}. [{r["code"]}] {r["name"][:30]}... ({len(r["content"])} 字符)')


if __name__ == '__main__':
    asyncio.run(main())
