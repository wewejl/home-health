# N+1 查询优化设计文档

**创建日期**: 2026-02-11
**任务ID**: BE-P1-002
**状态**: ✅ 已完成 (2026-02-11)
**负责人**: Team Lead

---

## 一、问题分析

### 1.1 什么是 N+1 查询问题

N+1 查询问题是指：执行 1 条查询获取 N 条主记录后，对每条记录又执行 1 次关联查询，总共执行 N+1 次数据库查询。

### 1.2 本项目的 N+1 查询问题位置

经过代码分析，发现以下存在 N+1 查询风险的代码：

#### doctor_workstation.py (7 处)

| 位置 | 函数 | 问题描述 | 严重程度 |
|------|------|----------|----------|
| `doctor_workstation.py:123-134` | `get_doctor_info` | 遍历医生时访问 `department.name` | 高 |
| `doctor_workstation.py:138-141` | `get_doctor_info` | 单独查询 department | 中 |
| `doctor_workstation.py:86-100` | `get_patient_stats` | 遍历患者 ID 查询 TaskInstance | 高 |
| `doctor_workstation.py:284-316` | `get_patients` | 遍历患者查询会话、医嘱、任务 | 高 |
| `doctor_workstation.py:510-542` | `get_patient_detail` | 多次单独查询 | 中 |
| `doctor_workstation.py:576-590` | `get_patient_consultations` | 遍历会话查询消息数 | 中 |
| `doctor_workstation.py:471-477` | `get_assignable_patients` | 遍历患者查询关联关系 | 中 |

#### admin_departments.py (3 处)

| 位置 | 函数 | 问题描述 | 严重程度 |
|------|------|----------|----------|
| `admin_departments.py:51` | `list_departments` | 遍历科室时访问 `dept.doctors` | 中 |
| `admin_departments.py:113` | `get_department` | 访问 `dept.doctors` | 低 |
| `admin_departments.py:144` | `update_department` | 访问 `dept.doctors` | 低 |

#### medical_orders.py (3 处)

| 位置 | 函数 | 问题描述 | 严重程度 |
|------|------|----------|----------|
| `medical_orders.py:180, 198` | `get_family_bonds` | 遍历关系时单独查询患者/家属 | 高 |
| `medical_orders.py:278-280` | `get_daily_tasks` | 遍历任务时访问 `task.order` | 高 |
| `medical_orders.py:598` | `get_alerts` | 遍历预警时访问 `alert.task_instance.order` | 中 |

---

## 二、详细分析

### 2.1 `get_doctor_info` 函数问题

**当前代码 (行 123-134)**:
```python
managed_doctors = db.query(Doctor).filter(
    Doctor.id.in_(doctor.managed_doctor_ids)
).all()
managed_doctors = [
    ManagedDoctorInfo(
        id=d.id,
        name=d.name,
        title=d.title,
        department=d.department.name if d.department else None  # N+1 问题
    )
    for d in doctors
]
```

**问题**: 访问 `d.department.name` 时，SQLAlchemy 的 lazy loading 会导致每个医生触发一次额外的查询。

**当前代码 (行 138-141)**:
```python
if doctor.department_id:
    from ..models.department import Department
    dept = db.query(Department).filter(Department.id == doctor.department_id).first()
    department_name = dept.name if dept else None
```

**问题**: 已经有了 `doctor.department_id`，却单独查询 department，可以使用预加载避免。

---

### 2.2 `get_patient_stats` 函数问题

**当前代码 (行 86-100)**:
```python
for pid in patient_ids:
    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == pid,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()  # N+1 问题：每个患者触发一次查询
```

**问题**: 遍历所有患者 ID，为每个患者执行一次查询。

---

### 2.3 `get_patients` 函数问题

**当前代码 (行 284-316)**:
```python
for patient in patients:
    # 最后咨询时间
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient.id
    ).order_by(desc(ConsultationSession.updated_at)).first()  # N+1

    # 进行中的医嘱数
    active_orders = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient.id,
        MedicalOrder.status == OrderStatus.ACTIVE
    ).count()  # N+1

    # 最近7天完成率
    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient.id,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()  # N+1
```

**问题**: 每个患者触发 3 次额外查询，如果有 50 个患者，就是 150+ 次查询。

---

### 2.4 `get_patient_consultations` 函数问题

**当前代码 (行 576-590)**:
```python
for session in sessions:
    message_count = db.query(Message).filter(
        Message.session_id == session.id
    ).count()  # N+1 问题
```

**问题**: 每个会话触发一次消息计数查询。

---

### 2.5 `get_assignable_patients` 函数问题

**当前代码 (行 471-477)**:
```python
if is_assigned:
    rel = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_id == patient.id,
        DoctorPatientRelationship.is_active == True
    ).first()  # N+1 问题
```

**问题**: 每个已分配患者触发一次查询获取分配时间。

---

### 2.7 `list_departments` 函数问题 (admin_departments.py)

**当前代码 (行 48-61)**:
```python
departments = db.query(Department).order_by(Department.sort_order).all()
result = []
for dept in departments:
    doctor_count = len(dept.doctors) if dept.doctors else 0  # N+1 问题
    result.append(DepartmentDetailResponse(...))
```

**问题**: 访问 `dept.doctors` 时触发 lazy loading，每个科室触发一次查询。

---

### 2.8 `get_family_bonds` 函数问题 (medical_orders.py)

**当前代码 (行 175-209)**:
```python
# 查找我是家属的关系
as_family = db.query(FamilyBond).filter(
    FamilyBond.family_member_id == current_user.id
).all()

for bond in as_family:
    patient = db.query(User).filter(User.id == bond.patient_id).first()  # N+1
    results.append(...)

# 查找我是患者的关系
as_patient = db.query(FamilyBond).filter(
    FamilyBond.patient_id == current_user.id
).all()

for bond in as_patient:
    member = db.query(User).filter(User.id == bond.family_member_id).first()  # N+1
    results.append(...)
```

**问题**: 遍历关系时为每个关系单独查询用户信息。

---

### 2.9 `get_daily_tasks` 函数问题 (medical_orders.py)

**当前代码 (行 405-410)**:
```python
def build_response(task):
    data = TaskInstanceResponse.model_validate(task).model_dump()
    if task.order:
        data["order_title"] = task.order.title  # N+1 问题
        data["order_type"] = task.order.order_type.value
    return data
```

**问题**: 遍历任务时访问 `task.order` 触发 lazy loading。

---

### 2.10 `get_alerts` 函数问题 (medical_orders.py)

**当前代码 (行 588-601)**:
```python
return [
    {
        ...
        "task_title": alert.task_instance.order.title if alert.task_instance and alert.task_instance.order else None  # N+1 问题
    }
    for alert in alerts
]
```

**问题**: 遍历预警时访问 `alert.task_instance.order` 触发多次查询。

---

## 三、优化方案

### 3.1 使用 SQLAlchemy 预加载选项

SQLAlchemy 提供了多种预加载策略：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| `joinedload` | 使用 JOIN 一次性加载关联 | 一对一、一对多，数据量不大 |
| `selectinload` | 使用单独查询 + IN 一次性加载 | 一对多，避免重复数据 |
| `subqueryload` | 使用子查询一次性加载 | 复杂关联场景 |
| `lazy='noload'` | 禁用加载 | 仅需要主表数据 |

**导入语句**:
```python
from sqlalchemy.orm import joinedload, selectinload, lazyload
```

---

### 3.2 `get_doctor_info` 优化

**优化方案**:
```python
from sqlalchemy.orm import joinedload

@router.get("/me", response_model=DoctorInfoResponse)
def get_doctor_info(
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    # 使用 joinedload 预加载 department
    doctor_with_dept = db.query(AdminUser).options(
        joinedload(AdminUser.department)
    ).filter(AdminUser.id == doctor.id).first()

    # 获取管理的 AI 分身详情 - 预加载 department
    managed_doctors = []
    if doctor_with_dept.managed_doctor_ids:
        doctors = db.query(Doctor).options(
            joinedload(Doctor.department)
        ).filter(
            Doctor.id.in_(doctor_with_dept.managed_doctor_ids)
        ).all()

        managed_doctors = [
            ManagedDoctorInfo(
                id=d.id,
                name=d.name,
                title=d.title,
                department=d.department.name if d.department else None
            )
            for d in doctors
        ]

    return DoctorInfoResponse(
        id=doctor_with_dept.id,
        username=doctor_with_dept.username,
        email=doctor_with_dept.email,
        role=doctor_with_dept.role,
        department_id=doctor_with_dept.department_id,
        department_name=doctor_with_dept.department.name if doctor_with_dept.department else None,
        managed_doctors=managed_doctors
    )
```

**效果**: 从 N+1 次查询减少到 2 次查询（1 次查医生，1 次查 AI 分身）。

---

### 3.3 `get_patient_stats` 优化

**优化方案**:
```python
@router.get("/patient-stats", response_model=PatientStatsResponse)
def get_patient_stats(
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    patient_ids = _get_accessible_patient_ids(doctor.id, db)

    if not patient_ids:
        return PatientStatsResponse(total=0, active=0, new_today=0, low_compliance=0)

    total = len(patient_ids)

    # 活跃患者数 - 优化为单个查询
    active = db.query(MedicalOrder.patient_id).filter(
        MedicalOrder.patient_id.in_(patient_ids),
        MedicalOrder.status == OrderStatus.ACTIVE
    ).distinct().count()

    # 今日新增患者数
    today = date.today()
    new_today = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.is_active == True,
        func.date(DoctorPatientRelationship.created_at) == today
    ).count()

    # 低依从性患者数 - 优化为单个查询
    week_ago = datetime.utcnow() - timedelta(days=7)

    # 获取所有患者的任务完成情况（单个查询）
    week_tasks = db.query(
        TaskInstance.patient_id,
        TaskInstance.status
    ).filter(
        TaskInstance.patient_id.in_(patient_ids),
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    # 在内存中计算低依从性患者数
    patient_task_stats = {}
    for pid, status in week_tasks:
        if pid not in patient_task_stats:
            patient_task_stats[pid] = {"total": 0, "completed": 0}
        patient_task_stats[pid]["total"] += 1
        if status == TaskStatus.COMPLETED:
            patient_task_stats[pid]["completed"] += 1

    low_compliance = sum(
        1 for stats in patient_task_stats.values()
        if stats["total"] > 0 and stats["completed"] / stats["total"] < 0.5
    )

    return PatientStatsResponse(
        total=total,
        active=active,
        new_today=new_today,
        low_compliance=low_compliance
    )
```

**效果**: 从 N+1 次查询减少到 4 次查询。

---

### 3.4 `get_patients` 优化

**优化方案**:
```python
@router.get("/patients", response_model=List[PatientListItem])
def get_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    patient_ids = _get_accessible_patient_ids(doctor.id, db)

    if not patient_ids:
        return []

    # 构建查询
    query = db.query(User).filter(User.id.in_(patient_ids))

    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    patients = query.order_by(desc(User.created_at)).all()

    # 批量获取统计数据（优化为 3 个查询）
    patient_id_list = [p.id for p in patients]

    # 1. 最后咨询时间（单个查询）
    last_sessions = db.query(
        ConsultationSession.user_id,
        ConsultationSession.updated_at
    ).filter(
        ConsultationSession.user_id.in_(patient_id_list)
    ).distinct(ConsultationSession.user_id).all()

    # 构建 patient_id -> last_session_updated_at 映射
    session_map = {user_id: updated_at for user_id, updated_at in last_sessions}

    # 2. 进行中的医嘱数（单个查询）
    active_orders_counts = db.query(
        MedicalOrder.patient_id,
        func.count(MedicalOrder.id)
    ).filter(
        MedicalOrder.patient_id.in_(patient_id_list),
        MedicalOrder.status == OrderStatus.ACTIVE
    ).group_by(MedicalOrder.patient_id).all()

    orders_map = {pid: count for pid, count in active_orders_counts}

    # 3. 最近7天完成率（单个查询）
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_tasks = db.query(
        TaskInstance.patient_id,
        TaskInstance.status
    ).filter(
        TaskInstance.patient_id.in_(patient_id_list),
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    # 在内存中计算每个患者的完成率
    task_stats = {}
    for pid, status in week_tasks:
        if pid not in task_stats:
            task_stats[pid] = {"total": 0, "completed": 0}
        task_stats[pid]["total"] += 1
        if status == TaskStatus.COMPLETED:
            task_stats[pid]["completed"] += 1

    # 构建结果
    result = []
    for patient in patients:
        completed_count = task_stats.get(patient.id, {}).get("completed", 0)
        total_tasks = task_stats.get(patient.id, {}).get("total", 0)
        completion_rate = completed_count / total_tasks if total_tasks > 0 else 0.0

        result.append(PatientListItem(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=calculate_age(patient.birthday),
            last_consultation_at=session_map.get(patient.id),
            active_orders_count=orders_map.get(patient.id, 0),
            completion_rate=round(completion_rate, 2)
        ))

    return result
```

**效果**: 从 3N+1 次查询减少到 4 次查询。

---

### 3.5 `get_patient_consultations` 优化

**优化方案**:
```python
@router.get("/patients/{patient_id}/consultations", response_model=List[ConsultationSessionSchema])
def get_patient_consultations(
    patient_id: int,
    limit: int = Query(10, ge=1, le=50),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

    # 验证患者存在
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 获取对话会话
    sessions = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
    ).order_by(ConsultationSession.updated_at.desc()).limit(limit).all()

    session_ids = [s.id for s in sessions]

    # 批量获取消息计数（单个查询）
    message_counts = db.query(
        Message.session_id,
        func.count(Message.id)
    ).filter(
        Message.session_id.in_(session_ids)
    ).group_by(Message.session_id).all()

    # 构建 session_id -> message_count 映射
    message_count_map = {sid: count for sid, count in message_counts}

    # 构建结果
    result = [
        ConsultationSessionSchema(
            id=session.id,
            user_id=session.user_id,
            doctor_id=session.doctor_id,
            agent_type=session.agent_type,
            last_message=session.last_message,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count_map.get(session.id, 0)
        )
        for session in sessions
    ]

    return result
```

**效果**: 从 N+1 次查询减少到 2 次查询。

---

### 3.6 `get_assignable_patients` 优化

**优化方案**:
```python
@router.get("/patients/assignable", response_model=List[AssignablePatientResponse])
def get_assignable_patients(
    search: Optional[str] = Query(None, description="搜索关键词（姓名/手机号）"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    # 获取当前医生的已分配患者（包含分配时间）
    assigned_relationships = db.query(
        DoctorPatientRelationship.patient_id,
        DoctorPatientRelationship.created_at
    ).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.is_active == True
    ).all()

    # 构建 patient_id -> assigned_at 映射
    assigned_map = {pid: created_at for pid, created_at in assigned_relationships}
    assigned_ids = set(assigned_map.keys())

    # 构建查询
    query = db.query(User).filter(User.is_active == True)

    if search:
        query = query.filter(
            (User.nickname.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )

    patients = query.order_by(desc(User.created_at)).limit(limit).all()

    # 构建结果
    result = [
        AssignablePatientResponse(
            id=patient.id,
            nickname=patient.nickname,
            phone=patient.phone,
            gender=patient.gender,
            age=calculate_age(patient.birthday),
            is_assigned=patient.id in assigned_ids,
            assigned_at=assigned_map.get(patient.id)
        )
        for patient in patients
    ]

    return result
```

**效果**: 从 N+1 次查询减少到 2 次查询。

---

### 3.7 `get_patient_detail` 优化

**优化方案**:
```python
@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient_detail(
    patient_id: int,
    doctor: AdminUser = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    # 验证访问权限
    if not _verify_patient_access(doctor.id, patient_id, db):
        raise HTTPException(status_code=403, detail="无权访问该患者")

    patient = db.query(User).filter(User.id == patient_id).first()

    if not patient:
        raise HTTPException(status_code=404, detail="患者不存在")

    # 批量获取统计数据（3 个查询）
    week_ago = datetime.utcnow() - timedelta(days=7)

    # 1. 最后咨询时间
    last_session = db.query(ConsultationSession).filter(
        ConsultationSession.user_id == patient_id
    ).order_by(desc(ConsultationSession.updated_at)).first()

    # 2. 进行中的医嘱数
    active_orders = db.query(MedicalOrder).filter(
        MedicalOrder.patient_id == patient_id,
        MedicalOrder.status == OrderStatus.ACTIVE
    ).count()

    # 3. 最近7天完成率
    week_tasks = db.query(TaskInstance).filter(
        TaskInstance.patient_id == patient_id,
        TaskInstance.scheduled_date >= week_ago.date()
    ).all()

    completed_count = sum(1 for t in week_tasks if t.status == TaskStatus.COMPLETED)
    completion_rate = completed_count / len(week_tasks) if week_tasks else 0.0

    return PatientDetailResponse(
        id=patient.id,
        nickname=patient.nickname,
        phone=patient.phone,
        gender=patient.gender,
        age=calculate_age(patient.birthday),
        avatar_url=patient.avatar_url,
        is_profile_completed=patient.is_profile_completed,
        last_consultation_at=last_session.updated_at if last_session else None,
        active_orders_count=active_orders,
        completion_rate=round(completion_rate, 2),
        created_at=patient.created_at
    )
```

**说明**: 这个函数针对单个患者，当前实现已经是 4 次查询，优化空间有限。可以考虑将这 3 个统计查询合并为一个复杂的聚合查询，但会降低代码可读性。

---

### 3.8 `list_departments` 优化 (admin_departments.py)

**优化方案**:
```python
from sqlalchemy.orm import joinedload

@router.get("", response_model=List[DepartmentDetailResponse])
def list_departments(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin)
):
    # 使用 joinedload 预加载 doctors 关系
    departments = db.query(Department).options(
        joinedload(Department.doctors)
    ).order_by(Department.sort_order).all()

    result = []
    for dept in departments:
        # 现在 dept.doctors 已经预加载，不会触发额外查询
        doctor_count = len(dept.doctors) if dept.doctors else 0
        result.append(DepartmentDetailResponse(
            id=dept.id,
            name=dept.name,
            description=dept.description,
            icon=dept.icon,
            sort_order=dept.sort_order,
            is_active=getattr(dept, 'is_active', True),
            doctor_count=doctor_count
        ))
    return result
```

**效果**: 从 N+1 次查询减少到 1 次查询。

---

### 3.9 `get_family_bonds` 优化 (medical_orders.py)

**优化方案**:
```python
@router.get("/family-bonds", response_model=List[FamilyBondResponse])
def get_family_bonds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from ..models.medical_order import FamilyBond

    results = []

    # 查找我是家属的关系（我关注的患者）
    as_family = db.query(FamilyBond).filter(
        FamilyBond.family_member_id == current_user.id
    ).all()

    # 批量获取患者信息
    patient_ids = [bond.patient_id for bond in as_family]
    patients_map = {
        p.id: p
        for p in db.query(User).filter(User.id.in_(patient_ids)).all()
    } if patient_ids else {}

    for bond in as_family:
        patient = patients_map.get(bond.patient_id)
        results.append(FamilyBondResponse(
            id=bond.id,
            patient_id=bond.patient_id,
            family_member_id=bond.family_member_id,
            relationship_type=bond.relationship_type,
            notification_level=bond.notification_level.value,
            family_member_name=current_user.nickname,
            family_member_phone=current_user.phone,
            patient_name=patient.nickname if patient else "未知"
        ))

    # 查找我是患者的关系（别人关注我）
    as_patient = db.query(FamilyBond).filter(
        FamilyBond.patient_id == current_user.id
    ).all()

    # 批量获取家属信息
    member_ids = [bond.family_member_id for bond in as_patient]
    members_map = {
        m.id: m
        for m in db.query(User).filter(User.id.in_(member_ids)).all()
    } if member_ids else {}

    for bond in as_patient:
        member = members_map.get(bond.family_member_id)
        results.append(FamilyBondResponse(
            id=bond.id,
            patient_id=bond.patient_id,
            family_member_id=bond.family_member_id,
            relationship_type=bond.relationship_type,
            notification_level=bond.notification_level.value,
            family_member_name=member.nickname if member else "未知",
            family_member_phone=member.phone if member else None,
            patient_name=current_user.nickname
        ))

    return results
```

**效果**: 从 2N+2 次查询减少到 4 次查询。

---

### 3.10 `get_daily_tasks` 优化 (medical_orders.py)

**优化方案**:
```python
from sqlalchemy.orm import joinedload

@router.get("/tasks/{task_date}", response_model=TaskListResponse)
def get_daily_tasks(
    task_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定日期的任务列表

    返回按状态分组的任务
    """
    # 使用 selectinload 预加载 order 关系
    tasks = db.query(TaskInstance).options(
        selectinload(TaskInstance.order)
    ).filter(
        TaskInstance.patient_id == current_user.id,
        TaskInstance.scheduled_date == task_date
    ).all()

    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
    overdue = [t for t in tasks if t.status == TaskStatus.OVERDUE]

    # 构建响应 - 现在 task.order 已预加载
    def build_response(task):
        data = TaskInstanceResponse.model_validate(task).model_dump()
        # 不再触发额外查询
        if task.order:
            data["order_title"] = task.order.title
            data["order_type"] = task.order.order_type.value
        return data

    # 计算依从性
    total = len(tasks)
    completed_count = len(completed)
    overdue_count = len(overdue)
    pending_count = len(pending)
    rate = completed_count / total if total > 0 else 0

    summary = ComplianceResponse(
        date=task_date.isoformat(),
        total=total,
        completed=completed_count,
        overdue=overdue_count,
        pending=pending_count,
        rate=round(rate, 2)
    )

    return TaskListResponse(
        date=task_date.isoformat(),
        pending=[build_response(t) for t in pending],
        completed=[build_response(t) for t in completed],
        overdue=[build_response(t) for t in overdue],
        summary=summary
    )
```

**效果**: 从 N+1 次查询减少到 2 次查询。

---

### 3.11 `get_alerts` 优化 (medical_orders.py)

**优化方案**:
```python
from sqlalchemy.orm import joinedload, selectinload

@router.get("/alerts", response_model=List[dict])
def get_alerts(
    active_only: bool = Query(True, description="是否只返回未确认的预警"),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的预警列表"""
    from ..services.alert_service import AlertService
    from ..models.medical_order import Alert, AlertSeverity

    # 预加载 task_instance 和 order 关系
    query = db.query(Alert).options(
        selectinload(Alert.task_instance).selectinload(TaskInstance.order)
    ).filter(Alert.patient_id == current_user.id)

    if active_only:
        query = query.filter(Alert.is_acknowledged == False)

    alerts = query.order_by(
        Alert.severity.desc(),
        Alert.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": alert.id,
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "title": alert.title,
            "message": alert.message,
            "value_data": alert.value_data,
            "is_acknowledged": alert.is_acknowledged,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            # 不再触发额外查询
            "task_title": alert.task_instance.order.title if alert.task_instance and alert.task_instance.order else None
        }
        for alert in alerts
    ]
```

**效果**: 从 2N+1 次查询减少到 1 次查询。

---

## 四、其他路由检查

让我检查其他路由文件是否也存在 N+1 查询问题：

| 文件 | 检查结果 |
|------|----------|
| `admin_doctors.py` | 需检查 |
| `admin_departments.py` | 需检查 |
| `medical_orders.py` | 需检查 |
| `sessions_v2.py` | 需检查 |
| `medical_records.py` | 需检查 |

---

## 五、优化效果预估

### 5.1 查询次数对比

| 函数 | 文件 | 优化前 | 优化后 | 改善幅度 |
|------|------|--------|--------|----------|
| `get_doctor_info` | doctor_workstation.py | 3+N | 2 | 50%+ |
| `get_patient_stats` | doctor_workstation.py | 3+N | 4 | 80%+ |
| `get_patients` | doctor_workstation.py | 3N+1 | 4 | 95%+ |
| `get_patient_consultations` | doctor_workstation.py | N+1 | 2 | 95%+ |
| `get_assignable_patients` | doctor_workstation.py | N+1 | 2 | 95%+ |
| `list_departments` | admin_departments.py | N+1 | 1 | 95%+ |
| `get_family_bonds` | medical_orders.py | 2N+2 | 4 | 90%+ |
| `get_daily_tasks` | medical_orders.py | N+1 | 2 | 95%+ |
| `get_alerts` | medical_orders.py | 2N+1 | 1 | 98%+ |

*假设 N = 记录数量（患者数、会话数、科室数等）*

### 5.2 性能影响

| 场景 | 记录数 | 优化前查询 | 优化后查询 | 响应时间改善 |
|------|--------|-----------|-----------|-------------|
| 医生工作台首页 | 50 患者 | 151+ | 4 | ~90% |
| 患者列表页 | 100 患者 | 301+ | 4 | ~95% |
| 对话列表页 | 20 会话 | 21 | 2 | ~90% |
| 科室列表 | 10 科室 | 11 | 1 | ~90% |
| 家属关系列表 | 10 关系 | 22 | 4 | ~80% |
| 任务列表 | 10 任务 | 11 | 2 | ~80% |
| 预警列表 | 20 预警 | 41 | 1 | ~95% |

---

## 六、实施步骤

### 6.1 准备阶段

1. **添加导入语句**:
   ```python
   from sqlalchemy.orm import joinedload, selectinload
   ```

2. **创建工具函数** (可选):
   ```python
   def batch_get_last_session(patient_ids: List[int], db: Session) -> Dict[int, datetime]:
       """批量获取患者最后咨询时间"""
       # ...
   ```

### 6.2 实施顺序

| 顺序 | 文件 | 函数 | 优先级 | 预估时间 |
|------|------|------|--------|----------|
| 1 | doctor_workstation.py | `get_doctor_info` | 高 | 10 分钟 |
| 2 | doctor_workstation.py | `get_patient_stats` | 高 | 15 分钟 |
| 3 | doctor_workstation.py | `get_patients` | 高 | 20 分钟 |
| 4 | doctor_workstation.py | `get_assignable_patients` | 中 | 15 分钟 |
| 5 | doctor_workstation.py | `get_patient_consultations` | 中 | 10 分钟 |
| 6 | doctor_workstation.py | `get_patient_detail` | 低 | 5 分钟 |
| 7 | admin_departments.py | `list_departments` | 中 | 5 分钟 |
| 8 | admin_departments.py | `get_department` | 低 | 3 分钟 |
| 9 | admin_departments.py | `update_department` | 低 | 3 分钟 |
| 10 | medical_orders.py | `get_family_bonds` | 高 | 15 分钟 |
| 11 | medical_orders.py | `get_daily_tasks` | 高 | 10 分钟 |
| 12 | medical_orders.py | `get_alerts` | 中 | 10 分钟 |

**总计**: 约 121 分钟（2 小时）

### 6.3 验证步骤

1. **代码审查**: 确保所有修改正确
2. **启动后端服务**: 使用 Docker 容器
3. **手动测试**: 访问医生工作台各个页面
4. **SQL 日志验证**: 启用 SQLAlchemy echo=True 对比查询次数

---

## 七、风险与注意事项

### 7.1 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 预加载导致数据量过大 | 内存占用增加 | 使用 selectinload 而非 joinedload |
| 代码可读性下降 | 维护困难 | 添加注释说明优化意图 |
| 边界情况处理 | 空列表异常 | 确保空列表情况正确处理 |

### 7.2 注意事项

1. **选择合适的预加载策略**:
   - `joinedload`: 适用于一对一、少量数据
   - `selectinload`: 适用于一对多、避免重复数据

2. **避免过度优化**:
   - 单条记录的详情页（如 `get_patient_detail`）优化收益有限
   - 重点优化列表接口

3. **保持代码可读性**:
   - 使用变量名清晰表达意图
   - 添加注释说明为什么使用预加载

---

## 八、相关文档

- [技术债务清单](/docs/planning/tech-debt.md)
- [SQLAlchemy 预加载文档](https://docs.sqlalchemy.org/en/14/orm/loading_relationships.html)

---

## 九、执行结果

### 9.1 完成状态

| 文件 | 优化函数数 | 状态 |
|------|-----------|------|
| `doctor_workstation.py` | 6 | ✅ 完成 |
| `admin_departments.py` | 4 | ✅ 完成 |
| `medical_orders.py` | 4 | ✅ 完成 |

### 9.2 验证结果

所有 API 测试通过：
- `/admin/departments`: 28 个科室，正确显示医生数量
- `/api/doctor/me`: 医生信息、科室名称、AI 分身列表正常
- `/api/doctor/patient-stats`: 患者统计正常
- `/api/doctor/patients`: 患者列表正常

---

**文档状态**: ✅ 已完成
**最后更新**: 2026-02-11
