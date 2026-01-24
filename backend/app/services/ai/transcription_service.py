"""
语音转写服务

功能：
- 将语音录音转换为文本
- 支持多种音频格式
- 提取症状关键词
- 支持实时和离线转写
"""
import os
import json
import base64
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from .base_ai_service import BaseAIService
from ...config import get_settings

settings = get_settings()


class TranscriptionStatus(str, Enum):
    """转写状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionSegment:
    """转写分段"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    text: str          # 文本内容
    confidence: float  # 置信度


@dataclass
class TranscriptionResult:
    """转写结果"""
    task_id: str
    status: TranscriptionStatus
    text: str                              # 完整转写文本
    duration: float                        # 音频时长（秒）
    confidence: float                      # 整体置信度
    segments: List[TranscriptionSegment]   # 分段信息
    extracted_symptoms: List[str]          # 提取的症状
    language: str                          # 识别的语言
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["created_at"] = self.created_at.isoformat()
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
        return result


class SpeechTranscriptionService(BaseAIService):
    """语音转写服务"""
    
    # 支持的音频格式
    SUPPORTED_FORMATS = ["mp3", "wav", "m4a", "aac", "ogg", "flac", "webm"]
    
    # 最大文件大小（字节）
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # 最大时长（秒）
    MAX_DURATION = 600  # 10分钟
    
    def __init__(self):
        super().__init__()
        self._task_cache: Dict[str, TranscriptionResult] = {}
    
    async def transcribe(
        self,
        audio_url: Optional[str] = None,
        audio_base64: Optional[str] = None,
        audio_path: Optional[str] = None,
        language: str = "zh",
        extract_symptoms: bool = True
    ) -> TranscriptionResult:
        """
        转写音频
        
        Args:
            audio_url: 音频 URL
            audio_base64: Base64 编码的音频
            audio_path: 本地音频文件路径
            language: 语言代码
            extract_symptoms: 是否提取症状
        
        Returns:
            TranscriptionResult 转写结果
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # 创建初始结果
        result = TranscriptionResult(
            task_id=task_id,
            status=TranscriptionStatus.PROCESSING,
            text="",
            duration=0.0,
            confidence=0.0,
            segments=[],
            extracted_symptoms=[],
            language=language,
            created_at=datetime.utcnow()
        )
        
        try:
            # 获取音频数据
            audio_data = await self._get_audio_data(audio_url, audio_base64, audio_path)
            
            if not audio_data:
                result.status = TranscriptionStatus.FAILED
                result.error_message = "无法获取音频数据"
                return result
            
            # 调用转写 API
            transcription = await self._call_transcription_api(audio_data, language)
            
            if transcription:
                result.text = transcription.get("text", "")
                result.duration = transcription.get("duration", 0.0)
                result.confidence = transcription.get("confidence", 0.8)
                result.segments = self._parse_segments(transcription.get("segments", []))
                result.language = transcription.get("language", language)
                result.status = TranscriptionStatus.COMPLETED
                result.completed_at = datetime.utcnow()
                
                # 提取症状
                if extract_symptoms and result.text:
                    result.extracted_symptoms = await self._extract_symptoms_from_text(result.text)
            else:
                result.status = TranscriptionStatus.FAILED
                result.error_message = "转写失败"
            
        except Exception as e:
            result.status = TranscriptionStatus.FAILED
            result.error_message = str(e)
        
        # 缓存结果
        self._task_cache[task_id] = result
        
        return result
    
    async def get_task_status(self, task_id: str) -> Optional[TranscriptionResult]:
        """获取转写任务状态"""
        return self._task_cache.get(task_id)
    
    async def transcribe_with_llm(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 LLM 处理转写文本（后处理）
        
        Args:
            text: 原始转写文本
            context: 上下文信息
        
        Returns:
            处理后的结果
        """
        system_prompt = """你是一位医疗语音助手，负责处理患者的语音描述。

你的任务：
1. 清理和规范化文本
2. 提取关键症状信息
3. 识别时间、程度等关键细节
4. 输出结构化 JSON"""

        user_prompt = f"""请处理以下语音转写文本，提取医疗相关信息。

转写文本：{text}
{"上下文：" + context if context else ""}

请输出 JSON 格式：
{{
    "cleaned_text": "清理后的文本",
    "symptoms": ["症状1", "症状2"],
    "symptom_details": [
        {{
            "symptom": "症状名",
            "duration": "持续时间",
            "severity": "严重程度",
            "location": "部位"
        }}
    ],
    "time_mentions": ["时间提及"],
    "key_info": ["其他关键信息"],
    "follow_up_questions": ["建议追问的问题"]
}}

请直接输出 JSON："""

        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            
            return self._parse_json(response, {
                "cleaned_text": text,
                "symptoms": [],
                "symptom_details": [],
                "time_mentions": [],
                "key_info": [],
                "follow_up_questions": []
            })
            
        except Exception as e:
            print(f"LLM 后处理失败: {e}")
            return {"cleaned_text": text, "symptoms": []}
    
    async def _get_audio_data(
        self,
        url: Optional[str],
        base64_data: Optional[str],
        file_path: Optional[str]
    ) -> Optional[bytes]:
        """获取音频数据"""
        if base64_data:
            try:
                return base64.b64decode(base64_data)
            except:
                return None
        
        if url:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return response.content
            except:
                return None
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    return f.read()
            except:
                return None
        
        return None
    
    async def _call_transcription_api(
        self,
        audio_data: bytes,
        language: str
    ) -> Optional[Dict]:
        """
        调用转写 API

        注意：这里提供了多种实现方案，根据 ASR_PROVIDER 配置选择
        """
        provider = settings.ASR_PROVIDER

        # 方案1: 使用 GLM-ASR（智谱语音识别）
        if provider == "glm":
            result = await self._transcribe_with_glm(audio_data, language)
            if result:
                return result

        # 方案2: 使用阿里云 Paraformer
        if provider == "aliyun":
            result = await self._transcribe_with_aliyun(audio_data, language)
            if result:
                return result

        # 方案3: 使用 OpenAI Whisper API
        if provider == "openai":
            result = await self._transcribe_with_whisper(audio_data, language)
            if result:
                return result

        # 方案4: 本地模拟（开发测试用）
        return self._mock_transcription(audio_data)

    async def _transcribe_with_glm(
        self,
        audio_data: bytes,
        language: str
    ) -> Optional[Dict]:
        """
        GLM-ASR-2512 转写（智谱语音识别）

        需要配置 GLM_API_KEY
        """
        api_key = settings.GLM_API_KEY
        if not api_key:
            print("GLM_API_KEY 未配置")
            return None

        try:
            import io

            # GLM API 使用 Bearer Token 格式
            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            # 准备 multipart/form-data
            files = {
                "file": ("audio.m4a", io.BytesIO(audio_data), "audio/m4a"),
                "model": (None, settings.GLM_ASR_MODEL),
                "stream": (None, "false")
            }

            print(f"[GLM-ASR] 正在调用 GLM-ASR API，音频大小: {len(audio_data)} bytes")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.GLM_ASR_BASE_URL,
                    headers=headers,
                    files=files
                )

                print(f"[GLM-ASR] API 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    text = data.get("text", "")

                    print(f"[GLM-ASR] 转写成功: {text[:50]}...")

                    return {
                        "text": text,
                        "duration": data.get("duration", 0),
                        "confidence": 0.9,  # GLM-ASR 不返回置信度，给个默认值
                        "language": "zh",  # GLM-ASR 自动识别语言
                        "segments": []
                    }
                else:
                    error_text = response.text
                    print(f"[GLM-ASR] API 错误: {error_text}")
                    return None

        except Exception as e:
            print(f"[GLM-ASR] 转写失败: {e}")
            import traceback
            traceback.print_exc()

        return None

    async def _transcribe_with_aliyun(
        self,
        audio_data: bytes,
        language: str
    ) -> Optional[Dict]:
        """
        阿里云 Paraformer 转写
        
        需要配置：
        - ALIYUN_ASR_ACCESS_KEY
        - ALIYUN_ASR_ACCESS_SECRET
        """
        # TODO: 实现阿里云 ASR 接口
        # 参考文档：https://help.aliyun.com/document_detail/324392.html
        return None
    
    async def _transcribe_with_whisper(
        self,
        audio_data: bytes,
        language: str
    ) -> Optional[Dict]:
        """
        OpenAI Whisper API 转写
        
        需要配置 OPENAI_API_KEY
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return None
        
        try:
            import io
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                files = {
                    "file": ("audio.wav", io.BytesIO(audio_data), "audio/wav"),
                    "model": (None, "whisper-1"),
                    "language": (None, language),
                    "response_format": (None, "verbose_json")
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    files=files
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "text": data.get("text", ""),
                        "duration": data.get("duration", 0),
                        "confidence": 0.9,
                        "language": data.get("language", language),
                        "segments": data.get("segments", [])
                    }
        except Exception as e:
            print(f"Whisper 转写失败: {e}")
        
        return None
    
    def _mock_transcription(self, audio_data: bytes) -> Dict:
        """模拟转写（开发测试用）"""
        # 根据音频大小估算时长
        estimated_duration = len(audio_data) / (16000 * 2)  # 假设16kHz, 16bit
        
        return {
            "text": "[模拟转写结果] 这是一段测试音频的转写文本。",
            "duration": estimated_duration,
            "confidence": 0.85,
            "language": "zh",
            "segments": [
                {
                    "start": 0.0,
                    "end": estimated_duration,
                    "text": "[模拟转写结果]",
                    "confidence": 0.85
                }
            ]
        }
    
    def _parse_segments(self, raw_segments: List[Dict]) -> List[TranscriptionSegment]:
        """解析分段信息"""
        segments = []
        for seg in raw_segments:
            segments.append(TranscriptionSegment(
                start_time=seg.get("start", 0.0),
                end_time=seg.get("end", 0.0),
                text=seg.get("text", ""),
                confidence=seg.get("confidence", 0.8)
            ))
        return segments
    
    async def _extract_symptoms_from_text(self, text: str) -> List[str]:
        """从文本中提取症状"""
        system_prompt = """从以下文本中提取所有提到的症状，只输出症状列表的 JSON 数组。"""
        
        user_prompt = f"""文本：{text}

请输出 JSON 数组格式的症状列表：
["症状1", "症状2"]

只输出 JSON 数组："""

        try:
            response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            # 尝试解析 JSON 数组
            content = response.strip()
            if content.startswith("["):
                return json.loads(content)
            
            return []
            
        except Exception as e:
            print(f"症状提取失败: {e}")
            return []
    
    def validate_audio_file(
        self,
        filename: str,
        file_size: int
    ) -> tuple[bool, str]:
        """
        验证音频文件
        
        Returns:
            (is_valid, error_message)
        """
        # 检查文件格式
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext not in self.SUPPORTED_FORMATS:
            return False, f"不支持的音频格式: {ext}，支持: {', '.join(self.SUPPORTED_FORMATS)}"
        
        # 检查文件大小
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            return False, f"文件过大，最大支持 {max_mb:.0f}MB"
        
        return True, ""


# 单例
_transcription_service: Optional[SpeechTranscriptionService] = None


def get_transcription_service() -> SpeechTranscriptionService:
    """获取转写服务单例"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = SpeechTranscriptionService()
    return _transcription_service
