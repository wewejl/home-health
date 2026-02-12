# Schema Weekdays 字段补全设计文档

> **创建日期**: 2026-02-12
> **状态**: 设计中
> **优先级**: P1 (中)

---

## 1. 问题分析

### 1.1 当前问题

**问题描述**：
`medical_events` 表缺少 `weekdays` 字段，导致前端无法显示事件发生的是周几。

**影响范围**：
- 医疗事件列表显示
- 医生日历视图
- 医生工作台事件统计

### 1.2 数据库现状

**表**: `medical_events`

**现有字段**:
```sql
CREATE TABLE medical_events (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES users(id),
    doctor_id UUID REFERENCES doctors(id),
    event_type VARCHAR,
    title VARCHAR,
    description TEXT,
    event_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
    -- 缺少: weekdays 字段
);
```

**需要的字段**:
```sql
weekdays VARCHAR(20)  -- 例如: "周一,周二" 或 JSON 数组
```

---

## 2. 解决方案

### 2.1 数据存储方案

#### 方案 A: 存储周名称（推荐）

```sql
weekdays VARCHAR(20)  -- 存储中文周名称
-- 示例: "周一", "周二", "周三,周四"
-- 优点: 简单，易读，易搜索
-- 缺点: 不支持多天事件
```

#### 方案 B: 存储 JSON 数组

```sql
weekdays JSONB  -- 存储 JSON 数组
-- 示例: ["周一", "周二"]
-- 优点: 支持多天事件
-- 缺点: 查询和排序复杂
```

#### 方案 C: 存储数字索引

```sql
weekday_indexes VARCHAR(10)  -- 存储数字索引
-- 示例: "1,2,3,4"
-- 优点: 紧凑，易于排序
-- 缺点: 需要前端转换显示
```

**推荐方案 A**：存储周名称，简化实现。

### 2.2 自动计算策略

```python
# backend/app/models/medical_event.py

from datetime import datetime

class MedicalEvent(Base):
    # ... 现有字段 ...

    weekdays = Column(String(20), nullable=True)

    @staticmethod
    def calculate_weekday(event_date: date) -> str:
        """根据日期自动计算周几"""
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        return weekdays[event_date.weekday()]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 如果创建时未提供 weekdays，自动计算
        if not self.weekdays and self.event_date:
            self.weekdays = self.calculate_weekday(self.event_date)
```

---

## 3. 数据库迁移

### 3.1 迁移脚本

```python
# backend/migrations/versions/add_weekdays_to_medical_events.py

from alembic import op
import sqlalchemy as sa

def upgrade():
    # 添加 weekdays 列
    op.add_column('medical_events', 'weekdays',
                sa.String(length=20, nullable=True))

    # 为现有数据计算并填充 weekdays
    from sqlalchemy.orm import sessionmaker
    from app.models.medical_event import MedicalEvent

    Session = sessionmaker(bind=op.get_bind())
    session = Session()

    # 获取所有没有 weekdays 的记录
    events = session.query(MedicalEvent)\
        .filter(MedicalEvent.weekdays.is_(None))\
        .all()

    for event in events:
        if event.event_date:
            weekdays = MedicalEvent.calculate_weekday(event.event_date)
            event.weekdays = weekdays

    session.commit()

def downgrade():
    # 移除 weekdays 列
    op.drop_column('medical_events', 'weekdays')
```

### 3.2 回滚计划

- 保留原有数据（删除 weekdays 字段）
- 可选：备份数据到临时表

---

## 4. 后端实现

### 4.1 Schema 更新

```python
# backend/app/models/medical_event.py

class MedicalEvent(Base):
    __tablename__ = 'medical_events'

    # ... 现有字段 ...

    weekdays = Column(String(20), nullable=True, index=True)
    """事件发生的周几，如：周一、周二、周三"""

    # 索引优化：支持按周几查询
    __table_args__ = (
        Index('idx_medical_events_weekdays', 'weekdays'),
    )
```

### 4.2 API 适配

```python
# backend/app/routes/medical_events.py

from pydantic import BaseModel

class MedicalEventResponse(BaseModel):
    # ... 现有字段 ...
    weekdays: Optional[str] = None  # 新增字段

class MedicalEventCreate(BaseModel):
    # ... 现有字段 ...
    weekdays: Optional[str] = None  # 创建时可指定

@router.post("/events", response_model=MedicalEventResponse)
async def create_event(
    event: MedicalEventCreate,
    db: Session = Depends(get_db)
):
    """创建医疗事件"""
    # 如果未提供 weekdays，自动计算
    if not event.weekdays and event.event_date:
        event.weekdays = MedicalEvent.calculate_weekday(event.event_date)

    db_event = MedicalEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event
```

### 4.3 周筛选支持

```python
@router.get("/events")
async def get_events(
    doctor_id: int,
    weekday: Optional[str] = None,  # 新增：按周几筛选
    db: Session = Depends(get_db)
):
    """获取医疗事件列表，支持按周几筛选"""
    query = db.query(MedicalEvent).filter(
        MedicalEvent.doctor_id == doctor_id
    )

    # 周几筛选
    if weekday:
        query = query.filter(MedicalEvent.weekdays == weekday)

    return query.order_by(MedicalEvent.event_date.desc()).all()
```

---

## 5. 前端实现

### 5.1 类型定义

```typescript
// frontend/src/types/medical-event.ts

export interface MedicalEvent {
  id: string;
  patient_id: string;
  doctor_id: string;
  event_type: string;
  title: string;
  description?: string;
  event_date: string;
  weekdays?: string;  // 新增字段
  created_at: string;
  updated_at: string;
}

// 周几常量
export const WEEKDAYS = [
  { value: '周一', label: '周一' },
  { value: '周二', label: '周二' },
  { value: '周三', label: '周三' },
  { value: '周四', label: '周四' },
  { value: '周五', label: '周五' },
  { value: '周六', label: '周六' },
  { value: '周日', label: '周日' },
];
```

### 5.2 显示组件

```typescript
// frontend/src/components/EventCard.tsx

import { WEEKDAYS } from '@/types/medical-event';

interface EventCardProps {
  event: MedicalEvent;
}

export function EventCard({ event }: EventCardProps) {
  // 解析 weekdays（支持逗号分隔的多天）
  const weekdayList = event.weekdays
    ? event.weekdays.split(',')
    : [];

  return (
    <div className="event-card">
      <div className="event-header">
        <span className="event-date">
          {formatDate(event.event_date)}
        </span>
        {/* 显示周几标签 */}
        {weekdayList.length > 0 && (
          <div className="weekdays-tags">
            {weekdayList.map(day => (
              <Tag key={day} color="blue">
                {day}
              </Tag>
            ))}
          </div>
        )}
      </div>

      <h3 className="event-title">{event.title}</h3>

      {/* 其他内容... */}
    </div>
  );
}
```

### 5.3 日历视图增强

```typescript
// frontend/src/components/DoctorCalendar.tsx

import { WEEKDAYS } from '@/types/medical-event';

interface DoctorCalendarProps {
  events: MedicalEvent[];
  onDateSelect: (date: Date) => void;
}

export function DoctorCalendar({ events, onDateSelect }: DoctorCalendarProps) {
  // 按周几分组事件
  const eventsByWeekday = useMemo(() => {
    const grouped = {
      '周一': [], '周二': [], '周三': [], '周四': [],
      '周五': [], '周六': [], '周日': [],
    };

    events.forEach(event => {
      if (event.weekdays) {
        const days = event.weekdays.split(',');
        days.forEach(day => {
          if (grouped[day])) {
            grouped[day].push(event);
          }
        });
      }
    });

    return grouped;
  }, [events]);

  return (
    <div className="doctor-calendar">
      <div className="weekday-header">
        {WEEKDAYS.map(wd => (
          <div key={wd.value} className="weekday-col">
            <div className="weekday-label">{wd.label}</div>
            <div className="weekday-events">
              {eventsByWeekday[wd.value].map(event => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 6. UI 设计

### 6.1 事件卡片显示

```
┌─────────────────────────────────────────────────────────┐
│  📅 2024年2月12日 (周一)             [详情] │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  复诊 - 高血压管理                       │
│                                                 │
│  患者: 张三                               │
│  │ 时间: 09:00-10:00                    │
│  │ 备注: 测量血压，调整用药剂量...         │
│  │                                    [编辑] [删除] │
│                                                 │
└─────────────────────────────────────────────────────────┘
```

### 6.2 日历周视图

```
┌─────────────────────────────────────────────────────────┐
│  2024年2月                              [上月] [下月] │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┬──────────┬──────────┬──────────┐   │
│  │ 周一    │ 周二    │ 周三    │ 周四    │   │
│  ├──────────┼──────────┼──────────┼──────────┤   │
│  │ 🟢 晨检 │ 🟢 查房 │ 🔴 手术 │ 🟢 随访 │   │
│  │         │         │         │         │   │
│  │ 3人     │ 5人     │ 1人     │ 2人     │   │
│  └──────────┴──────────┴──────────┴──────────┘   │
│                                                 │
│  本月统计: 共 23 个事件                   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. 测试计划

### 7.1 单元测试

```python
# backend/test/test_medical_events_weekdays.py

class TestWeekdaysField:
    def test_auto_calculate_weekday(self):
        """测试自动计算周几"""
        # 创建事件不提供 weekdays
        event = MedicalEvent(
            event_date=date(2024, 2, 12),  # 周一
            weekdays=None
        )
        assert event.calculate_weekday() == "周一"

    def test_multi_day_event(self):
        """测试多天事件"""
        event = MedicalEvent(
            weekdays="周一,周二,周三"
        )
        assert "," in event.weekdays

    def test_filter_by_weekday(self):
        """测试按周几筛选"""
        # 创建不同周几的事件
        # 查询筛选
        # 验证结果

class TestWeekdayAPI:
    def test_create_event_with_weekday(self): ...
    def test_get_events_filter_weekday(self): ...
```

### 7.2 集成测试

1. 创建事件 → 验证 weekdays 字段有值
2. 编辑事件日期 → 验证 weekdays 自动更新
3. 删除事件 → 不影响其他记录
4. 按周几筛选 → 返回正确结果

---

## 8. 实施计划

### Phase 1: 数据库迁移 (1h)
- [ ] 创建 Alembic 迁移脚本
- [ ] 编写 weekdays 自动计算逻辑
- [ ] 执行迁移
- [ ] 验证数据正确性

### Phase 2: 后端实现 (1h)
- [ ] 更新 MedicalEvent 模型
- [ ] 更新 Schema 定义
- [ ] 添加周筛选 API 参数
- [ ] 编写单元测试

### Phase 3: 前端实现 (2h)
- [ ] 更新 MedicalEvent 类型
- [ ] 更新 EventCard 组件显示周几
- [ ] 创建日历周视图组件
- [ ] 添加周筛选器组件

### Phase 4: 测试验证 (1h)
- [ ] 运行单元测试
- [ ] 手动测试创建流程
- [ ] 验证前端显示正确

---

## 9. 验收标准

- [ ] medical_events 表包含 weekdays 字段
- [ ] 创建事件时自动计算周几
- [ ] 前端事件卡片显示周几标签
- [ ] 日历视图支持按周分组
- [ ] API 支持按周几筛选
- [ ] 所有迁移可回滚
- [ ] 单元测试覆盖率 > 80%
- [ ] 前端组件通过 ESLint

---

## 10. 风险和注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 迁移数据量大 | 执行时间长 | 分批执行，每批1000条 |
| 前端未传 weekdays | 显示为空 | 后端自动计算兜底 |
| 跨天事件 | 显示不完整 | 支持多 weekdays 存储 |
| 周几国际化 | 仅支持中文 | 后期可添加 i18n 支持 |

---

*文档版本*: v1.0
*最后更新*: 2026-02-12
