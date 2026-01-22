#!/usr/bin/env python3
"""
代码替换器 - 将 iOS 代码中的 SF Symbol 替换为自定义图标

步骤：
1. 扫描 Swift 文件中的 Image(systemName: "...")
2. 替换为自定义 Image 资源
3. 更新 Assets.xcassets 或创建新的 Asset Catalog
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


class IconReplacer:
    """iOS 图标代码替换器"""

    # SF Symbol 到自定义图标的映射
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

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ios_dir = self.project_root / "ios/xinlingyisheng/xinlingyisheng"
        self.views_dir = self.ios_dir / "Views"
        self.assets_dir = self.ios_dir / "Assets.xcassets"

    def scan_files(self) -> List[Path]:
        """扫描需要处理的 Swift 文件"""
        swift_files = list(self.views_dir.rglob("*.swift"))
        print(f"找到 {len(swift_files)} 个 Swift 文件")
        return swift_files

    def find_icon_usage(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """
        查找文件中使用的图标

        Returns:
            [(line_number, icon_name, full_match), ...]
        """
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')

        usages = []
        pattern = r'Image\(systemName:\s*"([^"]+)"\)'

        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                icon_name = match.group(1)
                full_match = match.group(0)
                usages.append((line_num, icon_name, full_match))

        return usages

    def generate_replacement_code(
        self,
        icon_name: str,
        full_match: str,
        context: str
    ) -> str:
        """
        生成替换代码

        SF Symbol 替换选项：
        1. 直接替换为 Image(icon_name) - 需要在 Assets 中添加图片
        2. 使用 .renderingMode(.template) 保持单色
        """
        safe_name = self.ICON_MAPPINGS.get(icon_name, icon_name.replace(".", "_"))

        # 检查是否需要保持渲染模式
        if ".foregroundColor" in context or ".tint" in context:
            # 有颜色设置，使用 template 渲染模式
            return f'Image("{safe_name}")'
        else:
            # 没有颜色设置，添加默认渲染模式
            return f'Image("{safe_name}").renderingMode(.original)'

    def create_icon_extension(self) -> str:
        """生成 SwiftUI Image 扩展代码"""
        code = '''import SwiftUI

// MARK: - 自定义图标扩展
extension Image {
    /// 使用自定义图标替换 SF Symbol
    /// - Parameter name: 图标名称（不含扩展名）
    /// - Parameter bundle: Bundle，默认使用 main
    static func icon(_ name: String, bundle: Bundle = .main) -> Image {
        Image(bundle: bundle, imageResource: .init(name: name))
    }
}

// MARK: - 图标名称枚举
enum IconName: String {
    // 导航方向
    case chevronRight
    case chevronLeft
    case chevronDown
    case arrowUp
    case arrowClockwise
    case arrowTriangleMerge

    // 操作动作
    case plusCircleFill
    case pencil
    case xmarkCircleFill
    case xmark
    case checkmarkCircleFill
    case checkmarkSealFill
    case sliderHorizontal3
    case squareAndPencil
    case ellipsisCircle

    // 状态指示
    case flameFill
    case sparkles
    case stopFill
    case lockShield
    case clockArrowCirclepath
    case exclamationmarkTriangle
    case exclamationmarkTriangleFill

    // 通讯交流
    case bubbleLeftAndBubbleRight
    case bubbleLeftFill
    case envelope
    case speakerWave2Fill
    case micFill
    case micSlashFill
    case paperplaneFill

    // 医疗专用
    case brainHeadProfile
    case heartFill
    case crossFill
    case noteText

    // 文档管理
    case docText
    case docTextFill
    case docTextViewfinder
    case calendar
    case link
    case squareAndArrowDown
    case squareAndArrowUp

    // 用户相关
    case personFill
    case personCircleFill
    case person2Slash
    case personCropCircleBadgePlus
    case personFillViewfinder
    case building2Slash

    // 其他
    case rectanglePortraitAndArrowRight
    case magnifyingglass
    case faceSmiling
}
'''
        return code

    def create_asset_catalog_script(self) -> str:
        """生成创建 Asset Catalog 的脚本"""
        script = f'''#!/bin/bash
# 自动创建 iOS Asset Catalog 图标集

ASSETS_PATH="{self.assets_dir.relative_to(self.project_root)}/CustomIcons.xcassets"
mkdir -p "$ASSETS_PATH"

# 为每个图标创建 imageset
'''

        for sf_name, asset_name in self.ICON_MAPPINGS.items():
            script += f'''
echo "创建 {asset_name}..."
mkdir -p "$ASSETS_PATH/{asset_name}.imageset"
cat > "$ASSETS_PATH/{asset_name}.imageset/Contents.json" << 'EOF'
{{
  "images" : [
    {{
      "filename" : "{asset_name}_16@1x.png",
      "idiom" : "universal",
      "scale" : "1x"
    }},
    {{
      "filename" : "{asset_name}_32@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    }},
    {{
      "filename" : "{asset_name}_48@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }}
  ],
  "info" : {{
    "author" : "xcode",
    "version" : 1
  }},
  "properties" : {{
    "preserves-vector-representation" : true
  }}
}}
EOF
'''

        script += '''
echo "Asset Catalog 结构已创建!"
echo "请将生成的 PNG 图片复制到对应的 .imageset 目录中"
'''

        return script

    def generate_replacement_plan(self) -> Dict:
        """生成替换计划报告"""
        files = self.scan_files()
        plan = {
            "total_files": len(files),
            "files": {},
            "summary": {
                "total_icons_used": 0,
                "unique_icons": set(),
                "files_to_modify": []
            }
        }

        for file_path in files:
            usages = self.find_icon_usage(file_path)
            if usages:
                relative_path = file_path.relative_to(self.project_root)
                plan["files"][str(relative_path)] = [
                    {"line": line, "icon": icon, "match": match}
                    for line, icon, match in usages
                ]
                plan["summary"]["total_icons_used"] += len(usages)
                plan["summary"]["unique_icons"].update([icon for _, icon, _ in usages])
                plan["summary"]["files_to_modify"].append(str(relative_path))

        plan["summary"]["unique_icons"] = list(plan["summary"]["unique_icons"])
        plan["summary"]["unique_count"] = len(plan["summary"]["unique_icons"])

        return plan

    def save_reports(self) -> None:
        """保存所有报告文件"""
        output_dir = Path("scripts/icon_workflow/output/replacement")
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 生成替换计划
        plan = self.generate_replacement_plan()
        plan_path = output_dir / "replacement_plan.json"
        with open(plan_path, 'w', encoding='utf-8') as f:
            # convert set to list for JSON serialization
            plan_copy = dict(plan)
            plan_copy["summary"]["unique_icons"] = list(plan_copy["summary"]["unique_icons"])
            json.dump(plan_copy, f, ensure_ascii=False, indent=2)

        print(f"✅ 替换计划已生成: {plan_path}")
        print(f"   - 需要修改的文件: {plan['summary']['unique_count']} 个")
        print(f"   - 使用的图标总数: {plan['summary']['total_icons_used']} 次")
        print(f"   - 唯一图标数: {plan['summary']['unique_count']} 个")

        # 2. 生成 SwiftUI 扩展代码
        extension_code = self.create_icon_extension()
        extension_path = output_dir / "IconExtension.swift"
        with open(extension_path, 'w', encoding='utf-8') as f:
            f.write(extension_code)

        print(f"✅ 图标扩展代码已生成: {extension_path}")

        # 3. 生成 Asset Catalog 创建脚本
        asset_script = self.create_asset_catalog_script()
        script_path = output_dir / "create_assets.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(asset_script)

        print(f"✅ Asset Catalog 脚本已生成: {script_path}")

        # 4. 生成替换说明文档
        doc = self.generate_documentation(plan)
        doc_path = output_dir / "REPLACEMENT_GUIDE.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc)

        print(f"✅ 替换指南已生成: {doc_path}")

        return plan

    def generate_documentation(self, plan: Dict) -> str:
        """生成替换说明文档"""
        doc = f'''# iOS 图标替换指南

## 概述

本文档说明如何将 iOS 项目中的 SF Symbol 替换为自定义图标。

## 统计信息

- 需要修改的文件: {len(plan['summary']['files_to_modify'])} 个
- 唯一图标数: {plan['summary']['unique_count']} 个
- 图标使用总数: {plan['summary']['total_icons_used']} 次

## 步骤

### 1. 批量生成所有图标

```bash
cd /Users/zhuxinye/Desktop/project/home-health
python scripts/icon_workflow/batch_generator.py batch
```

### 2. 处理图标（转透明、裁剪）

```bash
python scripts/icon_workflow/image_processor.py
```

### 3. 创建 Asset Catalog

```bash
bash scripts/icon_workflow/output/replacement/create_assets.sh
```

### 4. 复制图标到 Asset Catalog

```bash
# 将处理后的图标复制到对应的 .imageset 目录
python scripts/icon_workflow/copy_assets.py
```

### 5. 添加图标扩展代码

将 `IconExtension.swift` 添加到 Xcode 项目中。

### 6. 替换代码中的图标引用

查找并替换：
- `Image(systemName: "chevron.right")` → `Image(icon: "chevronRight")`

## 使用方式

```swift
// 使用自定义图标
Image(icon: "chevronRight")
    .foregroundColor(.purple)

// 或使用枚举
Image(icon: IconName.chevronRight.rawValue)
```

## 文件清单

需要修改的文件:
'''

        for file_path in plan['summary']['files_to_modify']:
            doc += f"- `{file_path}`\n"

        return doc


def main():
    """主函数"""
    project_root = "/Users/zhuxinye/Desktop/project/home-health"

    replacer = IconReplacer(project_root)
    replacer.save_reports()


if __name__ == "__main__":
    main()
