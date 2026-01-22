#!/usr/bin/env python3
"""
自动替换 Swift 代码中的 SF Symbol 为自定义图标
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# SF Symbol 到自定义图标的映射
# 注意：Swift 中使用驼峰命名，资源名使用下划线
SF_TO_CUSTOM = {
    "chevron.right": "chevronRight",
    "chevron.left": "chevronLeft",
    "chevron.down": "chevronDown",
    "arrow.up": "arrowUp",
    "arrow.clockwise": "arrowClockwise",
    "arrow.triangle.merge": "arrowTriangleMerge",
    "plus.circle.fill": "plusCircleFill",
    "pencil": "pencil",
    "xmark.circle.fill": "xmarkCircleFill",
    "xmark": "xmark",
    "checkmark.circle.fill": "checkmarkCircleFill",
    "checkmark.seal.fill": "checkmarkSealFill",
    "slider.horizontal.3": "sliderHorizontal3",
    "square.and.pencil": "squareAndPencil",
    "ellipsis.circle": "ellipsisCircle",
    "flame.fill": "flameFill",
    "sparkles": "sparkles",
    "stop.fill": "stopFill",
    "lock.shield": "lockShield",
    "clock.arrow.circlepath": "clockArrowCirclepath",
    "exclamationmark.triangle": "exclamationmarkTriangle",
    "exclamationmark.triangle.fill": "exclamationmarkTriangleFill",
    "bubble.left.and.bubble.right": "bubbleLeftAndBubbleRight",
    "bubble.left.fill": "bubbleLeftFill",
    "envelope": "envelope",
    "speaker.wave.2.fill": "speakerWave2Fill",
    "mic.fill": "micFill",
    "mic.slash.fill": "micSlashFill",
    "paperplane.fill": "paperplaneFill",
    "brain.head.profile": "brainHeadProfile",
    "heart.fill": "heartFill",
    "cross.fill": "crossFill",
    "note.text": "noteText",
    "doc.text": "docText",
    "doc.text.fill": "docTextFill",
    "doc.text.viewfinder": "docTextViewfinder",
    "calendar": "calendar",
    "link": "link",
    "square.and.arrow.down": "squareAndArrowDown",
    "square.and.arrow.up": "squareAndArrowUp",
    "person.fill": "personFill",
    "person.circle.fill": "personCircleFill",
    "person.2.slash": "person2Slash",
    "person.crop.circle.badge.plus": "personCropCircleBadgePlus",
    "person.fill.viewfinder": "personFillViewfinder",
    "building.2.slash": "building2Slash",
    "rectangle.portrait.and.arrow.right": "rectanglePortraitAndArrowRight",
    "magnifyingglass": "magnifyingglass",
    "face.smiling": "faceSmiling",
}


class IconReplacer:
    """图标替换器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.views_dir = self.project_root / "ios/xinlingyisheng/xinlingyisheng/Views"
        self.backup_dir = self.project_root / "ios/icon_replacement_backup"

    def backup_files(self) -> None:
        """备份要修改的文件"""
        import shutil

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        swift_files = list(self.views_dir.rglob("*.swift"))

        for file_path in swift_files:
            relative = file_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)

        print(f"✅ 已备份 {len(swift_files)} 个文件到: {self.backup_dir.relative_to(self.project_root)}")

    def replace_in_file(self, file_path: Path) -> Tuple[int, int]:
        """
        在单个文件中替换图标引用

        Returns:
            (替换数量, 匹配数量)
        """
        content = file_path.read_text(encoding='utf-8')

        total_matches = 0
        replacements = 0

        # 按名称长度降序排序，避免部分匹配问题
        for sf_name, custom_name in sorted(SF_TO_CUSTOM.items(), key=lambda x: len(x[0]), reverse=True):
            # 匹配 Image(systemName: "xxx")
            pattern = rf'Image\(systemName:\s*"{re.escape(sf_name)}"\)'

            matches = list(re.finditer(pattern, content))
            total_matches += len(matches)

            if matches:
                # 替换
                replacement = f'Image(icon: "{custom_name}")'
                content = re.sub(pattern, replacement, content)
                replacements += len(matches)

        # 写回文件
        if replacements > 0:
            file_path.write_text(content, encoding='utf-8')

        return replacements, total_matches

    def replace_all(self) -> Dict:
        """在所有文件中替换图标引用"""
        swift_files = list(self.views_dir.rglob("*.swift"))

        print(f"找到 {len(swift_files)} 个 Swift 文件\n")

        results = {
            "total_files": len(swift_files),
            "files_modified": [],
            "total_replacements": 0,
            "total_matches": 0
        }

        for file_path in swift_files:
            replacements, matches = self.replace_in_file(file_path)

            if replacements > 0:
                relative = file_path.relative_to(self.project_root)
                results["files_modified"].append(str(relative))
                results["total_replacements"] += replacements
                results["total_matches"] += matches
                print(f"  ✅ {relative}: {replacements} 处替换")

        print(f"\n{'='*50}")
        print(f"替换完成:")
        print(f"  修改文件: {len(results['files_modified'])} 个")
        print(f"  总替换数: {results['total_replacements']} 处")
        print(f"  总匹配数: {results['total_matches']} 处")

        return results


def main():
    """主函数"""
    project_root = "/Users/zhuxinye/Desktop/project/home-health"

    replacer = IconReplacer(project_root)

    print("=" * 50)
    print("开始替换图标引用...")
    print("=" * 50)

    # 1. 备份文件
    print("\n步骤 1: 备份原始文件")
    replacer.backup_files()

    # 2. 执行替换
    print("\n步骤 2: 替换图标引用")
    results = replacer.replace_all()

    print("\n" + "=" * 50)
    print("替换完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()
