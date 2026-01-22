#!/usr/bin/env python3
"""
测试生成多个优化后的图标进行对比
"""

import sys
sys.path.append("scripts/icon_workflow")

from optimized_prompts import OptimizedPromptBuilder
from liblib_client import LiblibAIClient, APIConfig


def test_comparison_icons():
    """生成对比测试图标"""

    config = APIConfig(
        access_key="R5FqjMESjuO4qrygB8FkvQ",
        secret_key="LVtCbjmHTL_R3Lm1vIxKiOUyYDGnSwEr"
    )

    client = LiblibAIClient(config)
    builder = OptimizedPromptBuilder()

    # 选择几个有代表性的图标进行测试
    test_icons = [
        ("chevron.right", "navigation"),
        ("checkmark.circle.fill", "status"),
        ("bubble.left.fill", "communication"),
        ("brain.head.profile", "medical"),
    ]

    print("生成对比测试图标...\n")

    results = []
    for icon_name, icon_type in test_icons:
        icon_def = builder.ICON_DEFINITIONS[icon_name]

        # 使用优化后的 prompt
        prompt = builder.build_prompt(icon_def)
        negative = builder.NEGATIVE_PROMPT

        print(f"[{icon_name}] {icon_def['zh']}")

        try:
            uuid = client.generate_image(
                prompt=prompt,
                negative_prompt=negative,
                width=512,
                height=512
            )

            image_url = client.wait_for_completion(uuid)

            if image_url:
                output_path = f"scripts/icon_workflow/output/comparison/{icon_name}_optimized.png"
                from pathlib import Path
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                if client.download_image(image_url, output_path):
                    print(f"  ✅ 已保存\n")
                    results.append((icon_name, "success"))
                else:
                    print(f"  ❌ 下载失败\n")
                    results.append((icon_name, "download_failed"))
            else:
                print(f"  ❌ 生成失败\n")
                results.append((icon_name, "generate_failed"))

        except Exception as e:
            print(f"  ❌ 错误: {e}\n")
            results.append((icon_name, "error"))

    # 总结
    print("=" * 50)
    print("对比测试完成:")
    success = sum(1 for _, status in results if status == "success")
    print(f"  成功: {success}/{len(results)}")

    return results


if __name__ == "__main__":
    test_comparison_icons()
