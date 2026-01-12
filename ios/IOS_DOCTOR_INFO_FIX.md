# iOS端医生信息修改方案

## 问题描述
iOS端在 `DoctorChatView.swift` 中硬编码了医生介绍文本，需要修改为使用后端API返回的真实数据。

## 修改位置

### 文件：`xinlingyisheng/xinlingyisheng/Views/DoctorChatView.swift`

需要修改的代码位置：**第904-921行**

## 当前问题代码

```swift
// Tab内容
VStack(alignment: .leading, spacing: 8) {
    if selectedTab == 0 {
        Text("擅长\(doctor.specialty)等疾病的诊治，具有丰富的临床经验。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(3)
    } else if selectedTab == 1 {
        Text("团队由多名资深医生组成，专注于\(doctor.department)领域，为患者提供专业、贴心的医疗服务。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(3)
    } else {
        Text("多次获得医院先进工作者称号，发表学术论文多篇，参与多项科研项目。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(3)
    }
}
```

## 解决方案

### 步骤1：确保后端API返回 `intro` 字段

后端 `DoctorModel` 已经包含 `intro` 字段（见 `APIModels.swift:93`），确保API返回该字段。

### 步骤2：修改 `DoctorInfo` 模型

在 `DepartmentDetailView.swift` 的 `DoctorInfo` 结构体中添加 `intro` 字段：

**文件位置：** `xinlingyisheng/xinlingyisheng/Views/DepartmentDetailView.swift:160-208`

```swift
struct DoctorInfo: Identifiable, Hashable {
    // ... 现有字段 ...
    let intro: String?  // 添加这个字段
    
    // 从 API 模型初始化
    init(from model: DoctorModel, departmentName: String) {
        self.doctorId = model.id
        self.name = model.name
        self.title = model.title ?? "主治医师"
        self.canPrescribe = model.can_prescribe
        self.isTopHospital = model.is_top_hospital
        self.hospital = model.hospital ?? "未知医院"
        self.department = departmentName
        self.specialty = model.specialty ?? ""
        self.intro = model.intro  // 添加这一行
        self.rating = model.rating
        self.monthlyAnswers = model.monthly_answers
        self.avgResponseTime = model.avg_response_time
    }
}
```

### 步骤3：修改 `DoctorInfoCardView` 的Tab内容显示

**文件位置：** `xinlingyisheng/xinlingyisheng/Views/DoctorChatView.swift:904-921`

将硬编码的文本替换为使用后端数据：

```swift
// Tab内容
VStack(alignment: .leading, spacing: 8) {
    if selectedTab == 0 {
        // 专业擅长 - 使用 specialty 字段
        Text(doctor.specialty.isEmpty ? "暂无专长信息" : doctor.specialty)
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    } else if selectedTab == 1 {
        // 团队简介 - 使用 intro 字段
        Text(doctor.intro ?? "由多位资深\(doctor.department)专家知识库训练的AI智能体，专注于\(doctor.department)领域疾病的诊断、治疗建议和健康管理。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    } else {
        // 获奖荣誉 - 可以使用 intro 或自定义文本
        Text("基于权威医学知识库和临床指南训练，持续学习最新医学研究成果，为您提供专业、及时的医疗咨询服务。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    }
}
.frame(maxWidth: .infinity, alignment: .leading)
```

### 步骤4：更新医生名片显示

如果需要，可以在医生名片区域也显示更多真实信息：

**文件位置：** `xinlingyisheng/xinlingyisheng/Views/DoctorChatView.swift:836-885`

```swift
// 医院标签 - 使用真实医院名称
HStack(spacing: 8) {
    if doctor.isTopHospital {
        DoctorBadgeTag(text: "AI智能体", color: DXYColors.teal)
    }
    
    // 如果医院名称不是默认值，显示医院名称
    if !doctor.hospital.isEmpty && doctor.hospital != "未知医院" {
        Text(doctor.hospital)
            .font(.system(size: 12))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(1)
    }
}
```

## 完整修改代码

### 修改1：DepartmentDetailView.swift - DoctorInfo结构体

```swift
struct DoctorInfo: Identifiable, Hashable {
    static func == (lhs: DoctorInfo, rhs: DoctorInfo) -> Bool {
        lhs.id == rhs.id
    }
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
    
    let doctorId: Int
    var id: Int { doctorId }
    let name: String
    let title: String
    let canPrescribe: Bool
    let isTopHospital: Bool
    let hospital: String
    let department: String
    let specialty: String
    let intro: String?  // 新增字段
    let rating: Double
    let monthlyAnswers: Int
    let avgResponseTime: String
    
    // UI 展示用字段（使用默认值，后端可扩展）
    var badges: [String] { [] }
    var textPrice: Double { 99 }
    var phonePrice: Double? { nil }
    var videoPrice: Double? { nil }
    var avatarColor: Color {
        let colors: [Color] = [.blue, .purple, .pink, .orange, .green, .cyan]
        return colors[doctorId % colors.count].opacity(0.3)
    }
    var hasRecommendBadge: Bool { doctorId % 2 == 0 }
    
    // 从 API 模型初始化
    init(from model: DoctorModel, departmentName: String) {
        self.doctorId = model.id
        self.name = model.name
        self.title = model.title ?? "主治医师"
        self.canPrescribe = model.can_prescribe
        self.isTopHospital = model.is_top_hospital
        self.hospital = model.hospital ?? "未知医院"
        self.department = departmentName
        self.specialty = model.specialty ?? ""
        self.intro = model.intro  // 新增
        self.rating = model.rating
        self.monthlyAnswers = model.monthly_answers
        self.avgResponseTime = model.avg_response_time
    }
}
```

### 修改2：DoctorChatView.swift - DoctorInfoCardView的Tab内容

```swift
// Tab内容
VStack(alignment: .leading, spacing: 8) {
    if selectedTab == 0 {
        // 专业擅长 - 使用后端specialty字段
        Text(doctor.specialty.isEmpty ? "暂无专长信息" : doctor.specialty)
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    } else if selectedTab == 1 {
        // 团队简介 - 使用后端intro字段
        Text(doctor.intro ?? "由多位资深\(doctor.department)专家知识库训练的AI智能体，专注于\(doctor.department)领域疾病的诊断、治疗建议和健康管理。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    } else {
        // 获奖荣誉 - AI智能体的特点描述
        Text("基于权威医学知识库和临床指南训练，持续学习最新医学研究成果，为您提供专业、及时的医疗咨询服务。")
            .font(.system(size: 14))
            .foregroundColor(DXYColors.textSecondary)
            .lineLimit(5)
    }
}
.frame(maxWidth: .infinity, alignment: .leading)
```

## 测试验证

修改完成后，请验证：

1. ✅ 皮肤科显示"皮肤科AI智能体"
2. ✅ 专业擅长显示完整的specialty内容
3. ✅ 团队简介显示intro字段内容
4. ✅ 所有科室都显示对应的AI智能体名称
5. ✅ 医院名称显示"心灵医生AI智能诊疗平台"

## 注意事项

1. **向后兼容**：使用 `??` 提供默认值，确保即使后端数据缺失也能正常显示
2. **行数限制**：将 `lineLimit` 从3改为5，因为AI智能体的介绍文本较长
3. **空值处理**：specialty为空时显示"暂无专长信息"，intro为空时使用默认模板
4. **一致性**：确保所有显示的信息都来自后端API，不再使用硬编码文本

## 相关文件

- `/Users/zhuxinye/Desktop/project/home-health/ios/xinlingyisheng/xinlingyisheng/Views/DepartmentDetailView.swift`
- `/Users/zhuxinye/Desktop/project/home-health/ios/xinlingyisheng/xinlingyisheng/Views/DoctorChatView.swift`
- `/Users/zhuxinye/Desktop/project/home-health/ios/xinlingyisheng/xinlingyisheng/Models/APIModels.swift`
