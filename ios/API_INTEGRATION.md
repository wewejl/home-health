# iOS 全面接入 API 方案文档

## 1. 概述

本文档记录 iOS 端从演示模式切换到全面接入后端 API 的改动内容和联调步骤。

---

## 2. 已完成的改动

### 2.1 移除 Mock 数据

**DepartmentDetailView.swift**
- 删除 `mockDoctors` 数组（约 80 行硬编码数据）
- 删除用于 mock 的 `DoctorInfo` 初始化器
- `loadDoctors()` 失败时只显示"暂无数据/重试"，不再 fallback 到假数据

**AskDoctorView.swift**
- 删除硬编码的 `internalMedicineDepartments`、`surgeryDepartments`、`otherDepartments`
- 删除 `QuickDepartmentsView`、`SectionAnchorView`、`DepartmentSectionView` 等使用静态数据的组件
- 新增 `DepartmentListView` 和 `DepartmentCardView`，直接使用 `DepartmentModel` 展示

**HomeView.swift**
- `DepartmentGridView` 改为从 API 加载科室列表
- 显示前 7 个科室 + "更多科室" 入口

### 2.2 精简模型

**DoctorInfo (DepartmentDetailView.swift)**
- 仅保留后端提供的字段：`doctorId, name, title, canPrescribe, isTopHospital, hospital, department, specialty, rating, monthlyAnswers, avgResponseTime`
- UI 展示字段（badges, textPrice, avatarColor 等）改为计算属性，使用默认值

**DepartmentModel (APIModels.swift)**
- 新增 `Hashable` 协议支持，用于 `navigationDestination`

### 2.3 数据流

```
HomeView / AskDoctorView
    ↓ onAppear
APIService.getDepartments()
    ↓
DepartmentModel[]
    ↓ 用户点击
DepartmentDetailView(departmentId)
    ↓ onAppear
APIService.getDoctors(departmentId)
    ↓
DoctorInfo[] (从 DoctorModel 映射)
    ↓ 用户点击
DoctorChatView(doctor)
    ↓
APIService.createSession / sendMessage
```

---

## 3. 后端基础数据

后端 `seed.py` 已包含：
- **12 个科室**：皮肤科、儿科、妇产科、消化内科、呼吸内科、心血管内科、内分泌科、神经内科、骨科、眼科、耳鼻咽喉科、口腔科
- **16 名医生**：每个科室 1-3 名，包含完整的职称、医院、专长等信息

### 初始化数据

```bash
cd backend
source venv/bin/activate
python -m app.seed
```

如需清空重建：
```bash
rm app.db
python -m app.seed
```

---

## 4. 联调步骤

### 4.1 启动后端

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：访问 `http://localhost:8000/docs` 查看 API 文档

### 4.2 配置 iOS BaseURL

编辑 `ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift`：

```swift
case .development:
    // 真机测试：替换为 Mac 局域网 IP
    // 终端运行: ifconfig | grep "inet " 获取 IP
    return "http://192.168.x.x:8000"
```

> ⚠️ 127.0.0.1 在真机上不可用，必须使用局域网 IP

### 4.3 测试流程

1. **登录**：任意手机号 + 验证码 `000000`
2. **首页**：科室网格应显示真实科室（从 API 加载）
3. **问医生**：科室列表应显示 12 个科室
4. **选择科室**：进入后应显示该科室的医生列表
5. **选择医生**：进入聊天界面，发送消息应得到 AI 回复

### 4.4 常见问题

| 现象 | 原因 | 解决方案 |
|------|------|----------|
| 科室列表为空 | 后端未启动或 seed 未执行 | 启动后端并执行 `python -m app.seed` |
| 网络连接失败 | BaseURL 配置错误 | 检查 APIConfig 中的 IP 地址 |
| 401 未授权 | Token 失效或未登录 | 重新登录获取 token |
| 医生列表为空 | 该科室无医生数据 | 检查 seed.py 中的 department_id 映射 |

---

## 5. 后续扩展

### 新增字段

如需在 iOS 显示更多医生信息（如价格、徽章）：

1. 后端 `Doctor` 模型添加字段
2. 更新 `DoctorResponse` schema
3. 执行数据库迁移
4. iOS `DoctorModel` 添加对应字段
5. `DoctorInfo` 初始化器中映射新字段

### 新增业务接口

1. 后端新增 route + service
2. iOS `APIConfig.Endpoints` 添加路径
3. `APIService` 添加请求方法
4. View 层调用并展示

---

## 6. 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `Views/DepartmentDetailView.swift` | 修改 | 移除 mock，精简 DoctorInfo |
| `Views/AskDoctorView.swift` | 修改 | 移除硬编码科室，使用 API 数据 |
| `Views/HomeView.swift` | 修改 | DepartmentGridView 改为 API 加载 |
| `Models/APIModels.swift` | 修改 | DepartmentModel 添加 Hashable |
| `ios/API_INTEGRATION.md` | 新增 | 本文档 |

---

*文档更新时间：2025-12-27*
