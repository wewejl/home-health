"""
任务调度服务

负责：
- 每日定时生成任务实例
- 检测超时任务
- 标记过期待完成的任务
"""
from typing import List
from datetime import date, datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.medical_order import MedicalOrder, TaskInstance, OrderStatus, TaskStatus


class TaskScheduler:
    """任务调度器"""

    def __init__(self, db: Session):
        self.db = db

    def generate_daily_tasks(self, order_id: int, target_date: date) -> List[TaskInstance]:
        """
        为指定医嘱生成指定日期的任务实例

        通常由定时任务每晚调用，生成第二天的任务
        """
        order = self.db.query(MedicalOrder).filter(
            MedicalOrder.id == order_id
        ).first()

        if not order:
            raise ValueError(f"医嘱不存在: {order_id}")

        if order.status != OrderStatus.ACTIVE:
            return []

        # 检查是否在有效期内
        if target_date < order.start_date:
            return []
        if order.end_date and target_date > order.end_date:
            return []

        # 检查是否已生成
        existing = self.db.query(TaskInstance).filter(
            TaskInstance.order_id == order_id,
            TaskInstance.scheduled_date == target_date
        ).first()

        if existing:
            return []  # 已生成

        instances = []
        reminder_times = order.reminder_times or ["09:00"]

        for reminder in reminder_times:
            instance = TaskInstance(
                order_id=order.id,
                patient_id=order.patient_id,
                scheduled_date=target_date,
                scheduled_time=self._parse_time(reminder),
                status=TaskStatus.PENDING
            )
            instances.append(instance)

        self.db.add_all(instances)
        self.db.commit()

        return instances

    def mark_overdue_tasks(self) -> int:
        """
        标记超时未完成的任务

        应该每分钟或每小时运行一次
        """
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()

        # 查找所有应该已完成但未完成的任务
        overdue_tasks = self.db.query(TaskInstance).filter(
            TaskInstance.status == TaskStatus.PENDING,
            TaskInstance.scheduled_date < current_date
        ).all()

        # 加上当天的超时任务
        today_overdue = self.db.query(TaskInstance).filter(
            TaskInstance.status == TaskStatus.PENDING,
            TaskInstance.scheduled_date == current_date,
            TaskInstance.scheduled_time < current_time
        ).all()

        all_overdue = overdue_tasks + today_overdue

        for task in all_overdue:
            task.status = TaskStatus.OVERDUE

        self.db.commit()

        return len(all_overdue)

    def generate_all_active_orders_tasks(self, target_date: date) -> int:
        """
        为所有活跃医嘱生成指定日期的任务

        由定时任务调用
        """
        active_orders = self.db.query(MedicalOrder).filter(
            MedicalOrder.status == OrderStatus.ACTIVE
        ).all()

        total_instances = 0
        for order in active_orders:
            instances = self.generate_daily_tasks(order.id, target_date)
            total_instances += len(instances)

        return total_instances

    def _parse_time(self, time_str: str) -> time:
        """解析时间字符串"""
        try:
            hour, minute = map(int, time_str.split(":"))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return time(9, 0)
