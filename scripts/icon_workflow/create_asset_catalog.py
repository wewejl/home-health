#!/usr/bin/env python3
"""
创建 Asset Catalog 并复制图标
"""

import json
import shutil
from pathlib import Path

# 图标映射：SF Symbol -> 文件名
ICON_MAPPINGS = {
    "chevron.right": "chevron_right",
    "chevron.left": "chevron_left",
    "chevron.down": "chevron_down",
    "arrow.up": "arrow_up",
    "arrow.clockwise": "arrow_clockwise",
    "arrow.triangle.merge": "arrow_triangle_merge",
    "plus.circle.fill": "plus_circle_fill",
    "pencil": "pencil",
    "xmark.circle.fill": "xmark_circle_fill",
    "xmark": "xmark",
    "checkmark.circle.fill": "checkmark_circle_fill",
    "checkmark.seal.fill": "checkmark_seal_fill",
    "slider.horizontal.3": "slider_horizontal_3",
    "square.and.pencil": "square_and_pencil",
    "ellipsis.circle": "ellipsis_circle",
    "flame.fill": "flame_fill",
    "sparkles": "sparkles",
    "stop.fill": "stop_fill",
    "lock.shield": "lock_shield",
    "clock.arrow.circlepath": "clock_arrow_circlepath",
    "exclamationmark.triangle": "exclamationmark_triangle",
    "exclamationmark.triangle.fill": "exclamationmark_triangle_fill",
    "bubble.left.and.bubble.right": "bubble_left_and_bubble_right",
    "bubble.left.fill": "bubble_left_fill",
    "envelope": "envelope",
    "speaker.wave.2.fill": "speaker_wave_2_fill",
    "mic.fill": "mic_fill",
    "mic.slash.fill": "mic_slash_fill",
    "paperplane.fill": "paperplane_fill",
    "brain.head.profile": "brain_head_profile",
    "heart.fill": "heart_fill",
    "cross.fill": "cross_fill",
    "note.text": "note_text",
    "doc.text": "doc_text",
    "doc.text.fill": "doc_text_fill",
    "doc.text.viewfinder": "doc_text_viewfinder",
    "calendar": "calendar",
    "link": "link",
    "square.and.arrow.down": "square_and_arrow_down",
    "square.and.arrow.up": "square_and_arrow_up",
    "person.fill": "person_fill",
    "person.circle.fill": "person_circle_fill",
    "person.2.slash": "person_2_slash",
    "person.crop.circle.badge.plus": "person_crop_circle_badge_plus",
    "person.fill.viewfinder": "person_fill_viewfinder",
    "building.2.slash": "building_2_slash",
    "rectangle.portrait.and.arrow.right": "rectangle_portrait_and_arrow_right",
    "magnifyingglass": "magnifyingglass",
    "face.smiling": "face_smiling",
}

# 原始图标和处理后图标的路径
INPUT_DIR = Path("scripts/icon_workflow/output/icons")
PROCESSED_DIR = Path("scripts/icon_workflow/output/processed")
ASSETS_DIR = Path("ios/xinlingyisheng/xinlingyisheng/Assets.xcassets/CustomIcons.xcassets")

def create_asset_catalog():
    """创建 Asset Catalog 结构"""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"创建 Asset Catalog: {ASSETS_DIR}")

    for sf_name, file_name in ICON_MAPPINGS.items():
        # 处理后的图片路径
        processed_path = PROCESSED_DIR / f"{file_name}_processed.png"

        if not processed_path.exists():
            print(f"  ⚠️  跳过 {sf_name} (处理后的图片不存在)")
            continue

        # 创建 imageset 目录
        imageset_dir = ASSETS_DIR / f"{file_name}.imageset"
        imageset_dir.mkdir(parents=True, exist_ok=True)

        # 读取图片尺寸
        from PIL import Image
        img = Image.open(processed_path)
        width, height = img.size

        # 生成 Contents.json
        contents = {
            "images": [
                {
                    "filename": f"{file_name}_processed.png",
                    "idiom": "universal",
                    "scale": "1x"
                }
            ],
            "info": {
                "author": "xcode",
                "version": 1
            },
            "properties": {
                "preserves-vector-representation": 1,
                "template-rendering-intent": "original"
            }
        }

        # 复制图片到 imageset
        shutil.copy2(processed_path, imageset_dir / f"{file_name}_processed.png")

        # 写入 Contents.json
        with open(imageset_dir / "Contents.json", 'w') as f:
            json.dump(contents, f, indent=2)

        print(f"  ✅ {sf_name} -> {file_name}.imageset")

    print(f"\n✅ Asset Catalog 创建完成!")
    print(f"   总计: {len(ICON_MAPPINGS)} 个图标")


if __name__ == "__main__":
    create_asset_catalog()
