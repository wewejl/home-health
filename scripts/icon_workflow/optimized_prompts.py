#!/usr/bin/env python3
"""
优化的图标 Prompt 生成器
针对 LiblibAI 星流 API 优化 prompt 模板
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class OptimizedIconInfo:
    """优化后的图标信息"""
    name: str              # SF Symbol 名称
    icon_type: str         # 图标类型
    prompt_en: str         # 优化后的英文 prompt
    prompt_zh: str         # 中文描述
    negative_prompt: str   # 负向 prompt


class OptimizedPromptBuilder:
    """优化的 Prompt 构建器"""

    # 通用 prompt 基础模板
    BASE_PROMPT = (
        "flat vector icon, minimalist design, "
        "duotone style with two colors, "
        "clean smooth curves, "
        "thick consistent stroke width, "
        "centered composition, "
        "high contrast, "
        "suitable for small size (48x48px), "
        "no shading, no gradients, no 3d effects, "
        "no textures, no patterns, "
        "solid colors only, "
        "isolated on transparent background, "
        "PNG with alpha channel, "
        "modern mobile app icon style"
    )

    # 负向 prompt
    NEGATIVE_PROMPT = (
        "photorealistic, 3d render, realistic, "
        "shading, shadows, gradients, texture, noise, grain, "
        "blur, fuzzy, messy, complex details, "
        "thin lines, intricate, ornate, decorative, "
        "watermark, text, logo, signature, "
        "white background, solid background, "
        "cartoon, anime, sketch, hand drawn, "
        "glossy, shiny, metallic, glass"
    )

    # 颜色配置
    PRIMARY_COLOR = "#5C44FF"  # 鑫琳医生紫色
    SECONDARY_COLOR = "#A5A5B5"  # 次要灰色
    ACCENT_COLOR = "#FF6B6B"    # 强调色（红色）

    # 图标定义
    ICON_DEFINITIONS = {
        # 导航方向类
        "chevron.right": {
            "type": "navigation",
            "zh": "向右箭头",
            "en_base": "chevron arrow pointing right",
            "style_specific": "thick bold arrow pointing right, 45 degree angle, V shape, filled arrowhead"
        },
        "chevron.left": {
            "type": "navigation",
            "zh": "向左箭头",
            "en_base": "chevron arrow pointing left",
            "style_specific": "thick bold arrow pointing left, 45 degree angle, V shape, filled arrowhead"
        },
        "chevron.down": {
            "type": "navigation",
            "zh": "向下箭头",
            "en_base": "chevron arrow pointing down",
            "style_specific": "thick bold arrow pointing down, inverted V shape, filled arrowhead"
        },
        "arrow.up": {
            "type": "navigation",
            "zh": "向上箭头",
            "en_base": "straight arrow pointing up",
            "style_specific": "vertical straight arrow, thick line, filled arrowhead pointing up"
        },
        "arrow.clockwise": {
            "type": "action",
            "zh": "顺时针刷新",
            "en_base": "circular refresh arrow",
            "style_specific": "circular arrow arc, clockwise direction, refresh metaphor, 270 degree arc"
        },
        "arrow.triangle.merge": {
            "type": "action",
            "zh": "合并箭头",
            "en_base": "merge arrows",
            "style_specific": "two arrows converging into triangle, merge concept, arrows pointing inward"
        },

        # 操作动作类
        "plus.circle.fill": {
            "type": "action",
            "zh": "圆形加号",
            "en_base": "plus sign inside circle",
            "style_specific": "circle outline with plus sign in center, add button style, rounded shape"
        },
        "pencil": {
            "type": "action",
            "zh": "铅笔编辑",
            "en_base": "pencil",
            "style_specific": "simple pencil shape, diagonal orientation, pointed tip, eraser at bottom"
        },
        "xmark.circle.fill": {
            "type": "action",
            "zh": "圆形叉号",
            "en_base": "X mark inside filled circle",
            "style_specific": "filled circle with white X mark, close button style"
        },
        "xmark": {
            "type": "action",
            "zh": "叉号",
            "en_base": "X mark",
            "style_specific": "simple X shape, two crossed lines, equal thickness"
        },
        "checkmark.circle.fill": {
            "type": "status",
            "zh": "圆形对勾",
            "en_base": "checkmark inside filled circle",
            "style_specific": "filled circle with white checkmark, success state"
        },
        "checkmark.seal.fill": {
            "type": "status",
            "zh": "盾牌对勾",
            "en_base": "checkmark inside seal shield",
            "style_specific": "shield badge shape with checkmark, verified badge, security symbol"
        },
        "slider.horizontal.3": {
            "type": "control",
            "zh": "水平滑块",
            "en_base": "horizontal slider with handle",
            "style_specific": "horizontal line with circular handle, slider control"
        },
        "square.and.pencil": {
            "type": "action",
            "zh": "编辑方块",
            "en_base": "square with pencil",
            "style_specific": "square outline with diagonal pencil, edit icon"
        },
        "ellipsis.circle": {
            "type": "action",
            "zh": "更多选项",
            "en_base": "three dots inside circle",
            "style_specific": "circle outline with three horizontal dots, more options"
        },

        # 状态指示类
        "flame.fill": {
            "type": "status",
            "zh": "火焰热门",
            "en_base": "flame fire",
            "style_specific": "simple flame shape, curved lines, hot symbol, trending up"
        },
        "sparkles": {
            "type": "status",
            "zh": "闪亮特效",
            "en_base": "sparkles magic",
            "style_specific": "three star shapes, sparkle effect, magic wand style"
        },
        "stop.fill": {
            "type": "status",
            "zh": "停止",
            "en_base": "stop sign square",
            "style_specific": "filled square or octagon, stop symbol"
        },
        "lock.shield": {
            "type": "status",
            "zh": "盾牌锁",
            "en_base": "lock inside shield",
            "style_specific": "shield outline with lock symbol, security icon"
        },
        "clock.arrow.circlepath": {
            "type": "status",
            "zh": "刷新历史",
            "en_base": "clock with circular arrow",
            "style_specific": "clock face with circular arrow around, history refresh"
        },
        "exclamationmark.triangle": {
            "type": "status",
            "zh": "警告三角",
            "en_base": "exclamation inside triangle",
            "style_specific": "triangle outline with exclamation point, warning symbol"
        },
        "exclamationmark.triangle.fill": {
            "type": "status",
            "zh": "填充警告",
            "en_base": "filled exclamation triangle",
            "style_specific": "filled triangle with white exclamation, warning"
        },

        # 通讯交流类
        "bubble.left.and.bubble.right": {
            "type": "communication",
            "zh": "对话气泡",
            "en_base": "two chat bubbles",
            "style_specific": "two rounded message bubbles, conversation icon, chat symbol"
        },
        "bubble.left.fill": {
            "type": "communication",
            "zh": "消息气泡",
            "en_base": "filled chat bubble",
            "style_specific": "filled rounded message bubble, chat icon, tail on one side"
        },
        "envelope": {
            "type": "communication",
            "zh": "信封邮件",
            "en_base": "envelope",
            "style_specific": "envelope shape with pointed flap, mail icon, closed letter"
        },
        "speaker.wave.2.fill": {
            "type": "communication",
            "zh": "扬声器",
            "en_base": "speaker with sound waves",
            "style_specific": "speaker cone with two curved sound wave lines, volume icon"
        },
        "mic.fill": {
            "type": "communication",
            "zh": "麦克风",
            "en_base": "microphone",
            "style_specific": "microphone shape with rounded top, stand base, recording icon"
        },
        "mic.slash.fill": {
            "type": "communication",
            "zh": "静音麦克风",
            "en_base": "microphone with slash",
            "style_specific": "microphone with diagonal line through, muted icon"
        },
        "paperplane.fill": {
            "type": "communication",
            "zh": "纸飞机发送",
            "en_base": "paper plane",
            "style_specific": "paper airplane pointing right, send message icon"
        },

        # 医疗专用类
        "brain.head.profile": {
            "type": "medical",
            "zh": "大脑头部",
            "en_base": "brain inside head profile",
            "style_specific": "side profile head silhouette with brain shape inside, medical icon, neuroscience"
        },
        "heart.fill": {
            "type": "medical",
            "zh": "爱心心脏",
            "en_base": "heart shape",
            "style_specific": "classic heart shape with rounded bottom, love heart symbol, filled"
        },
        "cross.fill": {
            "type": "medical",
            "zh": "医疗十字",
            "en_base": "medical cross",
            "style_specific": "plus cross shape, medical symbol, equal length arms"
        },
        "note.text": {
            "type": "medical",
            "zh": "文本笔记",
            "en_base": "note with text lines",
            "style_specific": "notepad or document with horizontal text lines, note icon"
        },

        # 文档管理类
        "doc.text": {
            "type": "document",
            "zh": "文本文档",
            "en_base": "document with text",
            "style_specific": "rectangle page with horizontal text lines, document icon"
        },
        "doc.text.fill": {
            "type": "document",
            "zh": "填充文档",
            "en_base": "filled document",
            "style_specific": "filled rectangle page with text lines, document"
        },
        "doc.text.viewfinder": {
            "type": "document",
            "zh": "扫描文档",
            "en_base": "document with viewfinder",
            "style_specific": "document with scanner frame corners, scan icon"
        },
        "calendar": {
            "type": "document",
            "zh": "日历",
            "en_base": "calendar",
            "style_specific": "rectangle with date grid, calendar icon, date picker"
        },
        "link": {
            "type": "document",
            "zh": "链接",
            "en_base": "chain link",
            "style_specific": "chain link shape, URL hyperlink, connection symbol"
        },
        "square.and.arrow.down": {
            "type": "document",
            "zh": "下载",
            "en_base": "square with down arrow",
            "style_specific": "square with downward arrow, download icon, save to device"
        },
        "square.and.arrow.up": {
            "type": "document",
            "zh": "上传",
            "en_base": "square with up arrow",
            "style_specific": "square with upward arrow, upload icon, share file"
        },

        # 用户相关类
        "person.fill": {
            "type": "user",
            "zh": "用户",
            "en_base": "person silhouette",
            "style_specific": "simple person silhouette, head and shoulders, user icon"
        },
        "person.circle.fill": {
            "type": "user",
            "zh": "用户头像",
            "en_base": "person inside circle",
            "style_specific": "circle with person silhouette inside, avatar placeholder"
        },
        "person.2.slash": {
            "type": "user",
            "zh": "禁止两人",
            "en_base": "two people with slash",
            "style_specific": "two person silhouettes with diagonal line, private users"
        },
        "person.crop.circle.badge.plus": {
            "type": "user",
            "zh": "添加用户",
            "en_base": "person circle with plus",
            "style_specific": "circle with person and small plus badge, add user"
        },
        "person.fill.viewfinder": {
            "type": "user",
            "zh": "扫描用户",
            "en_base": "person with viewfinder",
            "style_specific": "person silhouette with scanning frame corners, scan user"
        },
        "building.2.slash": {
            "type": "user",
            "zh": "私人场所",
            "en_base": "two buildings with slash",
            "style_specific": "two building shapes with diagonal line, private location"
        },

        # 分享类
        "rectangle.portrait.and.arrow.right": {
            "type": "share",
            "zh": "分享",
            "en_base": "rectangle with right arrow",
            "style_specific": "rectangle with arrow pointing right, share export"
        },

        # 搜索类
        "magnifyingglass": {
            "type": "search",
            "zh": "搜索放大镜",
            "en_base": "magnifying glass",
            "style_specific": "magnifying glass shape, circle with handle, search icon"
        },

        # 表情类
        "face.smiling": {
            "type": "emotion",
            "zh": "笑脸",
            "en_base": "smiling face",
            "style_specific": "simple smiley face, two dots for eyes, curved smile, happy emoji"
        },
    }

    @classmethod
    def build_prompt(cls, icon_def: Dict) -> str:
        """构建优化的 prompt"""
        en_base = icon_def["en_base"]
        style_specific = icon_def.get("style_specific", "")

        # 组合 prompt
        parts = [
            style_specific + ",",           # 具体样式描述放在最前面
            cls.BASE_PROMPT                  # 通用模板
        ]

        # 添加颜色信息
        parts.append(f"primary color {cls.PRIMARY_COLOR}, secondary color {cls.SECONDARY_COLOR}")

        return " ".join(parts)

    @classmethod
    def get_all_optimized_prompts(cls) -> List[OptimizedIconInfo]:
        """获取所有优化的图标信息"""
        icons = []

        for name, definition in cls.ICON_DEFINITIONS.items():
            icon_type = definition["type"]
            zh_desc = definition["zh"]
            en_base = definition["en_base"]

            prompt_en = cls.build_prompt(definition)

            icons.append(OptimizedIconInfo(
                name=name,
                icon_type=icon_type,
                prompt_en=prompt_en,
                prompt_zh=zh_desc,
                negative_prompt=cls.NEGATIVE_PROMPT
            ))

        return icons

    def generate_optimized_prompts_file(self) -> str:
        """生成优化的 prompts 文件"""
        icons = self.get_all_optimized_prompts()

        output_dir = Path("scripts/icon_workflow/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        prompts_file = output_dir / "optimized_prompts.txt"

        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write("# 优化的图标生成 Prompts\n")
            f.write("# 针对星流 Star-3 Alpha API 优化\n")
            f.write(f"# 总计 {len(icons)} 个图标\n\n")

            for icon in icons:
                f.write(f"# {icon.name} - {icon.prompt_zh}\n")
                f.write(f"Positive: {icon.prompt_en}\n")
                f.write(f"Negative: {icon.negative_prompt}\n")
                f.write("\n")

        print(f"✅ 优化的 Prompts 已生成: {prompts_file}")

        # 同时生成 JSON 格式
        manifest = {
            "total": len(icons),
            "negative_prompt": self.NEGATIVE_PROMPT,
            "primary_color": self.PRIMARY_COLOR,
            "secondary_color": self.SECONDARY_COLOR,
            "icons": [
                {
                    "name": icon.name,
                    "type": icon.icon_type,
                    "zh": icon.prompt_zh,
                    "prompt": icon.prompt_en,
                    "negative": icon.negative_prompt
                }
                for icon in icons
            ]
        }

        manifest_file = output_dir / "optimized_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"✅ 优化的清单已生成: {manifest_file}")

        return str(prompts_file)

    def test_single_prompt(self) -> None:
        """测试单个优化的 prompt"""
        from liblib_client import LiblibAIClient, APIConfig

        # 测试 heart_fill 图标
        test_prompt = (
            "classic heart shape with rounded bottom, love heart symbol, filled, "
            "flat vector icon, minimalist design, "
            "duotone style with two colors, "
            "clean smooth curves, "
            "thick consistent stroke width, "
            "centered composition, "
            "high contrast, "
            "suitable for small size (48x48px), "
            "no shading, no gradients, no 3d effects, "
            "no textures, no patterns, "
            "solid colors only, "
            "isolated on transparent background, "
            "PNG with alpha channel, "
            "modern mobile app icon style, "
            "primary color #5C44FF, secondary color #A5A5B5"
        )

        negative = (
            "photorealistic, 3d render, realistic, "
            "shading, shadows, gradients, texture, noise, grain, "
            "blur, fuzzy, messy, complex details, "
            "thin lines, intricate, ornate, decorative, "
            "watermark, text, logo, signature, "
            "white background, solid background, "
            "cartoon, anime, sketch, hand drawn, "
            "glossy, shiny, metallic, glass"
        )

        config = APIConfig(
            access_key="R5FqjMESjuO4qrygB8FkvQ",
            secret_key="LVtCbjmHTL_R3Lm1vIxKiOUyYDGnSwEr"
        )

        client = LiblibAIClient(config)

        try:
            print("生成优化后的爱心图标...")
            uuid = client.generate_image(
                prompt=test_prompt,
                negative_prompt=negative,
                width=512,
                height=512
            )

            image_url = client.wait_for_completion(uuid)

            if image_url:
                output_path = Path("scripts/icon_workflow/output/heart_fill_optimized.png")
                client.download_image(image_url, str(output_path))
                print(f"✅ 优化后的图标已保存: {output_path}")
            else:
                print("❌ 生成失败")

        except Exception as e:
            print(f"❌ 错误: {e}")


if __name__ == "__main__":
    import sys

    builder = OptimizedPromptBuilder()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 测试单个 prompt
        builder.test_single_prompt()
    else:
        # 生成所有优化的 prompts
        builder.generate_optimized_prompts_file()
