"""
MedLive HTML 解析器
将医脉通 HTML 页面解析成结构化 sections
"""
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Optional
import re


# Section 映射表：医脉通标题 -> 我们的 section ID
SECTION_MAPPING = {
    "简介": {"id": "overview", "icon": "info.circle", "title": "疾病简介"},
    "基础": {"id": "basics", "icon": "book.fill", "title": "基础知识"},
    "定义": {"id": "definition", "icon": "text.book.closed", "title": "定义"},
    "分类": {"id": "classification", "icon": "square.grid.2x2", "title": "疾病分类"},
    "流行病学": {"id": "epidemiology", "icon": "chart.bar", "title": "流行病学"},
    "病因": {"id": "causes", "icon": "cross.case", "title": "病因"},
    "发生机制": {"id": "mechanism", "icon": "gearshape.2", "title": "发生机制"},
    "病理生理": {"id": "pathophysiology", "icon": "lungs", "title": "病理生理"},
    "病理解剖": {"id": "pathology", "icon": "scope", "title": "病理解剖"},
    "诊断": {"id": "diagnosis", "icon": "stethoscope", "title": "诊断"},
    "诊断流程": {"id": "diagnosis_flow", "icon": "arrow.triangle.branch", "title": "诊断流程"},
    "诊断程序": {"id": "diagnosis_flow", "icon": "arrow.triangle.branch", "title": "诊断程序"},
    "问诊与查体": {"id": "examination", "icon": "person.text.rectangle", "title": "问诊与查体"},
    "辅助检查": {"id": "auxiliary_exams", "icon": "waveform.path", "title": "辅助检查"},
    "鉴别诊断": {"id": "differential", "icon": "eye", "title": "鉴别诊断"},
    "诊断标准": {"id": "diagnosis_criteria", "icon": "checkmark.seal", "title": "诊断标准"},
    "治疗": {"id": "treatment", "icon": "pills", "title": "治疗"},
    "治疗流程": {"id": "treatment_flow", "icon": "arrow.triangle.branch", "title": "治疗流程"},
    "治疗程序": {"id": "treatment_flow", "icon": "arrow.triangle.branch", "title": "治疗程序"},
    "治疗原则": {"id": "treatment_principles", "icon": "cross.case", "title": "治疗原则"},
    "药物治疗": {"id": "medication", "icon": "pills.fill", "title": "药物治疗"},
    "预防": {"id": "prevention", "icon": "shield.fill", "title": "预防"},
    "筛查": {"id": "screening", "icon": "magnifyingglass", "title": "筛查"},
    "预防与康复": {"id": "rehabilitation", "icon": "heart.circle", "title": "预防与康复"},
    "康复": {"id": "rehab", "icon": "figure.walk", "title": "康复"},
    "复诊与随访": {"id": "followup", "icon": "calendar", "title": "复诊与随访"},
    "监测与随访": {"id": "followup", "icon": "calendar", "title": "监测与随访"},
    "随访要点": {"id": "followup", "icon": "calendar", "title": "随访要点"},
    "患者教育": {"id": "patient_education", "icon": "text.bubble", "title": "患者教育"},
    "预后": {"id": "prognosis", "icon": "chart.line.uptrend.xyaxis", "title": "预后"},
    "其他": {"id": "other", "icon": "doc.text", "title": "其他"},
    "参考文献": {"id": "references", "icon": "books.vertical", "title": "参考文献"},
}


def parse_html_to_sections(html: str, wiki_id: str) -> Dict:
    """
    将医脉通 HTML 解析成结构化数据

    Args:
        html: 医脉通网页 HTML
        wiki_id: 疾病的 wiki_id

    Returns:
        包含疾病信息和 sections 的字典
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 提取基本信息
    disease_name = extract_disease_name(soup)

    # 提取内容 sections
    sections = extract_sections(soup)

    return {
        "wiki_id": wiki_id,
        "name": disease_name,
        "url": f"https://yzy.medlive.cn/pc/wikiDetail?wiki_id={wiki_id}",
        "source": "医脉通",
        "sections": sections
    }


def extract_disease_name(soup: BeautifulSoup) -> str:
    """提取疾病名称"""
    # 尝试多种选择器
    selectors = [
        ".illness_name",
        "h1",
        ".wiki-title",
        ".disease-name",
    ]
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(strip=True)
            # 清理标题中的额外信息
            text = re.sub(r"\s*-\s*医脉通.*$", "", text)
            text = re.sub(r"\s*-\s*医知源.*$", "", text)
            if text:
                return text

    # 最后尝试 title 标签
    title = soup.find("title")
    if title:
        text = title.get_text(strip=True)
        text = re.sub(r"\s*-\s*医脉通.*$", "", text)
        text = re.sub(r"\s*-\s*医知源.*$", "", text)
        if text:
            return text

    return "未知疾病"


def extract_sections(soup: BeautifulSoup) -> List[Dict]:
    """
    提取所有内容区块

    医脉通页面结构：
    - .menu_click: 目录项
    - .detail_cont: 内容容器
    - .detail_infor: 每个 section 的内容块
    - .tename-xxx: 标题的类型标识
    """
    sections = []

    # 查找所有内容块
    content_blocks = soup.select(".detail_cont .detail_infor")

    if not content_blocks:
        # 备选方案：查找所有 tename 标题后的内容
        content_blocks = []
        tename_elems = soup.select("[class*='tename-']")
        for elem in tename_elems:
            # 找到标题后的内容容器
            parent = elem.find_parent("div")
            if parent:
                content_blocks.append(parent)

    for block in content_blocks:
        # 提取标题
        title_elem = block.select_one("[class*='tename-']")

        if not title_elem:
            continue

        # 获取标题类型
        classes = title_elem.get('class', [])
        tename_class = None
        for cls in classes:
            if cls.startswith('tename-'):
                tename_class = cls.replace('tename-', '')
                break

        title_text = title_elem.get_text(strip=True)
        # 去掉数字前缀，如 "一、定义" -> "定义"
        title_text = re.sub(r'^[一二三四五六七八九十]+[、.]\s*', '', title_text)

        # 如果标题为空，使用 tename_class
        if not title_text and tename_class:
            title_text = tename_class

        if not title_text:
            continue

        # 查找映射
        mapping = SECTION_MAPPING.get(title_text, {
            "id": f"section_{tename_class or 'unknown'}",
            "icon": "doc.text",
            "title": title_text
        })

        # 提取内容
        content, items = extract_content_from_block(block, title_elem, mapping["id"])

        sections.append({
            "id": mapping["id"],
            "title": mapping["title"],
            "icon": mapping["icon"],
            "content": content,
            "items": items
        })

    return sections


def extract_content_from_block(block: BeautifulSoup, title_elem: BeautifulSoup, section_id: str) -> tuple:
    """
    从单个内容块提取内容和子项

    Returns:
        (content: str, items: List[Dict])
    """
    content_parts = []
    items = []
    item_counter = 0

    # 获取标题元素之后的所有内容，直接从块中提取所有文本
    # 移除标题元素后，获取剩余所有内容
    title_copy = title_elem.__copy__()
    title_elem.decompose()

    # 递归提取块内所有有意义的内容
    def extract_recursive(element, depth=0):
        nonlocal content_parts, items, item_counter

        if depth > 10:  # 防止无限递归
            return

        # 只处理 Tag 元素，跳过文本节点和其他类型
        if not isinstance(element, Tag):
            return

        # 跳过标题类元素
        classes = element.get('class', [])
        if classes and any('tename-' in str(c) for c in classes):
            return

        if element.name == "p":
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                content_parts.append(text)

        elif element.name == "div":
            # 检查是否包含 strong（子标题）
            strong = element.find("strong")
            if strong:
                item_title = strong.get_text(strip=True)
                strong_copy = strong.__copy__()
                strong.extract()
                item_content = element.get_text(strip=True)
                if item_content:
                    item_content = item_content.replace(item_title, "", 1).strip()

                if item_title or item_content:
                    items.append({
                        "id": f"{section_id}_item_{item_counter}",
                        "title": item_title if len(item_title) < 100 else None,
                        "content": item_content or item_title,
                        "level": 0
                    })
                    item_counter += 1
            else:
                # 递归处理子元素
                for child in element.children:
                    extract_recursive(child, depth + 1)

        elif element.name in ["ul", "ol"]:
            for li in element.find_all("li", recursive=False):
                item_data = extract_list_item(li, section_id, item_counter)
                if item_data:
                    items.append(item_data)
                    item_counter += 1

        elif element.name not in ['script', 'style', 'nav', 'header', 'footer']:
            # 其他元素，递归处理子元素
            for child in element.children:
                extract_recursive(child, depth + 1)

    # 从块中提取所有内容（标题之后）
    for child in block.children:
        extract_recursive(child, 0)

    # 恢复标题元素
    block.insert(0, title_copy)

    content = "\n".join(content_parts) if content_parts else None

    return content, items if items else None


def extract_list_item(li: BeautifulSoup, section_id: str, index: int) -> Optional[Dict]:
    """从 li 元素提取子项"""
    text = li.get_text(strip=True)
    if not text or len(text) < 2:
        return None

    # 检查是否有 strong 标记作为子标题
    strong = li.find("strong")
    if strong:
        item_title = strong.get_text(strip=True)
        item_content = text.replace(item_title, "", 1).strip()
        return {
            "id": f"{section_id}_item_{index}",
            "title": item_title,
            "content": item_content,
            "level": 0
        }

    # 检查是否有冒号分隔的标题
    if ":" in text or "：" in text:
        parts = re.split(r'[:：]', text, 1)
        if len(parts) == 2 and len(parts[0]) < 30:
            return {
                "id": f"{section_id}_item_{index}",
                "title": parts[0].strip(),
                "content": parts[1].strip(),
                "level": 0
            }

    # 普通列表项
    return {
        "id": f"{section_id}_item_{index}",
        "title": None,
        "content": text,
        "level": 0
    }


def parse_raw_text(text: str, wiki_id: str) -> Dict:
    """
    从原始文本解析（备用方案，当 HTML 解析失败时使用）
    适用于已保存的文本格式数据
    """
    lines = text.split("\n")

    disease_name = "未知"
    sections = []
    current_section = None
    current_content = []
    current_items = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测标题（类似 "→XX" 或数字开头的行）
        if line.startswith("→") or re.match(r'^\d+[→、]', line):
            # 保存上一个 section
            if current_section:
                sections.append({
                    "id": current_section["id"],
                    "title": current_section["title"],
                    "icon": current_section["icon"],
                    "content": "\n".join(current_content) if current_content else None,
                    "items": current_items if current_items else None
                })

            # 开始新 section
            title = re.sub(r'^[→\d、]+', '', line)
            mapping = SECTION_MAPPING.get(title, {
                "id": f"section_{len(sections)}",
                "icon": "doc.text",
                "title": title
            })

            current_section = mapping.copy()
            current_content = []
            current_items = []
        elif current_section:
            # 添加到当前 section 内容
            if line.startswith("- ") or line.startswith("• "):
                current_items.append({
                    "id": f"{current_section['id']}_item_{len(current_items)}",
                    "title": None,
                    "content": line[2:],
                    "level": 0
                })
            else:
                current_content.append(line)

    # 保存最后一个 section
    if current_section:
        sections.append({
            "id": current_section["id"],
            "title": current_section["title"],
            "icon": current_section["icon"],
            "content": "\n".join(current_content) if current_content else None,
            "items": current_items if current_items else None
        })

    return {
        "wiki_id": wiki_id,
        "name": disease_name,
        "sections": sections
    }
