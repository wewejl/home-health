# 患者搜索功能优化设计文档

> **创建日期**: 2026-02-12
> **状态**: 设计中
> **优先级**: P1 (高)

---

## 1. 现状分析

### 1.1 当前实现

**文件**: `frontend/src/pages/doctor/PatientList.tsx`

**现有功能**:
```typescript
// 当前搜索实现
const [searchTerm, setSearchTerm] = useState('');

// 搜索逻辑
const filteredPatients = patients.filter(p =>
  p.name?.includes(searchTerm) || p.phone?.includes(searchTerm)
);
```

**问题**:
- ❌ 每次输入都触发过滤（无防抖）
- ❌ 仅支持姓名/手机号精确匹配
- ❌ 无搜索历史
- ❌ 无高级筛选

### 1.2 后端 API

**文件**: `backend/app/routes/doctor_workstation.py`

**现有端点**:
```python
@router.get("/patients", response_model=PatientListResponse)
async def get_patients(
    doctor_id: int,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    # 简单的 LIKE 查询
    pass
```

**问题**:
- ❌ 搜索使用 `LIKE %term%`（效率低）
- ❌ 无搜索结果排序
- ❌ 无搜索统计

---

## 2. 优化方案

### 2.1 前端优化

#### 2.1.1 防抖搜索

```typescript
// hooks/useDebounceSearch.ts

import { useEffect, useRef } from 'react';

export function useDebounceSearch(
  searchTerm: string,
  delay: number = 300,
  onSearch: (term: string) => void
) {
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // 清除之前的定时器
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // 设置新的定时器
    timeoutRef.current = setTimeout(() => {
      onSearch(searchTerm.trim());
    }, delay);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [searchTerm, delay, onSearch]);
}
```

#### 2.1.2 搜索状态管理

```typescript
// 搜索状态枚举
enum SearchStatus {
  IDLE = 'idle',        // 未搜索
  SEARCHING = 'searching', // 搜索中
  RESULTS = 'results',    // 有结果
  EMPTY = 'empty'         // 无结果
}

interface SearchState {
  status: SearchStatus;
  searchTerm: string;
  searchHistory: string[];
  results: Patient[];
  resultCount: number;
}
```

#### 2.1.3 搜索历史

```typescript
// LocalStorage keys
const SEARCH_HISTORY_KEY = 'patient_search_history';
const MAX_HISTORY = 10;

// 保存搜索历史
function saveSearchHistory(term: string) {
  const history = getSearchHistory();
  const filtered = history.filter(t => t !== term);
  const updated = [term, ...filtered].slice(0, MAX_HISTORY);
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(updated));
}

// 显示搜索历史
function renderSearchHistory(history: string[]) {
  return (
    <div className="search-history">
      {history.map(term => (
        <div onClick={() => performSearch(term)}>
          🔍 {term}
        </div>
      ))}
    </div>
  );
}
```

### 2.2 后端优化

#### 2.2.1 全文搜索

```python
# backend/app/routes/doctor_workstation.py

from sqlalchemy import or_, func

@router.get("/patients/search")
async def search_patients(
    doctor_id: int,
    q: str,  # 搜索关键词
    db: Session = Depends(get_db)
):
    """
    全文搜索优化：
    1. 使用 pgsql 全文索引（如果配置）
    2. 多字段加权搜索
    3. 相关性排序
    """

    # 构建搜索条件
    conditions = []

    # 姓名（权重最高）
    conditions.append(
        Patient.name.ilike(f'%{q}%').label('name_relevance')
    )

    # 手机号
    conditions.append(
        Patient.phone.ilike(f'%{q}%').label('phone_relevance')
    )

    # 身份证
    conditions.append(
        Patient.id_card.ilike(f'%{q}%').label('id_card_relevance')
    )

    # 执行查询并按相关性排序
    query = db.query(Patient).filter(
        Patient.assigned_doctor_id == doctor_id
    ).filter(or_(*conditions))

    results = query.order_by(
        # 按相关性排序（匹配靠前的优先）
        case(
            (Patient.name.ilike(f'{q}%'), 1),
            (Patient.phone.ilike(f'{q}%'), 2),
            (Patient.id_card.ilike(f'{q}%'), 3),
            else_=4
        )
    ).limit(20).all()

    return {
        "patients": [format_patient(p) for p in results],
        "total": len(results)
    }
```

#### 2.2.2 高级筛选

```python
@router.get("/patients")
async def get_patients(
    doctor_id: int,
    search: Optional[str] = None,
    status: Optional[str] = None,      # 新增：状态筛选
    assigned_date_from: Optional[str],  # 新增：分配日期起
    assigned_date_to: Optional[str],    # 新增：分配日期止
    has_orders: Optional[bool],         # 新增：是否有医嘱
    db: Session = Depends(get_db)
):
    """高级筛选患者列表"""
    query = db.query(Patient).filter(
        Patient.assigned_doctor_id == doctor_id
    )

    # 状态筛选
    if status == 'active':
        query = query.filter(Patient.is_active == True)
    elif status == 'inactive':
        query = query.filter(Patient.is_active == False)

    # 日期范围筛选
    if assigned_date_from:
        query = query.filter(Patient.assigned_at >= assigned_date_from)
    if assigned_date_to:
        query = query.filter(Patient.assigned_at <= assigned_date_to)

    # 是否有医嘱
    if has_orders is not None:
        subquery = db.query(MedicalOrder.id).filter(
            MedicalOrder.patient_id == Patient.id
        )
        if has_orders:
            query = query.filter(subquery.exists())
        else:
            query = query.filter(~subquery.exists())

    # 分页
    results = query.order_by(Patient.assigned_at.desc())\
                   .offset(skip).limit(limit).all()

    return format_patient_list(results)
```

### 2.3 搜索统计

```python
# 记录搜索统计
from app.models.search_log import SearchLog

@router.post("/search/log")
async def log_search(
    doctor_id: int,
    search_term: str,
    results_count: int,
    db: Session = Depends(get_db)
):
    """记录搜索用于分析"""
    log = SearchLog(
        doctor_id=doctor_id,
        search_term=search_term,
        results_count=results_count
    )
    db.add(log)
    db.commit()
    return {"status": "logged"}
```

---

## 3. UI 设计

### 3.1 搜索框

```
┌─────────────────────────────────────────────────────────┐
│  患者管理                        [+ 新增患者]    │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │ 🔍 [搜索患者姓名或手机号...]        │   │
│  │                        [⚙️ 筛选] [🕒 历史] │   │
│  └─────────────────────────────────────────────┘   │
│                                                 │
│  搜索历史 (点击展开):                          │
│  ┌───────────────────────────────────────┐       │
│  │ 🕒 张三                     │       │
│  │ 🕒 李四                │       │
│  │ 🕒 13800138000         │       │
│  └───────────────────────────────────────┘       │
│                                                 │
│  搜索结果 (共 24 条):                         │
│  ┌─────────────────────────────────────────┐   │
│  │ 姓名         手机号        状态  操作 │   │
│  ├─────────────────────────────────────────┤   │
│  │ 张三        138****       活跃  [详情]│   │
│  │ 李四        139****       活跃  [详情]│   │
│  │ 王五        137****       离线  [详情]│   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│                              [显示更多 20]      │
└─────────────────────────────────────────────────┘
```

### 3.2 高级筛选面板

```
┌─────────────────────────────────────────────────────────┐
│  高级筛选                            [应用] [重置] │
├─────────────────────────────────────────────────────────┤
│                                                 │
│  患者状态:                                    │
│   ○ 全部  ● 活跃  ○ 离线             │
│                                                 │
│  分配日期:                                    │
│   从: [2024-01-01]  至: [2024-02-12]  │
│                                                 │
│  医嘱状态:                                    │
│   ○ 全部  ● 有医嘱  ○ 无医嘱          │
│                                                 │
│  排序方式:                                    │
│   ● 最近分配  ○ 姓名 A-Z  ○ 姓名 Z-A   │
│                                                 │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 技术实现

### 4.1 前端组件

```typescript
// PatientSearchBar.tsx

import { useDebounceSearch } from '@/hooks/useDebounceSearch';
import { saveSearchHistory, getSearchHistory } from '@/utils/searchHistory';

export function PatientSearchBar({ onSearch }: { onSearch: (term: string) => void }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const searchHistory = getSearchHistory();

  // 使用防抖搜索
  const debouncedSearch = useDebounceSearch(searchTerm, 300, onSearch);

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    if (term.trim()) {
      saveSearchHistory(term.trim());
      debouncedSearch(term.trim());
    }
  };

  return (
    <div className="patient-search-bar">
      {/* 搜索输入框 */}
      <Input
        placeholder="搜索患者姓名或手机号"
        value={searchTerm}
        onChange={(e) => handleSearch(e.target.value)}
        onFocus={() => setShowHistory(true)}
        prefix={<SearchOutlined />}
        allowClear
      />

      {/* 搜索历史下拉 */}
      {showHistory && (
        <Dropdown>
          {searchHistory.map(term => (
            <Dropdown.Item onClick={() => handleSearch(term)}>
              🕒 {term}
            </Dropdown.Item>
          ))}
        </Dropdown>
      )}

      {/* 筛选按钮 */}
      <Button icon={<FilterOutlined />} onClick={() => setShowFilters(true)} />

      {/* 历史按钮 */}
      <Button icon={<HistoryOutlined />} />
    </div>
  );
}
```

### 4.2 后端索引优化

```sql
-- 添加数据库索引用于搜索
CREATE INDEX IF NOT EXISTS idx_patients_doctor_name
ON patients(assigned_doctor_id, name);

CREATE INDEX IF NOT EXISTS idx_patients_doctor_phone
ON patients(assigned_doctor_id, phone);

CREATE INDEX IF NOT EXISTS idx_patients_doctor_id_card
ON patients(assigned_doctor_id, id_card);

-- 复合索引用于排序
CREATE INDEX IF NOT EXISTS idx_patients_assigned_status
ON patients(assigned_doctor_id, is_active, assigned_at DESC);
```

---

## 5. 测试计划

### 5.1 单元测试

```python
# backend/test/test_patient_search_api.py

class TestPatientSearchAPI:
    def test_search_by_name(self): ...
    def test_search_by_phone(self): ...
    def test_search_empty_result(self): ...
    def test_search_special_characters(self): ...

class TestAdvancedFilters:
    def test_filter_by_status(self): ...
    def test_filter_by_date_range(self): ...
    def test_filter_has_orders(self): ...
```

### 5.2 性能测试

```python
# 测试大量数据下的搜索性能

def test_search_performance_1000_patients(db_session):
    """测试1000患者时搜索性能"""
    # 创建1000个患者
    for i in range(1000):
        patient = Patient(name=f"患者{i}", phone=f"139{i:08d}", ...)
        db_session.add(patient)
    db_session.commit()

    # 测试搜索响应时间
    start = time.time()
    response = client.get(f"/api/doctor/patients?search=患者1")
    duration = time.time() - start

    # 应该在500ms内返回
    assert duration < 0.5
```

---

## 6. 实施计划

### Phase 1: 前端防抖 (1h)
- [ ] 创建 `useDebounceSearch` hook
- [ ] 添加搜索历史功能
- [ ] 更新 `PatientList.tsx` 使用新搜索

### Phase 2: 后端优化 (2h)
- [ ] 优化患者搜索 API
- [ ] 添加高级筛选参数
- [ ] 添加数据库索引

### Phase 3: UI 组件 (2h)
- [ ] 创建 `PatientSearchBar` 组件
- [ ] 创建高级筛选面板
- [ ] 搜索历史下拉组件

### Phase 4: 测试 (1h)
- [ ] 编写搜索 API 测试
- [ ] 性能测试
- [ ] 端到端测试

---

## 7. 验收标准

- [ ] 搜索输入有 300ms 防抖
- [ ] 支持搜索历史（最多10条）
- [ ] 支持按状态/日期/医嘱筛选
- [ ] 搜索结果按相关性排序
- [ ] 搜索响应时间 < 500ms (1000患者)
- [ ] 前端组件通过 ESLint
- [ ] 功能文档更新

---

*文档版本*: v1.0
*最后更新*: 2026-02-12
