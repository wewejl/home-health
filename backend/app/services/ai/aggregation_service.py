"""
智能事件聚合服务

功能：
- 分析病历事件关联性
- 自动聚合相关事件
- 生成合并建议
- 病程演变分析
"""
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .base_ai_service import BaseAIService
from .prompts.aggregation_prompts import AGGREGATION_PROMPTS


@dataclass
class RelatedEvent:
    """相关事件"""
    event_id: str
    relation_type: str  # same_condition/follow_up/complication/unrelated
    confidence: float
    reasoning: str


@dataclass
class AggregationResult:
    """聚合分析结果"""
    should_merge: bool
    confidence: float
    related_events: List[str]
    merge_reason: str
    suggested_action: str  # add_to_existing/create_new
    target_event_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MergeResult:
    """合并结果"""
    merged_title: str
    summary: str
    disease_progression: str
    key_milestones: List[Dict]
    current_status: str
    overall_risk_level: str
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventAggregationService(BaseAIService):
    """智能事件聚合服务"""
    
    # 配置参数
    TIME_WINDOW_DAYS = 7  # 时间窗口（天）
    SIMILARITY_THRESHOLD = 0.7  # 相似度阈值
    SAME_DAY_AUTO_MERGE = True  # 同天同科室自动合并
    
    def __init__(self):
        super().__init__(
            temperature=0.2,
            max_tokens=1500
        )
    
    async def analyze_relation(
        self,
        event_a: Dict,
        event_b: Dict
    ) -> Dict[str, Any]:
        """
        分析两个事件的关联性
        
        Args:
            event_a: 事件 A 信息
            event_b: 事件 B 信息
        
        Returns:
            关联分析结果
        """
        # 快速规则判断
        quick_result = self._quick_relation_check(event_a, event_b)
        if quick_result:
            return quick_result
        
        # AI 深度分析
        prompt = AGGREGATION_PROMPTS["analyze_relation"].format(
            event_a_title=event_a.get("title", ""),
            event_a_department=event_a.get("department", ""),
            event_a_complaint=event_a.get("chief_complaint", ""),
            event_a_symptoms=", ".join(event_a.get("symptoms", [])),
            event_a_time=event_a.get("start_time", ""),
            event_a_summary=event_a.get("summary", ""),
            event_b_title=event_b.get("title", ""),
            event_b_department=event_b.get("department", ""),
            event_b_complaint=event_b.get("chief_complaint", ""),
            event_b_symptoms=", ".join(event_b.get("symptoms", [])),
            event_b_time=event_b.get("start_time", ""),
            event_b_summary=event_b.get("summary", "")
        )
        
        try:
            response = await self._call_llm(
                system_prompt=AGGREGATION_PROMPTS["system"],
                user_prompt=prompt
            )
            
            result = self._parse_json(response, {
                "is_related": False,
                "relation_type": "unrelated",
                "confidence": 0.5,
                "reasoning": "无法判断",
                "should_merge": False
            })
            
            return result
            
        except Exception as e:
            print(f"关联分析失败: {e}")
            return {
                "is_related": False,
                "relation_type": "unrelated",
                "confidence": 0.3,
                "reasoning": f"分析失败: {e}",
                "should_merge": False
            }
    
    async def find_related_events(
        self,
        target_event: Dict,
        candidate_events: List[Dict]
    ) -> List[RelatedEvent]:
        """
        从候选事件中找出相关事件
        
        Args:
            target_event: 目标事件
            candidate_events: 候选事件列表
        
        Returns:
            相关事件列表
        """
        if not candidate_events:
            return []
        
        # 先用规则过滤
        filtered_candidates = self._filter_by_rules(target_event, candidate_events)
        
        if not filtered_candidates:
            return []
        
        # 格式化候选事件
        candidates_text = self._format_candidate_events(filtered_candidates)
        
        prompt = AGGREGATION_PROMPTS["find_related_events"].format(
            target_title=target_event.get("title", ""),
            target_department=target_event.get("department", ""),
            target_complaint=target_event.get("chief_complaint", ""),
            target_symptoms=", ".join(target_event.get("symptoms", [])),
            target_time=target_event.get("start_time", ""),
            candidate_events=candidates_text
        )
        
        try:
            response = await self._call_llm(
                system_prompt=AGGREGATION_PROMPTS["system"],
                user_prompt=prompt
            )
            
            result = self._parse_json(response, {"related_events": []})
            
            related = []
            for item in result.get("related_events", []):
                related.append(RelatedEvent(
                    event_id=item.get("event_id", ""),
                    relation_type=item.get("relation_type", "unrelated"),
                    confidence=item.get("confidence", 0.5),
                    reasoning=item.get("reasoning", "")
                ))
            
            return [r for r in related if r.confidence >= self.SIMILARITY_THRESHOLD]
            
        except Exception as e:
            print(f"查找相关事件失败: {e}")
            return []
    
    async def smart_aggregate(
        self,
        session_info: Dict,
        existing_events: List[Dict]
    ) -> AggregationResult:
        """
        智能聚合分析 - 判断新会话应归入哪个事件
        
        Args:
            session_info: 新会话信息
            existing_events: 现有事件列表
        
        Returns:
            聚合建议
        """
        # 快速规则匹配
        rule_result = self._rule_based_aggregate(session_info, existing_events)
        if rule_result:
            return rule_result
        
        if not existing_events:
            return AggregationResult(
                should_merge=False,
                confidence=1.0,
                related_events=[],
                merge_reason="无现有事件",
                suggested_action="create_new"
            )
        
        # 格式化现有事件
        events_text = self._format_existing_events(existing_events)
        
        prompt = AGGREGATION_PROMPTS["smart_aggregate"].format(
            session_department=session_info.get("department", ""),
            session_complaint=session_info.get("chief_complaint", ""),
            session_time=session_info.get("timestamp", ""),
            session_summary=session_info.get("summary", ""),
            existing_events=events_text
        )
        
        try:
            response = await self._call_llm(
                system_prompt=AGGREGATION_PROMPTS["system"],
                user_prompt=prompt
            )
            
            result = self._parse_json(response, {
                "action": "create_new",
                "confidence": 0.5
            })
            
            action = result.get("action", "create_new")
            target_id = result.get("target_event_id")
            
            return AggregationResult(
                should_merge=(action == "add_to_existing"),
                confidence=result.get("confidence", 0.5),
                related_events=[target_id] if target_id else [],
                merge_reason=result.get("reasoning", ""),
                suggested_action=action,
                target_event_id=target_id
            )
            
        except Exception as e:
            print(f"智能聚合失败: {e}")
            return AggregationResult(
                should_merge=False,
                confidence=0.3,
                related_events=[],
                merge_reason=f"分析失败: {e}",
                suggested_action="create_new"
            )
    
    async def generate_merged_summary(
        self,
        events: List[Dict]
    ) -> MergeResult:
        """
        生成合并后的综合摘要
        
        Args:
            events: 要合并的事件列表
        
        Returns:
            合并摘要
        """
        if not events:
            raise ValueError("事件列表不能为空")
        
        events_text = self._format_events_for_merge(events)
        
        prompt = AGGREGATION_PROMPTS["generate_merged_summary"].format(
            events=events_text
        )
        
        try:
            response = await self._call_llm(
                system_prompt=AGGREGATION_PROMPTS["system"],
                user_prompt=prompt,
                max_tokens=2000
            )
            
            result = self._parse_json(response, {
                "merged_title": "合并病历",
                "summary": "暂无摘要"
            })
            
            return MergeResult(
                merged_title=result.get("merged_title", "合并病历"),
                summary=result.get("summary", ""),
                disease_progression=result.get("disease_progression", ""),
                key_milestones=result.get("key_milestones", []),
                current_status=result.get("current_status", ""),
                overall_risk_level=result.get("overall_risk_level", "low"),
                recommendations=result.get("recommendations", [])
            )
            
        except Exception as e:
            print(f"生成合并摘要失败: {e}")
            # 降级处理
            return self._fallback_merged_summary(events)
    
    def _quick_relation_check(
        self,
        event_a: Dict,
        event_b: Dict
    ) -> Optional[Dict]:
        """快速规则判断"""
        # 同一科室
        same_dept = event_a.get("department") == event_b.get("department")
        
        # 时间差
        time_a = self._parse_time(event_a.get("start_time"))
        time_b = self._parse_time(event_b.get("start_time"))
        
        if time_a and time_b:
            time_diff = abs((time_a - time_b).days)
            
            # 同一天同科室 - 高度相关
            if same_dept and time_diff == 0:
                return {
                    "is_related": True,
                    "relation_type": "same_condition",
                    "confidence": 0.95,
                    "reasoning": "同一天同一科室的问诊，高度相关",
                    "should_merge": True
                }
            
            # 7天内同科室 - 可能相关
            if same_dept and time_diff <= self.TIME_WINDOW_DAYS:
                return None  # 需要 AI 进一步判断
            
            # 超过30天 - 不相关
            if time_diff > 30:
                return {
                    "is_related": False,
                    "relation_type": "unrelated",
                    "confidence": 0.9,
                    "reasoning": "时间间隔超过30天",
                    "should_merge": False
                }
        
        return None  # 需要 AI 判断
    
    def _rule_based_aggregate(
        self,
        session_info: Dict,
        existing_events: List[Dict]
    ) -> Optional[AggregationResult]:
        """规则引擎聚合"""
        session_dept = session_info.get("department", "")
        session_time = self._parse_time(session_info.get("timestamp"))
        
        if not session_time:
            return None
        
        # 查找同一天同科室的事件
        for event in existing_events:
            event_dept = event.get("department", "")
            event_time = self._parse_time(event.get("start_time"))
            event_status = event.get("status", "")
            
            if not event_time:
                continue
            
            # 同一天 + 同科室 + 活跃状态 → 自动合并
            if (event_dept == session_dept and 
                event_time.date() == session_time.date() and
                event_status in ["active", "ACTIVE"]):
                
                return AggregationResult(
                    should_merge=True,
                    confidence=0.95,
                    related_events=[event.get("id", "")],
                    merge_reason="同一天同一科室的问诊，自动归入现有事件",
                    suggested_action="add_to_existing",
                    target_event_id=event.get("id")
                )
        
        return None
    
    def _filter_by_rules(
        self,
        target: Dict,
        candidates: List[Dict]
    ) -> List[Dict]:
        """规则过滤候选事件"""
        target_time = self._parse_time(target.get("start_time"))
        
        filtered = []
        for event in candidates:
            # 排除自己
            if event.get("id") == target.get("id"):
                continue
            
            event_time = self._parse_time(event.get("start_time"))
            if target_time and event_time:
                time_diff = abs((target_time - event_time).days)
                # 只保留30天内的事件
                if time_diff <= 30:
                    filtered.append(event)
        
        return filtered
    
    def _format_candidate_events(self, events: List[Dict]) -> str:
        """格式化候选事件列表"""
        lines = []
        for i, event in enumerate(events, 1):
            lines.append(f"""
【事件 {i}】ID: {event.get('id', '')}
标题：{event.get('title', '')}
科室：{event.get('department', '')}
主诉：{event.get('chief_complaint', '')}
时间：{event.get('start_time', '')}
摘要：{event.get('summary', '')}
""")
        return "\n".join(lines)
    
    def _format_existing_events(self, events: List[Dict]) -> str:
        """格式化现有事件列表"""
        lines = []
        for event in events:
            lines.append(f"- ID: {event.get('id', '')}, "
                        f"科室: {event.get('department', '')}, "
                        f"时间: {event.get('start_time', '')}, "
                        f"状态: {event.get('status', '')}, "
                        f"主诉: {event.get('chief_complaint', '')}")
        return "\n".join(lines)
    
    def _format_events_for_merge(self, events: List[Dict]) -> str:
        """格式化要合并的事件"""
        lines = []
        for i, event in enumerate(events, 1):
            lines.append(f"""
【事件 {i}】
标题：{event.get('title', '')}
科室：{event.get('department', '')}
时间：{event.get('start_time', '')} - {event.get('end_time', '进行中')}
主诉：{event.get('chief_complaint', '')}
摘要：{event.get('summary', '')}
风险等级：{event.get('risk_level', 'low')}
""")
        return "\n".join(lines)
    
    def _parse_time(self, time_str: Any) -> Optional[datetime]:
        """解析时间字符串"""
        if isinstance(time_str, datetime):
            return time_str
        
        if not time_str:
            return None
        
        try:
            if "T" in str(time_str):
                return datetime.fromisoformat(str(time_str).replace("Z", "+00:00"))
            return datetime.strptime(str(time_str), "%Y-%m-%d %H:%M:%S")
        except:
            return None
    
    def _fallback_merged_summary(self, events: List[Dict]) -> MergeResult:
        """降级合并摘要"""
        titles = [e.get("title", "") for e in events if e.get("title")]
        departments = list(set(e.get("department", "") for e in events if e.get("department")))
        
        return MergeResult(
            merged_title=titles[0] if titles else "合并病历",
            summary=f"包含 {len(events)} 个相关病历事件",
            disease_progression="",
            key_milestones=[],
            current_status="需要进一步分析",
            overall_risk_level="medium",
            recommendations=["建议详细查看各事件记录", "如症状持续请及时就医"]
        )


# 单例
_aggregation_service: Optional[EventAggregationService] = None


def get_aggregation_service() -> EventAggregationService:
    """获取聚合服务单例"""
    global _aggregation_service
    if _aggregation_service is None:
        _aggregation_service = EventAggregationService()
    return _aggregation_service
