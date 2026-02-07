# 医嘱任务页面 UI 重构设计

> 创建日期：2026-02-07
> 状态：✅ 已完成

---

## 一、需求概述

重构医嘱任务模块的 UI 设计，使其更符合护理任务的实际使用场景。

### 核心问题
- 当前任务列表页的大日历占用过多空间
- 任务完成页面的打卡方式过于复杂

### 重构范围
| 页面 | 改动 |
|------|------|
| **任务列表页** | 移除大日历，改用横向日期条 |
| **任务完成页** | 简化为：任务信息 → 拍照（可选）→ 语音描述（必须）→ 完成 |

---

## 二、任务列表页设计

### 2.1 页面布局

```
┌─────────────────────────────────────────┐
│  医嘱任务                    🔔 预警     │  ← 顶部标题
├─────────────────────────────────────────┤
│  今日完成率: 75%  已完成:3  待完成:1     │  ← 统计卡片
├─────────────────────────────────────────┤
│  < 2/6 周三 | 2/7 周四 | 2/8 周五 >     │  ← 横向日期条
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 📋 擦碘伏            08:00      │   │  ← 待完成任务
│  │    用药                        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ✅ 测量血糖          12:00      │   │  ← 已完成任务
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### 2.2 横向日期条组件

```swift
// 组件位置：ios/.../Views/HorizontalDatePicker.swift

struct HorizontalDatePicker: View {
    @Binding var selectedDate: Date

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(generateDates(), id: \.self) { date in
                    DateChip(date: date, isSelected: isSameDay(date, selectedDate))
                        .onTapGesture { selectedDate = date }
                }
            }
            .padding(.horizontal)
        }
    }
}

struct DateChip: View {
    let date: Date
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 4) {
            Text(monthDay)        // "2/7"
                .font(.caption2)
            Text(weekday)         // "周四"
                .font(.caption)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(isSelected ? Color.green : Color.gray.opacity(0.1))
        .foregroundColor(isSelected ? .white : .gray)
        .cornerRadius(12)
    }
}
```

### 2.3 移除的代码

```swift
// 删除文件中第 144-152 行的大日历
// DatePicker("", selection: $viewModel.selectedDate, displayedComponents: .date)
//     .datePickerStyle(.graphical)
//     .frame(height: layout.isCompact ? 300 : 350)
```

---

## 三、任务完成页设计

### 3.1 页面布局

```
┌─────────────────────────────────────────┐
│  < 完成任务                    取消      │  ← 导航栏
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 💊 擦碘伏                       │   │  ← 任务名称
│  │                                 │   │
│  │ 医嘱内容：                      │   │
│  │ 每日三次，用棉签蘸取碘伏        │   │  ← 医嘱内容
│  │ 轻轻擦拭伤口处                 │   │
│  │                                 │   │
│  │ 计划时间：08:00                │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │                                 │   │
│  │     [📷 拍照证明]               │   │  ← 拍照（可选）
│  │     点击拍摄或选择照片          │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  🎤 按住说话，描述症状/状态      │   │  ← 语音描述（必须）
│  │                                 │   │
│  │  已转文字内容：                  │   │
│  │  "已按时擦药，伤口恢复良好..."  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      ✅ 完成任务                 │   │  ← 提交按钮
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### 3.2 组件结构

```swift
// 文件：ios/.../Views/SimplifiedTaskCompletionView.swift

struct SimplifiedTaskCompletionView: View {
    let task: TaskInstance
    @State private var selectedImage: Image? = nil
    @State private var voiceText: String = ""
    @State private var isRecording: Bool = false
    @State private var isSubmitting: Bool = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // 1. 任务信息卡片
                TaskInfoCard(task: task)

                // 2. 拍照区域（可选）
                PhotoProofSection(image: $selectedImage)

                // 3. 语音描述（必须）
                VoiceDescriptionSection(
                    text: $voiceText,
                    isRecording: $isRecording
                )

                // 4. 完成按钮
                CompleteButton(
                    isDisabled: voiceText.isEmpty,
                    isLoading: isSubmitting
                ) {
                    submitTask()
                }
            }
            .padding()
        }
    }
}
```

### 3.3 各区域设计

#### 3.3.1 任务信息卡片

```swift
struct TaskInfoCard: View {
    let task: TaskInstance

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 任务标题
            HStack {
                Image(systemName: task.typeIcon)
                Text(task.order_title ?? "任务")
                    .font(.headline)
                Spacer()
                Text(task.scheduled_time)
                    .font(.caption)
                    .foregroundColor(.gray)
            }

            // 医嘱内容
            VStack(alignment: .leading, spacing: 4) {
                Text("医嘱内容")
                    .font(.caption)
                    .foregroundColor(.gray)
                Text(task.description ?? "无详细说明")
                    .font(.body)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(16)
    }
}
```

#### 3.3.2 拍照区域（可选）

```swift
struct PhotoProofSection: View {
    @Binding var image: Image?
    @State private var pickerItems: [PhotosPickerItem] = []

    var body: some View {
        VStack(spacing: 12) {
            Text("拍照证明（可选）")
                .font(.subheadline)
                .foregroundColor(.gray)

            if let image = image {
                // 已选照片预览
                image
                    .resizable()
                    .scaledToFill()
                    .frame(height: 200)
                    .cornerRadius(12)
                    .overlay(
                        Button("删除") { image = nil }
                            .padding(8)
                            .background(Color.red)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        , alignment: .topTrailing
                    )
            } else {
                // 拍照按钮
                PhotosPicker(selection: $pickerItems, matching: .images) {
                    VStack(spacing: 8) {
                        Image(systemName: "camera.fill")
                            .font(.title2)
                        Text("点击拍照或选择照片")
                            .font(.caption)
                    }
                    .frame(height: 120)
                    .frame(maxWidth: .infinity)
                    .background(Color.gray.opacity(0.05))
                    .cornerRadius(12)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(16)
    }
}
```

#### 3.3.3 语音描述（必须）

```swift
struct VoiceDescriptionSection: View {
    @Binding var text: String
    @State var isRecording: Bool = false

    var body: some View {
        VStack(spacing: 12) {
            Text("症状/状态描述（必填）")
                .font(.subheadline)
                .foregroundColor(.gray)

            // 录音按钮
            Button {
                // 开始/停止录音
                isRecording.toggle()
            } label: {
                HStack {
                    Image(systemName: isRecording ? "stop.circle.fill" : "mic.circle.fill")
                        .font(.title2)
                    Text(isRecording ? "松开结束" : "按住说话")
                        .font(.body)
                }
                .foregroundColor(.white)
                .padding()
                .frame(maxWidth: .infinity)
                .background(isRecording ? Color.red : Color.green)
                .cornerRadius(12)
            }

            // 转文字结果
            if !text.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    Text("已转文字：")
                        .font(.caption)
                        .foregroundColor(.gray)
                    Text(text)
                        .font(.body)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.gray.opacity(0.05))
                        .cornerRadius(8)
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.05))
        .cornerRadius(16)
    }
}
```

#### 3.3.4 完成按钮

```swift
struct CompleteButton: View {
    let isDisabled: Bool
    let isLoading: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                if isLoading {
                    ProgressView()
                } else {
                    Image(systemName: "checkmark.circle.fill")
                    Text("完成任务")
                }
            }
            .foregroundColor(.white)
            .font(.headline)
            .padding()
            .frame(maxWidth: .infinity)
            .background(isDisabled ? Color.gray : Color.green)
            .cornerRadius(12)
        }
        .disabled(isDisabled)
    }
}
```

---

## 四、实现清单

### 4.1 任务列表页改造

| 序号 | 任务 | 文件 |
|------|------|------|
| 1 | 创建 `HorizontalDatePicker.swift` 组件 | 新建 |
| 2 | 修改 `MedicalOrderListView.swift` 移除大日历 | 修改 |
| 3 | 调整任务卡片样式，增大显示区域 | 修改 |
| 4 | 更新 ViewModel 的日期选择逻辑 | 修改 |

### 4.2 任务完成页改造

| 序号 | 任务 | 文件 |
|------|------|------|
| 1 | 创建 `SimplifiedTaskCompletionView.swift` | 新建 |
| 2 | 实现任务信息卡片组件 | 新建 |
| 3 | 实现拍照区域组件 | 新建 |
| 4 | 实现语音描述组件 | 新建 |
| 5 | 集成语音转文字服务（使用现有 ASR） | 修改 |
| 6 | 更新提交逻辑 | 修改 |
| 7 | 删除旧的 `TaskCheckInView.swift` | 删除 |

---

## 五、数据流

```
用户点击任务
    ↓
打开 SimplifiedTaskCompletionView
    ↓
┌─────────────────────────────────────┐
│ 1. 显示任务信息                      │
│    - 从 TaskInstance 获取           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. 用户拍照（可选）                  │
│    - 选择照片 → 预览                │
│    - 上传到服务器 → 获取 URL         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. 用户语音描述（必须）              │
│    - 按住录音 → 调用 ASR 服务        │
│    - 返回转文字结果                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. 点击完成按钮                      │
│    - 校验：语音描述不能为空          │
│    - 调用 API 提交完成记录            │
│    - 关闭页面，刷新列表              │
└─────────────────────────────────────┘
```

---

## 六、API 调用

### 6.1 提交任务完成

```swift
// 调用现有 API
POST /api/medical-orders/tasks/{task_id}/complete

{
    "completion_type": "photo",  // 或 "check"
    "photo_url": "https://...",  // 可选
    "notes": "已转文字的语音描述", // 必填
    "voice_data": { ... }         // 可选：音频数据
}
```

---

## 七、验收标准

- [x] 任务列表页：横版日期条正常工作，切换日期刷新任务
- [x] 任务列表页：任务卡片显示完整，可正常点击
- [x] 任务完成页：任务信息正确显示
- [x] 任务完成页：拍照可选，可正常选择和删除照片
- [x] 任务完成页：语音描述必须填，无文字时无法提交
- [x] 任务完成页：提交后列表刷新，任务状态更新
- [x] 语音转文字正常工作（使用现有 ASR 服务）

---

## 八、参考文件

- 现有实现：`ios/xinlingyisheng/xinlingyisheng/Views/MedicalOrderListView.swift`
- 现有实现：`ios/xinlingyisheng/xinlingyisheng/Views/TaskCheckInView.swift`
- 数据模型：`ios/xinlingyisheng/xinlingyisheng/Models/MedicalOrderModels.swift`
- 语音服务：`ios/xinlingyisheng/xinlingyisheng/Services/PressAndHoldVoiceService.swift`
