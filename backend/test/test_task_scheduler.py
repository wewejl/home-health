"""
TaskScheduler 单元测试

测试任务调度器的所有方法：
- 任务生成
- 任务调度
- 状态更新
- 过期任务标记
"""
import pytest
from datetime import date, datetime, time, timedelta
from sqlalchemy.orm import Session

# 导入 TaskScheduler 和相关模型
try:
    from app.services.task_scheduler import TaskScheduler
    from app.models.medical_order import (
        MedicalOrder,
        TaskInstance,
        OrderStatus,
        TaskStatus,
        OrderType,
        ScheduleType
    )
    from app.models.user import User
except ImportError:
    from backend.app.services.task_scheduler import TaskScheduler
    from backend.app.models.medical_order import (
        MedicalOrder,
        TaskInstance,
        OrderStatus,
        TaskStatus,
        OrderType,
        ScheduleType
    )
    from backend.app.models.user import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_patient(db_session: Session) -> User:
    """创建测试患者"""
    patient = User(
        phone="13800138000",
        nickname="测试患者",
        is_profile_completed=True,
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def active_medical_order(db_session: Session, test_patient: User) -> MedicalOrder:
    """创建活跃的医嘱"""
    order = MedicalOrder(
        patient_id=test_patient.id,
        doctor_id=None,
        order_type=OrderType.MEDICATION,
        title="测试用药医嘱",
        description="每日服用药物",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        reminder_times=["08:00", "12:00", "18:00"],
        status=OrderStatus.ACTIVE
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def draft_medical_order(db_session: Session, test_patient: User) -> MedicalOrder:
    """创建草稿状态的医嘱"""
    order = MedicalOrder(
        patient_id=test_patient.id,
        order_type=OrderType.MEDICATION,
        title="草稿医嘱",
        schedule_type=ScheduleType.DAILY,
        start_date=date.today(),
        status=OrderStatus.DRAFT
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def task_scheduler(db_session: Session) -> TaskScheduler:
    """创建任务调度器实例"""
    return TaskScheduler(db_session)


# ============================================================================
# 任务生成测试
# ============================================================================

class TestGenerateDailyTasks:
    """测试每日任务生成"""

    def test_generate_daily_tasks_success(self, task_scheduler: TaskScheduler, active_medical_order: MedicalOrder):
        """测试成功生成每日任务"""
        target_date = date.today()

        instances = task_scheduler.generate_daily_tasks(active_medical_order.id, target_date)

        # 应该生成3个任务（对应3个提醒时间）
        assert len(instances) == 3

        # 验证任务属性
        for instance in instances:
            assert instance.order_id == active_medical_order.id
            assert instance.patient_id == active_medical_order.patient_id
            assert instance.scheduled_date == target_date
            assert instance.status == TaskStatus.PENDING
            assert instance.scheduled_time in [
                time(8, 0),
                time(12, 0),
                time(18, 0)
            ]

    def test_generate_daily_tasks_no_reminder_times(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试没有提醒时间的医嘱生成任务"""
        # 创建没有提醒时间的医嘱
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MONITORING,
            title="监测医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=None,
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        target_date = date.today()
        instances = task_scheduler.generate_daily_tasks(order.id, target_date)

        # 应该生成1个默认任务
        assert len(instances) == 1
        assert instances[0].scheduled_time == time(9, 0)  # 默认时间

    def test_generate_daily_tasks_order_not_found(self, task_scheduler: TaskScheduler):
        """测试医嘱不存在"""
        with pytest.raises(ValueError, match="医嘱不存在"):
            task_scheduler.generate_daily_tasks(99999, date.today())

    def test_generate_daily_tasks_draft_order(self, task_scheduler: TaskScheduler, draft_medical_order: MedicalOrder):
        """测试草稿状态医嘱不生成任务"""
        target_date = date.today()

        instances = task_scheduler.generate_daily_tasks(draft_medical_order.id, target_date)

        # 草稿医嘱不应该生成任务
        assert len(instances) == 0

    def test_generate_daily_tasks_stopped_order(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试已停用医嘱不生成任务"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="已停用医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            status=OrderStatus.STOPPED
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        target_date = date.today()
        instances = task_scheduler.generate_daily_tasks(order.id, target_date)

        assert len(instances) == 0

    def test_generate_daily_tasks_before_start_date(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试目标日期在开始日期之前"""
        tomorrow = date.today() + timedelta(days=1)
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="未来医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=tomorrow,
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 今天在开始日期之前，不应该生成任务
        instances = task_scheduler.generate_daily_tasks(order.id, date.today())
        assert len(instances) == 0

    def test_generate_daily_tasks_after_end_date(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试目标日期在结束日期之后"""
        yesterday = date.today() - timedelta(days=1)
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="过期医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today() - timedelta(days=7),
            end_date=yesterday,
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 今天在结束日期之后，不应该生成任务
        instances = task_scheduler.generate_daily_tasks(order.id, date.today())
        assert len(instances) == 0

    def test_generate_daily_tasks_already_exists(self, db_session: Session, active_medical_order: MedicalOrder, task_scheduler: TaskScheduler):
        """测试已存在的任务不再重复生成"""
        target_date = date.today()

        # 第一次生成
        instances1 = task_scheduler.generate_daily_tasks(active_medical_order.id, target_date)
        assert len(instances1) == 3

        # 第二次生成（应该返回空，因为已存在）
        instances2 = task_scheduler.generate_daily_tasks(active_medical_order.id, target_date)
        assert len(instances2) == 0

        # 验证数据库中只有3个任务
        count = db_session.query(TaskInstance).filter(
            TaskInstance.order_id == active_medical_order.id,
            TaskInstance.scheduled_date == target_date
        ).count()
        assert count == 3

    def test_generate_daily_tasks_custom_reminder_times(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试自定义提醒时间"""
        custom_times = ["06:30", "13:45", "22:15"]
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="自定义时间医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=custom_times,
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        target_date = date.today()
        instances = task_scheduler.generate_daily_tasks(order.id, target_date)

        assert len(instances) == 3
        scheduled_times = {inst.scheduled_time for inst in instances}
        assert scheduled_times == {
            time(6, 30),
            time(13, 45),
            time(22, 15)
        }


class TestGenerateAllActiveOrdersTasks:
    """测试为所有活跃医嘱生成任务"""

    def test_generate_all_active_orders_tasks(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试为多个活跃医嘱生成任务"""
        # 创建多个活跃医嘱
        order1 = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="医嘱1",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        order2 = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MONITORING,
            title="医嘱2",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["12:00", "18:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add_all([order1, order2])
        db_session.commit()

        target_date = date.today()
        total_instances = task_scheduler.generate_all_active_orders_tasks(target_date)

        # order1 生成1个任务，order2 生成2个任务
        assert total_instances == 3

    def test_generate_all_active_orders_tasks_with_draft(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试混合活跃和草稿医嘱"""
        active_order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="活跃医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        draft_order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="草稿医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["09:00"],
            status=OrderStatus.DRAFT
        )
        db_session.add_all([active_order, draft_order])
        db_session.commit()

        target_date = date.today()
        total_instances = task_scheduler.generate_all_active_orders_tasks(target_date)

        # 只有活跃医嘱生成任务
        assert total_instances == 1


# ============================================================================
# 过期任务标记测试
# ============================================================================

class TestMarkOverdueTasks:
    """测试过期任务标记"""

    def test_mark_overdue_tasks_past_date(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试标记过去日期的任务为过期"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 创建一个过去日期的待完成任务
        past_date = date.today() - timedelta(days=1)
        task = TaskInstance(
            order_id=order.id,
            patient_id=test_patient.id,
            scheduled_date=past_date,
            scheduled_time=time(8, 0),
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        # 标记过期任务
        overdue_count = task_scheduler.mark_overdue_tasks()

        assert overdue_count == 1
        db_session.refresh(task)
        assert task.status == TaskStatus.OVERDUE

    def test_mark_overdue_tasks_today_past_time(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试标记今天已过时间的任务为过期"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["00:01"],  # 凌晨，肯定已过期
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 创建一个今天的待完成任务（时间已过）
        task = TaskInstance(
            order_id=order.id,
            patient_id=test_patient.id,
            scheduled_date=date.today(),
            scheduled_time=time(0, 1),
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        # 标记过期任务
        overdue_count = task_scheduler.mark_overdue_tasks()

        assert overdue_count >= 1
        db_session.refresh(task)
        assert task.status == TaskStatus.OVERDUE

    def test_mark_overdue_tasks_future_time(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试未来时间的任务不被标记为过期"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["23:59"],  # 很晚的时间
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 创建一个未来的待完成任务
        task = TaskInstance(
            order_id=order.id,
            patient_id=test_patient.id,
            scheduled_date=date.today(),
            scheduled_time=time(23, 59),
            status=TaskStatus.PENDING
        )
        db_session.add(task)
        db_session.commit()

        # 标记过期任务
        overdue_count = task_scheduler.mark_overdue_tasks()

        # 这个任务不应该被标记
        db_session.refresh(task)
        assert task.status == TaskStatus.PENDING

    def test_mark_overdue_tasks_completed_not_affected(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试已完成的任务不受影响"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 创建一个已完成的任务
        task = TaskInstance(
            order_id=order.id,
            patient_id=test_patient.id,
            scheduled_date=date.today() - timedelta(days=1),
            scheduled_time=time(8, 0),
            status=TaskStatus.COMPLETED
        )
        db_session.add(task)
        db_session.commit()

        # 标记过期任务
        overdue_count = task_scheduler.mark_overdue_tasks()

        # 已完成的任务不应该被计数
        assert overdue_count == 0
        db_session.refresh(task)
        assert task.status == TaskStatus.COMPLETED

    def test_mark_overdue_tasks_multiple_tasks(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试标记多个过期任务"""
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="测试医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            reminder_times=["08:00", "12:00", "18:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 创建多个过去日期的待完成任务
        past_date = date.today() - timedelta(days=1)
        for reminder_time in ["08:00", "12:00", "18:00"]:
            hour, minute = map(int, reminder_time.split(":"))
            task = TaskInstance(
                order_id=order.id,
                patient_id=test_patient.id,
                scheduled_date=past_date,
                scheduled_time=time(hour, minute),
                status=TaskStatus.PENDING
            )
            db_session.add(task)
        db_session.commit()

        # 标记过期任务
        overdue_count = task_scheduler.mark_overdue_tasks()

        assert overdue_count == 3

    def test_mark_overdue_tasks_empty_database(self, db_session: Session, task_scheduler: TaskScheduler):
        """测试空数据库"""
        overdue_count = task_scheduler.mark_overdue_tasks()
        assert overdue_count == 0


# ============================================================================
# 时间解析测试
# ============================================================================

class TestParseTime:
    """测试时间解析"""

    def test_parse_time_valid(self, task_scheduler: TaskScheduler):
        """测试解析有效时间"""
        result = task_scheduler._parse_time("08:30")
        assert result == time(8, 30)

    def test_parse_time_midnight(self, task_scheduler: TaskScheduler):
        """测试解析午夜时间"""
        result = task_scheduler._parse_time("00:00")
        assert result == time(0, 0)

    def test_parse_time_end_of_day(self, task_scheduler: TaskScheduler):
        """测试解析一天结束时间"""
        result = task_scheduler._parse_time("23:59")
        assert result == time(23, 59)

    def test_parse_time_invalid_format(self, task_scheduler: TaskScheduler):
        """测试解析无效格式"""
        result = task_scheduler._parse_time("invalid")
        assert result == time(9, 0)  # 默认值

    def test_parse_time_empty_string(self, task_scheduler: TaskScheduler):
        """测试解析空字符串"""
        result = task_scheduler._parse_time("")
        assert result == time(9, 0)  # 默认值

    def test_parse_time_none(self, task_scheduler: TaskScheduler):
        """测试解析 None"""
        result = task_scheduler._parse_time(None)
        assert result == time(9, 0)  # 默认值


# ============================================================================
# 边界条件测试
# ============================================================================

class TestEdgeCases:
    """测试边界条件"""

    def test_generate_tasks_for_no_end_date(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试没有结束日期的医嘱"""
        far_future = date.today() + timedelta(days=100)
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="长期医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today(),
            end_date=None,  # 没有结束日期
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # 为远期日期生成任务应该成功
        instances = task_scheduler.generate_daily_tasks(order.id, far_future)
        assert len(instances) == 1

    def test_generate_tasks_start_date_equals_target(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试目标日期等于开始日期"""
        target_date = date.today()
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="今天开始的医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=target_date,
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        instances = task_scheduler.generate_daily_tasks(order.id, target_date)
        assert len(instances) == 1

    def test_generate_tasks_end_date_equals_target(self, db_session: Session, test_patient: User, task_scheduler: TaskScheduler):
        """测试目标日期等于结束日期"""
        target_date = date.today()
        order = MedicalOrder(
            patient_id=test_patient.id,
            order_type=OrderType.MEDICATION,
            title="今天结束的医嘱",
            schedule_type=ScheduleType.DAILY,
            start_date=date.today() - timedelta(days=7),
            end_date=target_date,
            reminder_times=["08:00"],
            status=OrderStatus.ACTIVE
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        instances = task_scheduler.generate_daily_tasks(order.id, target_date)
        assert len(instances) == 1
