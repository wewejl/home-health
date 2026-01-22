#!/usr/bin/env python3
"""
批量图标生成器 - 使用 LiblibAI API 批量生成图标
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from liblib_client import LiblibAIClient, APIConfig


class IconBatchGenerator:
    """批量图标生成器"""

    def __init__(self, access_key: str, secret_key: str):
        self.config = APIConfig(
            access_key=access_key,
            secret_key=secret_key
        )
        self.client = LiblibAIClient(self.config)
        self.output_dir = Path("scripts/icon_workflow/output/icons")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_manifest(self) -> List[Dict[str, Any]]:
        """加载图标清单"""
        manifest_path = Path("scripts/icon_workflow/output/icon_manifest.json")
        if not manifest_path.exists():
            raise FileNotFoundError("请先运行 icon_analyzer.py 生成清单")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data["icons"]

    def generate_single_icon(
        self,
        icon_name: str,
        prompt: str,
        index: int = 0,
        total: int = 0
    ) -> bool:
        """
        生成单个图标

        Args:
            icon_name: 图标名称
            prompt: 生成 prompt
            index: 当前索引
            total: 总数

        Returns:
            是否成功
        """
        prefix = f"[{index + 1}/{total}] " if total > 0 else ""

        try:
            # 提交生成请求
            uuid = self.client.generate_image(
                prompt=prompt,
                width=512,
                height=512,
                negative_prompt="photorealistic, 3d, complex details, shading, gradients, messy, blurry, noise, watermark, text"
            )

            # 等待生成完成
            image_url = self.client.wait_for_completion(
                uuid,
                check_interval=5,
                timeout=180
            )

            if image_url:
                # 下载图片
                # 将 SF Symbol 名称转换为有效的文件名
                safe_name = icon_name.replace(".", "_")
                save_path = self.output_dir / f"{safe_name}.png"

                if self.client.download_image(image_url, str(save_path)):
                    print(f"{prefix}✅ {icon_name} -> {save_path.name}")
                    return True

            print(f"{prefix}❌ {icon_name} 生成失败")
            return False

        except Exception as e:
            print(f"{prefix}❌ {icon_name} 错误: {e}")
            return False

    def generate_batch(
        self,
        limit: int = None,
        start_from: int = 0,
        icon_filter: List[str] = None
    ) -> Dict[str, Any]:
        """
        批量生成图标

        Args:
            limit: 生成数量限制
            start_from: 从第几个开始
            icon_filter: 只生成指定的图标列表

        Returns:
            生成结果统计
        """
        icons = self.load_manifest()

        # 过滤
        if icon_filter:
            icons = [icon for icon in icons if icon["name"] in icon_filter]

        if start_from > 0:
            icons = icons[start_from:]

        if limit:
            icons = icons[:limit]

        total = len(icons)
        print(f"开始批量生成 {total} 个图标...\n")

        results = {
            "total": total,
            "success": 0,
            "failed": 0,
            "icons": []
        }

        for i, icon in enumerate(icons):
            icon_name = icon["name"]
            prompt = icon["prompt_en"]

            success = self.generate_single_icon(
                icon_name=icon_name,
                prompt=prompt,
                index=i,
                total=total
            )

            if success:
                results["success"] += 1
                results["icons"].append({
                    "name": icon_name,
                    "status": "success"
                })
            else:
                results["failed"] += 1
                results["icons"].append({
                    "name": icon_name,
                    "status": "failed"
                })

            # 避免请求过快
            time.sleep(2)

        # 保存结果
        results_path = self.output_dir / "generation_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*50}")
        print(f"批量生成完成!")
        print(f"  成功: {results['success']}")
        print(f"  失败: {results['failed']}")
        print(f"  结果已保存: {results_path}")

        return results

    def generate_test_samples(self) -> None:
        """生成几个测试样本图标"""
        test_icons = [
            "chevron.right",
            "checkmark.circle.fill",
            "heart.fill",
            "brain.head.profile",
            "bubble.left.fill"
        ]

        print("生成测试样本图标...\n")
        self.generate_batch(limit=5, icon_filter=test_icons)


if __name__ == "__main__":
    import sys

    # API 配置
    ACCESS_KEY = "R5FqjMESjuO4qrygB8FkvQ"
    SECRET_KEY = "LVtCbjmHTL_R3Lm1vIxKiOUyYDGnSwEr"

    generator = IconBatchGenerator(ACCESS_KEY, SECRET_KEY)

    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            # 生成测试样本
            generator.generate_test_samples()

        elif command == "batch":
            # 批量生成所有
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            generator.generate_batch(limit=limit)

        elif command == "continue":
            # 继续之前的任务
            start_from = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            generator.generate_batch(start_from=start_from)

        else:
            print(f"未知命令: {command}")
            print("可用命令: test, batch [limit], continue [start_from]")
    else:
        # 默认生成测试样本
        generator.generate_test_samples()
