#!/usr/bin/env python3
"""
图片后处理器 - 处理生成的图标：
1. 将白色背景转换为透明
2. 裁剪到边界框
3. 生成多尺寸变体 (@1x, @2x, @3x)
"""

from PIL import Image, ImageChops, ImageDraw, ImageFilter
import numpy as np
from pathlib import Path
from typing import List, Tuple


class IconProcessor:
    """图标处理器"""

    def __init__(self, input_dir: str = "scripts/icon_workflow/output/icons"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path("scripts/icon_workflow/output/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def white_to_transparent(self, image: Image.Image, threshold: int = 240) -> Image.Image:
        """
        将白色背景转换为透明

        Args:
            image: 输入图片
            threshold: 白色阈值（0-255），大于此值视为白色

        Returns:
            处理后的 RGBA 图片
        """
        # 转换为 RGBA
        image = image.convert("RGBA")

        # 获取像素数据
        data = np.array(image)

        # 创建 alpha 通道：接近白色的像素设为透明
        # RGB 都大于 threshold 的像素视为白色/背景
        white_mask = (
            (data[:, :, 0] > threshold) &  # R
            (data[:, :, 1] > threshold) &  # G
            (data[:, :, 2] > threshold)    # B
        )

        # 设置 alpha 通道
        data[white_mask, 3] = 0  # 白色区域透明

        # 抗锯齿边缘：对接近白色的像素进行半透明处理
        for i in range(threshold - 30, threshold):
            edge_mask = (
                (data[:, :, 0] > i) &
                (data[:, :, 1] > i) &
                (data[:, :, 2] > i) &
                (~white_mask)  # 不在纯白区域
            )
            # 计算透明度比例
            alpha_ratio = (threshold - i) / 30
            data[edge_mask, 3] = (data[edge_mask, 3] * alpha_ratio).astype(np.uint8)

        return Image.fromarray(data)

    def trim_whitespace(self, image: Image.Image, padding: int = 10) -> Image.Image:
        """
        裁剪掉周围的空白区域

        Args:
            image: 输入图片（应该是 RGBA）
            padding: 保留的内边距

        Returns:
            裁剪后的图片
        """
        # 获取边界框
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # 获取非透明像素的边界框
        bbox = image.getbbox()
        if bbox is None:
            # 整张图片都是透明的
            return image

        # 添加内边距
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(image.width, bbox[2] + padding)
        bottom = min(image.height, bbox[3] + padding)

        # 如果有内容则裁剪
        if left < right and top < bottom:
            return image.crop((left, top, right, bottom))

        return image

    def create_resized_variants(
        self,
        image: Image.Image,
        base_size: int = 64
    ) -> List[Tuple[int, Image.Image]]:
        """
        创建多尺寸变体

        Args:
            image: 原始图片
            base_size: 基础尺寸 (@1x)

        Returns:
            [(scale, image), ...] 列表
        """
        variants = []
        for scale in [1, 2, 3]:
            size = base_size * scale
            resized = image.resize((size, size), Image.Resampling.LANCZOS)
            variants.append((scale, resized))

        return variants

    def process_single_icon(
        self,
        input_path: Path,
        base_name: str,
        remove_white: bool = True,
        trim: bool = True
    ) -> dict:
        """
        处理单个图标

        Args:
            input_path: 输入图片路径
            base_name: 基础文件名（不含扩展名）
            remove_white: 是否移除白色背景
            trim: 是否裁剪空白

        Returns:
            处理结果信息
        """
        try:
            # 加载图片
            img = Image.open(input_path)

            # 步骤1: 白色背景转透明
            if remove_white:
                img = self.white_to_transparent(img)

            # 步骤2: 裁剪空白
            if trim:
                img = self.trim_whitespace(img)

            # 步骤3: 保存处理后的原始尺寸
            processed_path = self.output_dir / f"{base_name}_processed.png"
            img.save(processed_path, "PNG")

            # 步骤4: 生成多尺寸变体
            variants_dir = self.output_dir / "variants" / base_name
            variants_dir.mkdir(parents=True, exist_ok=True)

            # iOS 图标常用尺寸
            ios_sizes = {
                16: "@1x",
                32: "@2x",
                48: "@3x",
                64: "@1x",
                128: "@2x",
                256: "@1x"
            }

            for size, suffix in ios_sizes.items():
                if size <= 512:  # 不超过原始尺寸
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    output_name = f"{base_name}_{size}{suffix}.png"
                    resized.save(variants_dir / output_name, "PNG")

            return {
                "name": base_name,
                "status": "success",
                "original_size": Image.open(input_path).size,
                "processed_size": img.size,
                "variants_path": str(variants_dir)
            }

        except Exception as e:
            return {
                "name": base_name,
                "status": "error",
                "error": str(e)
            }

    def process_all(self) -> List[dict]:
        """批量处理所有图标"""
        results = []

        for input_path in self.input_dir.glob("*.png"):
            if "generation_results" in input_path.name:
                continue

            base_name = input_path.stem
            print(f"处理: {base_name}")

            result = self.process_single_icon(input_path, base_name)
            results.append(result)

            if result["status"] == "success":
                print(f"  ✅ {result['original_size']} -> {result['processed_size']}")
            else:
                print(f"  ❌ {result.get('error', 'Unknown error')}")

        # 保存处理报告
        import json
        report_path = self.output_dir / "processing_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n处理完成! 报告已保存: {report_path}")

        return results

    def verify_transparency(self, image_path: Path) -> bool:
        """验证图片是否包含透明区域"""
        img = Image.open(image_path)
        if img.mode != "RGBA":
            return False

        # 检查是否有透明像素
        alpha = img.split()[-1]
        for pixel in alpha.getdata():
            if pixel < 255:
                return True

        return False


def test_processor():
    """测试处理器"""
    processor = IconProcessor()

    # 处理单个测试图标
    test_input = Path("scripts/icon_workflow/output/icons/chevron_right.png")
    if test_input.exists():
        result = processor.process_single_icon(
            test_input,
            "chevron_right",
            remove_white=True,
            trim=True
        )

        print(f"\n处理结果: {result}")

        # 验证透明度
        processed_path = Path("scripts/icon_workflow/output/processed/chevron_right_processed.png")
        if processed_path.exists():
            has_transparency = processor.verify_transparency(processed_path)
            print(f"包含透明区域: {has_transparency}")


if __name__ == "__main__":
    import sys

    processor = IconProcessor()

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_processor()
    else:
        # 批量处理所有
        processor.process_all()
