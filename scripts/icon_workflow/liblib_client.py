#!/usr/bin/env python3
"""
LiblibAI 星流 Star-3 Alpha API 客户端
用于批量生成图标
"""

import hashlib
import hmac
import base64
import json
import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    """API 配置"""
    access_key: str
    secret_key: str
    base_url: str = "https://openapi.liblibai.cloud"

    # 星流 Star-3 Alpha 文生图配置
    template_uuid: str = "5d7e67009b344550bc1aa6ccbfa1d7f4"
    text2img_uri: str = "/api/generate/webui/text2img/ultra"
    status_uri: str = "/api/generate/webui/status"


class LiblibAIClient:
    """LiblibAI API 客户端"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "LiblibAI-Python-Client/1.0"
        })

    def _generate_signature(self, uri: str) -> tuple[str, str, str]:
        """
        生成 API 签名

        Args:
            uri: 请求的 URI 路径

        Returns:
            (signature, timestamp, nonce)
        """
        timestamp = str(int(time.time() * 1000))
        nonce = self._generate_nonce(10)

        # 拼接原文: uri + "&" + timestamp + "&" + nonce
        original_string = f"{uri}&{timestamp}&{nonce}"

        # 使用 SecretKey 进行 HMAC-SHA1 加密
        key_bytes = self.config.secret_key.encode('utf-8')
        message_bytes = original_string.encode('utf-8')

        hmac_obj = hmac.new(key_bytes, message_bytes, hashlib.sha1)
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')

        # 转换为 URL 安全的 Base64
        signature = signature.replace('+', '-').replace('/', '_').replace('=', '')

        return signature, timestamp, nonce

    def _generate_nonce(self, length: int = 10) -> str:
        """生成随机字符串"""
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def _build_url(self, uri: str, signature: str, timestamp: str, nonce: str) -> str:
        """构建请求 URL"""
        return (
            f"{self.config.base_url}{uri}"
            f"?AccessKey={self.config.access_key}"
            f"&Signature={signature}"
            f"&Timestamp={timestamp}"
            f"&SignatureNonce={nonce}"
        )

    def generate_image(
        self,
        prompt: str,
        width: int = 512,
        height: int = 512,
        img_count: int = 1,
        steps: int = 30,
        negative_prompt: str = ""
    ) -> str:
        """
        提交文生图请求

        Args:
            prompt: 正向提示词（英文）
            width: 图片宽度
            height: 图片高度
            img_count: 生成图片数量
            steps: 采样步数
            negative_prompt: 负向提示词

        Returns:
            generate_uuid: 生成任务 UUID
        """
        # 生成签名
        signature, timestamp, nonce = self._generate_signature(self.config.text2img_uri)

        # 构建请求数据
        request_data = {
            "templateUuid": self.config.template_uuid,
            "generateParams": {
                "prompt": prompt,
                "imageSize": {
                    "width": width,
                    "height": height
                },
                "imgCount": img_count,
                "steps": steps
            }
        }

        if negative_prompt:
            request_data["generateParams"]["negativePrompt"] = negative_prompt

        # 构建请求 URL
        url = self._build_url(self.config.text2img_uri, signature, timestamp, nonce)

        # 发送请求
        print(f"正在生成图片: {prompt[:50]}...")
        response = self.session.post(url, json=request_data)

        if response.status_code != 200:
            raise Exception(f"API 请求失败: {response.status_code} - {response.text}")

        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"API 返回错误: {result.get('message', 'Unknown error')}")

        generate_uuid = result.get("data", {}).get("generateUuid")
        if not generate_uuid:
            raise Exception("未返回 generateUuid")

        print(f"任务已提交, UUID: {generate_uuid}")
        return generate_uuid

    def check_status(self, generate_uuid: str) -> Dict[str, Any]:
        """
        查询生成状态

        Args:
            generate_uuid: 生成任务 UUID

        Returns:
            状态信息字典
        """
        # 重新生成签名（注意：查询接口的 URI 不同）
        signature, timestamp, nonce = self._generate_signature(self.config.status_uri)

        # 构建请求数据
        request_data = {
            "generateUuid": generate_uuid
        }

        # 构建请求 URL
        url = self._build_url(self.config.status_uri, signature, timestamp, nonce)

        # 发送请求
        response = self.session.post(url, json=request_data)

        if response.status_code != 200:
            raise Exception(f"API 请求失败: {response.status_code} - {response.text}")

        result = response.json()

        if result.get("code") != 0:
            raise Exception(f"API 返回错误: {result.get('message', 'Unknown error')}")

        return result.get("data", {})

    def wait_for_completion(
        self,
        generate_uuid: str,
        check_interval: int = 3,
        timeout: int = 300
    ) -> Optional[str]:
        """
        等待图片生成完成

        Args:
            generate_uuid: 生成任务 UUID
            check_interval: 检查间隔（秒）
            timeout: 超时时间（秒）

        Returns:
            图片 URL，如果生成失败则返回 None
        """
        start_time = time.time()
        first_check = True  # 第一次检查时先等待一下

        while time.time() - start_time < timeout:
            # 第一次检查前先等待几秒，让任务有时间启动
            if first_check:
                print("等待任务启动...")
                time.sleep(5)
                first_check = False

            status_data = self.check_status(generate_uuid)
            generate_status = status_data.get("generateStatus")

            print(f"当前状态: {generate_status} ({status_data.get('percentCompleted', 0)}%)")

            # 状态码说明:
            # 1, 2, 3 = 执行中
            # 4 = 审核中
            # 5 = 生成成功
            # 6, 7 = 生成失败

            if generate_status in [1, 2, 3]:
                time.sleep(check_interval)

            elif generate_status == 4:
                # 审核中，检查审核状态
                images = status_data.get("images", [])
                if images:
                    audit_status = images[0].get("auditStatus")
                    if audit_status in [1, 2, 3]:
                        print("审核中...")
                        time.sleep(check_interval)
                        continue
                    elif audit_status in [4, 5]:
                        print("内容审核未通过，可能包含敏感内容")
                        return None

            elif generate_status == 5:
                # 生成成功
                images = status_data.get("images", [])
                if images:
                    image_url = images[0].get("imageUrl")
                    print(f"生成成功! 图片 URL: {image_url}")
                    return image_url
                return None

            else:
                print(f"生成失败, 状态: {generate_status}")
                return None

        print("等待超时")
        return None

    def download_image(self, image_url: str, save_path: str) -> bool:
        """
        下载生成的图片

        Args:
            image_url: 图片 URL
            save_path: 保存路径

        Returns:
            是否下载成功
        """
        try:
            response = self.session.get(image_url, stream=True)
            if response.status_code == 200:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"图片已保存: {save_path}")
                return True
        except Exception as e:
            print(f"下载失败: {e}")
        return False


# 测试函数
def test_icon_generation():
    """测试生成一个简单图标"""

    # 配置 API
    config = APIConfig(
        access_key="R5FqjMESjuO4qrygB8FkvQ",
        secret_key="LVtCbjmHTL_R3Lm1vIxKiOUyYDGnSwEr"
    )

    client = LiblibAIClient(config)

    # 测试 prompt - 生成灵犀医生 App 图标（犀牛 + 日式治愈系）
    # 主色 #517A6B (森林雾绿), 背景 #F7F2E8 (奶油白)
    test_prompt = (
        "cute minimalist rhino icon for medical app, Japanese healing style, "
        "flat design, vector style, clean smooth lines, "
        "primary color #517A6B sage green, accent color #B5D1C2 light sage, "
        "background #F7F2E8 warm cream, "
        "friendly rhino face, simple geometric shapes, rounded corners, "
        "professional medical feel, trustworthy, calming, "
        "no shading, no gradients, modern app icon style, high quality"
    )

    test_negative = (
        "photorealistic, 3d, complex, detailed, "
        "shading, gradient, messy, blurry, noise, watermark"
    )

    try:
        # 提交生成请求
        uuid = client.generate_image(
            prompt=test_prompt,
            width=512,
            height=512,
            negative_prompt=test_negative
        )

        # 等待生成完成
        image_url = client.wait_for_completion(uuid)

        if image_url:
            # 下载图片
            output_dir = Path("scripts/icon_workflow/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            save_path = output_dir / "test_gear_icon.png"
            client.download_image(image_url, str(save_path))
            print(f"\n✅ 测试成功! 图标已保存到: {save_path}")
            return True
        else:
            print("\n❌ 生成失败")
            return False

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False


if __name__ == "__main__":
    test_icon_generation()
