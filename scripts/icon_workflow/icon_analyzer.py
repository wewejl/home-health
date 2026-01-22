#!/usr/bin/env python3
"""
图标分析器 - 扫描 iOS 代码，提取所有图标并生成 prompts
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class IconInfo:
    """图标信息"""
    name: str              # SF Symbol 名称
    usage_context: str     # 使用上下文（在哪个文件/位置使用）
    icon_type: str         # 图标类型（导航、操作、状态等）
    prompt_en: str         # 英文 prompt
    prompt_zh: str         # 中文描述
    color_primary: str = "#5C44FF"  # 主色（鑫琳医生紫色）
    color_secondary: str = "#A5A5B5"  # 次色（灰色）


class IconAnalyzer:
    """图标分析器"""

    # SF Symbol 到图标的映射配置
    ICON_DEFINITIONS = {
        # 导航方向类
        "chevron.right": {
            "type": "navigation",
            "zh": "向右箭头",
            "en": "chevron arrow pointing right",
            "style": "thin line arrow"
        },
        "chevron.left": {
            "type": "navigation",
            "zh": "向左箭头",
            "en": "chevron arrow pointing left",
            "style": "thin line arrow"
        },
        "chevron.down": {
            "type": "navigation",
            "zh": "向下箭头",
            "en": "chevron arrow pointing down",
            "style": "thin line arrow"
        },
        "arrow.up": {
            "type": "navigation",
            "zh": "向上箭头",
            "en": "arrow pointing up",
            "style": "straight arrow"
        },
        "arrow.clockwise": {
            "type": "action",
            "zh": "顺时针刷新箭头",
            "en": "circular refresh arrow clockwise",
            "style": "circular arrow"
        },
        "arrow.triangle.merge": {
            "type": "action",
            "zh": "合并箭头",
            "en": "merge arrows triangle",
            "style": "triangular arrows"
        },

        # 操作动作类
        "plus.circle.fill": {
            "type": "action",
            "zh": "圆形加号",
            "en": "plus sign inside circle",
            "style": "circular plus button"
        },
        "pencil": {
            "type": "action",
            "zh": "铅笔编辑",
            "en": "pencil for editing",
            "style": "pencil icon"
        },
        "xmark.circle.fill": {
            "type": "action",
            "zh": "圆形叉号关闭",
            "en": "X mark inside circle",
            "style": "circular close button"
        },
        "xmark": {
            "type": "action",
            "zh": "叉号",
            "en": "X mark",
            "style": "simple X"
        },
        "checkmark.circle.fill": {
            "type": "status",
            "zh": "圆形对勾",
            "en": "checkmark inside circle",
            "style": "circular checkmark"
        },
        "checkmark.seal.fill": {
            "type": "status",
            "zh": "盾牌对勾认证",
            "en": "checkmark inside seal shield",
            "style": "shield checkmark"
        },
        "slider.horizontal.3": {
            "type": "control",
            "zh": "水平滑块",
            "en": "horizontal slider control",
            "style": "slider with handle"
        },
        "square.and.pencil": {
            "type": "action",
            "zh": "方块和铅笔编辑",
            "en": "square with pencil",
            "style": "edit icon"
        },
        "ellipsis.circle": {
            "type": "action",
            "zh": "三个点更多",
            "en": "three dots inside circle",
            "style": "more options dots"
        },

        # 状态指示类
        "flame.fill": {
            "type": "status",
            "zh": "火焰热门",
            "en": "flame fire icon",
            "style": "flame shape"
        },
        "sparkles": {
            "type": "status",
            "zh": "闪亮特效",
            "en": "sparkles magic effect",
            "style": "sparkle stars"
        },
        "stop.fill": {
            "type": "status",
            "zh": "停止方块",
            "en": "stop sign square",
            "style": "square stop"
        },
        "lock.shield": {
            "type": "status",
            "zh": "盾牌锁",
            "en": "lock inside shield",
            "style": "shield lock"
        },
        "clock.arrow.circlepath": {
            "type": "status",
            "zh": "时钟刷新历史",
            "en": "clock with circular arrow",
            "style": "refresh clock"
        },
        "exclamationmark.triangle": {
            "type": "status",
            "zh": "警告三角",
            "en": "exclamation inside triangle",
            "style": "warning triangle"
        },
        "exclamationmark.triangle.fill": {
            "type": "status",
            "zh": "填充警告三角",
            "en": "filled exclamation triangle",
            "style": "filled warning triangle"
        },

        # 通讯交流类
        "bubble.left.and.bubble.right": {
            "type": "communication",
            "zh": "对话气泡",
            "en": "two chat bubbles",
            "style": "conversation bubbles"
        },
        "bubble.left.fill": {
            "type": "communication",
            "zh": "左气泡消息",
            "en": "chat bubble filled",
            "style": "message bubble"
        },
        "envelope": {
            "type": "communication",
            "zh": "信封邮件",
            "en": "envelope mail",
            "style": "mail icon"
        },
        "speaker.wave.2.fill": {
            "type": "communication",
            "zh": "扬声器音量",
            "en": "speaker with sound waves",
            "style": "volume speaker"
        },
        "mic.fill": {
            "type": "communication",
            "zh": "麦克风",
            "en": "microphone",
            "style": "mic icon"
        },
        "mic.slash.fill": {
            "type": "communication",
            "zh": "禁用麦克风",
            "en": "microphone with slash",
            "style": "muted mic"
        },
        "paperplane.fill": {
            "type": "communication",
            "zh": "纸飞机发送",
            "en": "paper plane send",
            "style": "send plane"
        },

        # 医疗专用类
        "brain.head.profile": {
            "type": "medical",
            "zh": "大脑头部轮廓",
            "en": "brain inside head profile",
            "style": "medical brain"
        },
        "heart.fill": {
            "type": "medical",
            "zh": "爱心心脏",
            "en": "heart shape",
            "style": "heart icon"
        },
        "cross.fill": {
            "type": "medical",
            "zh": "医疗十字",
            "en": "medical cross",
            "style": "plus cross"
        },
        "note.text": {
            "type": "medical",
            "zh": "文本笔记",
            "en": "note with text lines",
            "style": "note icon"
        },

        # 文档管理类
        "doc.text": {
            "type": "document",
            "zh": "文本文档",
            "en": "document with text lines",
            "style": "document icon"
        },
        "doc.text.fill": {
            "type": "document",
            "zh": "填充文本文档",
            "en": "filled document with text",
            "style": "filled document"
        },
        "doc.text.viewfinder": {
            "type": "document",
            "zh": "取景框文档",
            "en": "document with viewfinder",
            "style": "scan document"
        },
        "calendar": {
            "type": "document",
            "zh": "日历",
            "en": "calendar date",
            "style": "calendar icon"
        },
        "link": {
            "type": "document",
            "zh": "链接",
            "en": "chain link",
            "style": "link icon"
        },
        "square.and.arrow.down": {
            "type": "document",
            "zh": "下载",
            "en": "square with down arrow",
            "style": "download icon"
        },
        "square.and.arrow.up": {
            "type": "document",
            "zh": "上传",
            "en": "square with up arrow",
            "style": "upload icon"
        },

        # 用户相关类
        "person.fill": {
            "type": "user",
            "zh": "用户人形",
            "en": "person silhouette",
            "style": "user icon"
        },
        "person.circle.fill": {
            "type": "user",
            "zh": "圆形用户头像",
            "en": "person inside circle",
            "style": "avatar circle"
        },
        "person.2.slash": {
            "type": "user",
            "zh": "禁止两人",
            "en": "two people with slash",
            "style": "private users"
        },
        "person.crop.circle.badge.plus": {
            "type": "user",
            "zh": "带加号用户",
            "en": "person circle with plus badge",
            "style": "add user"
        },
        "person.fill.viewfinder": {
            "type": "user",
            "zh": "取景框用户",
            "en": "person with viewfinder",
            "style": "scan user"
        },
        "building.2.slash": {
            "type": "user",
            "zh": "禁止建筑",
            "en": "two buildings with slash",
            "style": "private place"
        },

        # 分享类
        "rectangle.portrait.and.arrow.right": {
            "type": "share",
            "zh": "分享箭头",
            "en": "rectangle with right arrow",
            "style": "share icon"
        },

        # 搜索类
        "magnifyingglass": {
            "type": "search",
            "zh": "放大镜搜索",
            "en": "magnifying glass",
            "style": "search icon"
        },

        # 表情类
        "face.smiling": {
            "type": "emotion",
            "zh": "笑脸",
            "en": "smiling face",
            "style": "happy face"
        },
    }

    @classmethod
    def get_all_icons(cls) -> List[IconInfo]:
        """获取所有图标信息列表"""
        icons = []

        for name, definition in cls.ICON_DEFINITIONS.items():
            icon_type = definition["type"]
            zh_desc = definition["zh"]
            en_desc = definition["en"]

            # 生成 prompt
            prompt_en = cls._generate_prompt(en_desc, icon_type)
            prompt_zh = zh_desc

            icons.append(IconInfo(
                name=name,
                usage_context="",
                icon_type=icon_type,
                prompt_en=prompt_en,
                prompt_zh=prompt_zh
            ))

        return icons

    @classmethod
    def _generate_prompt(cls, icon_desc: str, icon_type: str) -> str:
        """生成英文 prompt"""
        # 基础 prompt 模板
        base_prompt = (
            f"minimalist {icon_desc} icon, duotone style, "
            f"flat design, vector style, clean lines, "
            f"primary color {IconInfo.color_primary} purple, "
            f"secondary color {IconInfo.color_secondary} gray, "
            f"white background, isolated, simple geometric shapes, "
            f"no shading, no gradients, no 3d effect, "
            f"modern mobile app icon style, "
            f"transparent background PNG format"
        )

        # 根据类型添加额外描述
        type_specific = {
            "navigation": ", thin stroke, directional arrow",
            "action": ", action button style, interactive",
            "status": ", status indicator, clear visibility",
            "communication": ", message or communication symbol",
            "medical": ", healthcare symbol, professional",
            "document": ", file or document symbol",
            "user": ", user or account symbol",
            "share": ", sharing or export symbol",
            "search": ", search or find symbol",
            "emotion": ", emoji style icon",
            "control": ", UI control element"
        }

        if icon_type in type_specific:
            base_prompt += type_specific[icon_type]

        return base_prompt

    @classmethod
    def scan_code(cls, code_path: str) -> List[str]:
        """扫描代码文件，提取所有使用的 SF Symbol"""
        code_path = Path(code_path)
        if not code_path.exists():
            return []

        # 读取代码
        content = code_path.read_text(encoding='utf-8', errors='ignore')

        # 提取所有 Image(systemName: "...") 中的名称
        pattern = r'Image\(systemName:\s*"([^"]+)"\)'
        matches = re.findall(pattern, content)

        return list(set(matches))  # 去重


def generate_icon_manifest():
    """生成图标清单"""
    analyzer = IconAnalyzer()
    icons = analyzer.get_all_icons()

    # 按类型分组
    grouped = {}
    for icon in icons:
        if icon.icon_type not in grouped:
            grouped[icon.icon_type] = []
        grouped[icon.icon_type].append(icon)

    # 输出清单
    manifest = {
        "total": len(icons),
        "by_type": {
            k: len(v) for k, v in grouped.items()
        },
        "icons": [asdict(icon) for icon in icons]
    }

    # 保存 JSON
    output_dir = Path("scripts/icon_workflow/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "icon_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ 图标清单已生成: {manifest_path}")
    print(f"   总计 {len(icons)} 个图标")

    # 输出分组统计
    print("\n按类型分组:")
    for icon_type, count in sorted(manifest["by_type"].items(), key=lambda x: -x[1]):
        print(f"  {icon_type}: {count} 个")

    return icons, manifest


def generate_prompt_file():
    """生成 prompt 文件，用于批量生成"""
    icons, manifest = generate_icon_manifest()

    output_dir = Path("scripts/icon_workflow/output")
    prompts_file = output_dir / "icon_prompts.txt"

    with open(prompts_file, 'w', encoding='utf-8') as f:
        f.write("# 星流 Star-3 Alpha 图标生成 Prompts\n")
        f.write(f"# 总计 {len(icons)} 个图标\n\n")
        f.write("# 使用方法: 复制每行的 prompt 到 LiblibAI 生成\n\n")

        for icon in icons:
            f.write(f"# {icon.name} - {icon.prompt_zh}\n")
            f.write(f"{icon.prompt_en}\n")
            f.write("\n")

    print(f"✅ Prompt 文件已生成: {prompts_file}")

    return icons


if __name__ == "__main__":
    generate_prompt_file()
