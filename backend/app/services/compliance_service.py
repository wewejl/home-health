"""
依从性计算服务

负责：
- 计算患者日/周/医嘱周期依从性
- 生成依从性报告数据
"""
from typing import Dict, List
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.medical_order import TaskInstance, TaskStatus


class ComplianceService:
    """依从性计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_daily_compliance(self, patient_id: int, target_date: date) -> Dict:
        """
        计算指定日期的依从性

        返回:
        {
            "total": 总任务数,
            "completed": 完成数,
            "overdue": 超时数,
            "pending": 待完成数,
            "rate": 依从率 (0-1)
        }
        """
        # 查询当日所有任务
        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date == target_date
        ).all()

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)

        rate = completed / total if total > 0 else 0

        return {
            "date": target_date.isoformat(),
            "total": total,
            "completed": completed,
            "overdue": overdue,
            "pending": pending,
            "rate": round(rate, 2)
        }

    def calculate_weekly_compliance(self, patient_id: int) -> Dict:
        """
        计算近7天的依从性趋势

        返回:
        {
            "daily_rates": [日依从率列表],
            "average_rate": 平均依从率,
            "dates": [日期列表]
        }
        """
        today = date.today()
        daily_rates = []
        dates = []

        for i in range(6, -1, -1):  # 从6天前到今天
            target_date = today - timedelta(days=i)
            compliance = self.calculate_daily_compliance(patient_id, target_date)
            daily_rates.append(compliance["rate"])
            dates.append(target_date.isoformat())

        average_rate = sum(daily_rates) / len(daily_rates) if daily_rates else 0

        return {
            "daily_rates": daily_rates,
            "average_rate": round(average_rate, 2),
            "dates": dates
        }

    def calculate_order_compliance(self, order_id: int) -> Dict:
        """
        计算整个医嘱周期的依从性

        返回:
        {
            "order_id": 医嘱ID,
            "total": 总任务数,
            "completed": 完成数,
            "rate": 依从率,
            "start_date": 开始日期,
            "end_date": 结束日期
        }
        """
        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.order_id == order_id
        ).all()

        if not tasks:
            return {
                "order_id": order_id,
                "total": 0,
                "completed": 0,
                "rate": 0,
                "start_date": None,
                "end_date": None
            }

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        rate = completed / total if total > 0 else 0

        # 获取日期范围
        dates = [t.scheduled_date for t in tasks]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None

        return {
            "order_id": order_id,
            "total": total,
            "completed": completed,
            "rate": round(rate, 2),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

    def get_abnormal_records(
        self,
        patient_id: int,
        days: int = 30
    ) -> List[Dict]:
        """
        获取异常记录（超时未完成的任务）

        返回最近N天的异常记录
        """
        since_date = date.today() - timedelta(days=days)

        tasks = self.db.query(TaskInstance).filter(
            TaskInstance.patient_id == patient_id,
            TaskInstance.scheduled_date >= since_date,
            TaskInstance.status == TaskStatus.OVERDUE
        ).order_by(TaskInstance.scheduled_date.desc()).all()

        return [
            {
                "task_id": t.id,
                "date": t.scheduled_date.isoformat(),
                "time": t.scheduled_time.strftime("%H:%M"),
                "order_title": t.order.title if t.order else "未知医嘱"
            }
            for t in tasks
        ]
