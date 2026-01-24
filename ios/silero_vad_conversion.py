#!/usr/bin/env python3
"""
Silero VAD 模型下载与 Core ML 转换脚本

用法：
    python silero_vad_conversion.py
"""

import os
import urllib.request
from pathlib import Path

# Silero VAD 模型 URL
SILERO_VAD_URL = "https://github.com/snakers4/silero-vad/raw/files/models/silero_vad.onnx"

def download_file(url: str, dest_path: Path) -> bool:
    """下载文件"""
    try:
        print(f"正在下载 {url}...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"下载完成: {dest_path}")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False

def convert_to_coreml(onnx_path: Path, mlmodel_path: Path) -> bool:
    """将 ONNX 模型转换为 Core ML 格式"""
    try:
        import coremltools as ct
        import onnx

        print(f"正在加载 ONNX 模型: {onnx_path}...")
        onnx_model = onnx.load(str(onnx_path))

        print("正在转换为 Core ML 格式...")
        # 转换模型
        mlmodel = ct.convert(
            onnx_model,
            source="onnx",
            inputs=[ct.TensorType(name="input", shape=(1, 512), dtype=np.float32)]
        )

        print(f"正在保存 Core ML 模型: {mlmodel_path}...")
        mlmodel.save(str(mlmodel_path))
        print("转换完成!")
        return True

    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请运行: pip install coremltools onnx")
        return False
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def main():
    # 确定输出路径
    script_dir = Path(__file__).parent
    models_dir = script_dir / "xinlingyisheng" / "Models"
    models_dir.mkdir(parents=True, exist_ok=True)

    onnx_path = models_dir / "silero_vad.onnx"
    mlmodel_path = models_dir / "SileroVAD.mlmodel"

    # 检查是否已有 mlmodel 文件
    if mlmodel_path.exists():
        print(f"Core ML 模型已存在: {mlmodel_path}")
        return

    # 检查是否已有 onnx 文件
    if not onnx_path.exists():
        if not download_file(SILERO_VAD_URL, onnx_path):
            print("下载失败，退出")
            return
    else:
        print(f"ONNX 模型已存在: {onnx_path}")

    # 转换模型
    convert_to_coreml(onnx_path, mlmodel_path)

if __name__ == "__main__":
    main()
