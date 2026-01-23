"""
医嘱管理服务

包含：
- 医嘱 CRUD 操作
- 医嘱激活（生成任务实例）
- 任务生成逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.medical_order import (
    MedicalOrder, TaskInstance, OrderType, ScheduleType,
    OrderStatus, TaskStatus, CompletionRecord
)
from ..models.user import User


class MedicalOrderService:
    """医嘱管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_draft_order(self, data: Dict[str, Any]) -> MedicalOrder:
        """
        创建草稿医嘱

        通常由 AI 从问诊对话中自动生成，或由医生手动创建
        """
        order = MedicalOrder(
            patient_id=data["patient_id"],
            doctor_id=data.get("doctor_id"),
            order_type=data["order_type"],
            title=data["title"],
            description=data.get("description"),
            schedule_type=data["schedule_type"],
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            frequency=data.get("frequency"),
            reminder_times=data.get("reminder_times", []),
            ai_generated=data.get("ai_generated", False),
            ai_session_id=data.get("ai_session_id"),
            status=OrderStatus.DRAFT
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def activate_order(self, order_id: int) -> MedicalOrder:
        """
        激活医嘱（医生审核通过）

        激活后开始生成每日任务实例
        """
        order = self.db.query(MedicalOrder).filter(
            MedicalOrder.id == order_id
        ).first()

        if not order:
            raise ValueError(f"医嘱不存在: {order_id}")

        if order.status != OrderStatus.DRAFT:
            raise ValueError(f"只有草稿状态的医嘱可以激活")

        order.status = OrderStatus.ACTIVE

        # 生成初始任务实例
        self._generate_task_instances(order)

        self.db.commit()
        self.db.refresh(order)

        return order

    def _generate_task_instances(self, order: MedicalOrder) -> List[TaskInstance]:
        """
        为医嘱生成任务实例

        根据调度类型和提醒时间生成任务
        """
        instances = []

        if order.schedule_type == ScheduleType.ONCE:
            # 一次性任务
            instance = TaskInstance(
                order_id=order.id,
                patient_id=order.patient_id,
                scheduled_date=order.start_date,
                scheduled_time=self._parse_time(order.reminder_times[0]) if order.reminder_times else time(9, 0),
                status=TaskStatus.PENDING
            )
            instances.append(instance)

        elif order.schedule_type == ScheduleType.DAILY:
            # 每日任务 - 生成未来7天的任务
            for days_ahead in range(7):
                task_date = order.start_date + timedelta(days=days_ahead)

                # 如果有结束日期，不超过结束日期
                if order.end_date and task_date > order.end_date:
                    break

                # 为每个提醒时间创建任务
                for reminder in order.reminder_times:
                    instance = TaskInstance(
                        order_id=order.id,
                        patient_id=order.patient_id,
                        scheduled_date=task_date,
                        scheduled_time=self._parse_time(reminder),
                        status=TaskStatus.PENDING
                    )
                    instances.append(instance)

        # 批量添加
        self.db.add_all(instances)
        self.db.commit()

        return instances

    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串 HH:MM"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return time(9, 0)  # 默认9点

    def get_patient_orders(
        self,
        patient_id: int,
        status: Optional[OrderStatus] = None,
        active_date: Optional[date] = None
    ) -> List[MedicalOrder]:
        """
        获取患者的医嘱列表

        active_date: 如果指定，只返回该日期有效的医嘱
        """
        query = self.db.query(MedicalOrder).filter(
            MedicalOrder.patient_id == patient_id
        )

        if status:
            query = query.filter(MedicalOrder.status == status)

        # 筛选指定日期有效的医嘱
        if active_date:
            query = query.filter(
                and_(
                    MedicalOrder.start_date <= active_date,
                    MedicalOrder.end_date >= active_date if MedicalOrder.end_date is not None else True
                )
            )

        return query.order_by(MedicalOrder.created_at.desc()).all()

    def get_patient_tasks(
        self,
        patient_id: int,
        task_date: date,
        status: Optional[TaskStatus] = None
    ) -> List[TaskInstance]:
        """
        获取患者指定日期的任务列表
        """
        query = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == task_date
        )

        if status:
            query = query.filter(TaskInstance.status == status)

        return query.order_by(TaskInstance.scheduled_time).all()
