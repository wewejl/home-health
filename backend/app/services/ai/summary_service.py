"""
AI 摘要服务

功能：
- 从病历事件中生成结构化摘要
- 提取症状信息
- 生成时间轴
- 风险评估
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .base_ai_service import BaseAIService
from .prompts.summary_prompts import SUMMARY_PROMPTS


@dataclass
class SymptomDetail:
    """症状详情"""
    name: str
    duration: Optional[str] = None
    severity: Optional[str] = None
    body_part: Optional[str] = None
    characteristics: Optional[List[str]] = None


@dataclass
class TimelineEvent:
    """时间轴事件"""
    timestamp: str
    type: str  # symptom_onset/consultation/image_upload/note/treatment
    title: str
    description: Optional[str] = None
    importance: str = "medium"


@dataclass
class SummaryResult:
    """摘要结果"""
    summary: str
    key_points: List[str]
    symptoms: List[str]
    symptom_details: Dict[str, Dict]
    possible_diagnosis: List[str]
    risk_level: str
    risk_warning: Optional[str]
    recommendations: List[str]
    follow_up_reminders: List[str]
    timeline: List[Dict]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AISummaryService(BaseAIService):
    """AI 摘要服务"""
    
    def __init__(self):
        super().__init__(
            temperature=0.3,
            max_tokens=2000
        )
    
    async def generate_summary(
        self,
        chief_complaint: str,
        department: str,
        sessions: List[Dict],
        attachments: Optional[List[Dict]] = None,
        notes: Optional[List[Dict]] = None,
        existing_analysis: Optional[Dict] = None
    ) -> SummaryResult:
        """
        生成病历摘要
        
        Args:
            chief_complaint: 主诉
            department: 科室
            sessions: 会话记录列表
            attachments: 附件列表
            notes: 用户备注列表
            existing_analysis: 现有 AI 分析
        
        Returns:
            SummaryResult 摘要结果
        """
        # 格式化对话记录
        conversation = self._format_conversations(sessions)
        
        # 格式化附件信息
        attachments_text = self._format_attachments(attachments or [])
        
        # 格式化备注
        notes_text = self._format_notes(notes or [])
        
        # 构建提示词
        prompt = SUMMARY_PROMPTS["generate_summary"].format(
            chief_complaint=chief_complaint or "未提供",
            department=department or "未知",
            conversation=conversation,
            attachments=attachments_text,
            notes=notes_text
        )
        
        try:
            response = await self._call_llm(
                system_prompt=SUMMARY_PROMPTS["system"],
                user_prompt=prompt
            )
            
            result = self._parse_json(response, self._get_default_summary())
            
            return SummaryResult(
                summary=result.get("summary", "暂无摘要"),
                key_points=result.get("key_points", []),
                symptoms=result.get("symptoms", []),
                symptom_details=result.get("symptom_details", {}),
                possible_diagnosis=result.get("possible_diagnosis", []),
                risk_level=result.get("risk_level", "low"),
                risk_warning=result.get("risk_warning"),
                recommendations=result.get("recommendations", []),
                follow_up_reminders=result.get("follow_up_reminders", []),
                timeline=result.get("timeline", []),
                confidence=result.get("confidence", 0.5)
            )
            
        except Exception as e:
            print(f"AI 摘要生成失败: {e}")
            return self._get_fallback_summary(chief_complaint, department, sessions)
    
    async def extract_symptoms(
        self,
        conversation: str
    ) -> Dict[str, Any]:
        """
        从对话中提取症状信息
        
        Args:
            conversation: 对话文本
        
        Returns:
            症状提取结果
        """
        prompt = SUMMARY_PROMPTS["extract_symptoms"].format(
            conversation=conversation
        )
        
        try:
            response = await self._call_llm(
                system_prompt=SUMMARY_PROMPTS["system"],
                user_prompt=prompt,
                temperature=0.2
            )
            
            result = self._parse_json(response, {"symptoms": [], "red_flags": []})
            return result
            
        except Exception as e:
            print(f"症状提取失败: {e}")
            return {"symptoms": [], "red_flags": [], "confidence": 0}
    
    async def generate_timeline(
        self,
        chief_complaint: str,
        sessions: List[Dict],
        attachments: Optional[List[Dict]] = None,
        notes: Optional[List[Dict]] = None
    ) -> List[TimelineEvent]:
        """
        生成时间轴事件
        
        Args:
            chief_complaint: 主诉
            sessions: 会话记录
            attachments: 附件
            notes: 备注
        
        Returns:
            时间轴事件列表
        """
        # 构建基础时间轴（基于实际数据）
        timeline = []
        
        # 添加会话事件
        for session in sessions:
            timestamp = session.get("timestamp") or session.get("created_at")
            if timestamp:
                timeline.append(TimelineEvent(
                    timestamp=timestamp,
                    type="consultation",
                    title=session.get("summary", "问诊记录"),
                    description=session.get("session_type", ""),
                    importance="high"
                ))
        
        # 添加附件事件
        for att in (attachments or []):
            timestamp = att.get("upload_time") or att.get("created_at")
            if timestamp:
                att_type = att.get("type", "image")
                timeline.append(TimelineEvent(
                    timestamp=timestamp,
                    type="image_upload" if att_type == "image" else "document_upload",
                    title=f"上传{att_type}",
                    description=att.get("description", ""),
                    importance="medium"
                ))
        
        # 添加备注事件
        for note in (notes or []):
            timestamp = note.get("created_at")
            if timestamp:
                timeline.append(TimelineEvent(
                    timestamp=timestamp,
                    type="note",
                    title="用户备注",
                    description=note.get("content", ""),
                    importance="high" if note.get("is_important") else "low"
                ))
        
        # 按时间排序
        timeline.sort(key=lambda x: x.timestamp)
        
        return timeline
    
    def _format_conversations(self, sessions: List[Dict]) -> str:
        """格式化会话记录为文本"""
        if not sessions:
            return "暂无对话记录"
        
        lines = []
        for session in sessions:
            session_id = session.get("session_id", "")
            summary = session.get("summary", "")
            timestamp = session.get("timestamp", "")
            
            lines.append(f"【会话 {session_id[:8] if session_id else ''}】时间：{timestamp}")
            if summary:
                lines.append(f"摘要：{summary}")
            
            # 如果有详细消息
            messages = session.get("messages", [])
            for msg in messages[-10:]:  # 只取最近10条
                role = "患者" if msg.get("role") == "user" else "医生"
                content = msg.get("content", "")
                lines.append(f"{role}: {self._truncate_text(content, 200)}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_attachments(self, attachments: List[Dict]) -> str:
        """格式化附件信息"""
        if not attachments:
            return "无附件"
        
        lines = []
        for att in attachments:
            att_type = att.get("type", "未知")
            filename = att.get("filename", "")
            description = att.get("description", "")
            lines.append(f"- {att_type}: {filename} {description}")
        
        return "\n".join(lines)
    
    def _format_notes(self, notes: List[Dict]) -> str:
        """格式化备注"""
        if not notes:
            return "无备注"
        
        lines = []
        for note in notes:
            content = note.get("content", "")
            is_important = note.get("is_important", False)
            prefix = "⚠️ " if is_important else "- "
            lines.append(f"{prefix}{content}")
        
        return "\n".join(lines)
    
    def _get_default_summary(self) -> Dict:
        """获取默认摘要结构"""
        return {
            "summary": "暂无摘要",
            "key_points": [],
            "symptoms": [],
            "symptom_details": {},
            "possible_diagnosis": [],
            "risk_level": "low",
            "risk_warning": None,
            "recommendations": ["建议继续观察", "如症状加重请及时就医"],
            "follow_up_reminders": [],
            "timeline": [],
            "confidence": 0.5
        }
    
    def _get_fallback_summary(
        self,
        chief_complaint: str,
        department: str,
        sessions: List[Dict]
    ) -> SummaryResult:
        """获取降级摘要（AI 服务不可用时）"""
        summary_parts = []
        if chief_complaint:
            summary_parts.append(f"主诉：{chief_complaint}")
        summary_parts.append(f"科室：{department}")
        summary_parts.append(f"共 {len(sessions)} 次问诊记录")
        
        return SummaryResult(
            summary="；".join(summary_parts),
            key_points=[chief_complaint] if chief_complaint else [],
            symptoms=[],
            symptom_details={},
            possible_diagnosis=[],
            risk_level="low",
            risk_warning=None,
            recommendations=["建议继续观察", "如症状加重请及时就医"],
            follow_up_reminders=[],
            timeline=[],
            confidence=0.3
        )


# 单例
_summary_service: Optional[AISummaryService] = None


def get_summary_service() -> AISummaryService:
    """获取摘要服务单例"""
    global _summary_service
    if _summary_service is None:
        _summary_service = AISummaryService()
    return _summary_service
