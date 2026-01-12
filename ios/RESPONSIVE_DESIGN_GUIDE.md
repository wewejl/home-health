# iOS 响应式设计指南

## 概述

本项目采用 **基于屏幕宽度比例的缩放系统**，这是 Apple 推荐的响应式设计方法。系统会根据设备屏幕宽度自动缩放所有 UI 元素，确保在不同尺寸的 iPhone 上都有一致的视觉体验。

## 设计原理

### 基准设备
- **基准设备**: iPhone 14 Pro Max (430pt 宽度)
- **缩放比例**: 当前设备宽度 / 430pt

### 设备缩放比例示例
| 设备 | 宽度 | 缩放比例 |
|------|------|----------|
| iPhone SE | 320pt | 0.744 (74.4%) |
| iPhone 12/13 mini | 360pt | 0.837 (83.7%) |
| iPhone 14 | 390pt | 0.907 (90.7%) |
| iPhone 14 Plus | 414pt | 0.963 (96.3%) |
| iPhone 14 Pro Max | 430pt | 1.000 (100%) |

## 核心 API

### 1. ScaleFactor - 缩放因子

```swift
// 获取当前设备的缩放比例
let scale = ScaleFactor.width  // 例如 iPhone 14 返回 0.907

// 缩放字体
let fontSize = ScaleFactor.font(16)  // iPhone 14: 14.5pt

// 缩放尺寸
let iconSize = ScaleFactor.size(24)  // iPhone 14: 21.8pt

// 缩放间距
let spacing = ScaleFactor.spacing(16)  // iPhone 14: 14.5pt

// 缩放内边距
let padding = ScaleFactor.padding(20)  // iPhone 14: 18.1pt
```

### 2. AdaptiveFont - 自适应字体

预定义的字体大小，自动适配所有设备：

```swift
// 使用预定义字体
Text("标题")
    .font(.system(size: AdaptiveFont.title1))  // 基准 24pt

Text("正文")
    .font(.system(size: AdaptiveFont.body))    // 基准 16pt

Text("说明")
    .font(.system(size: AdaptiveFont.caption)) // 基准 11pt
```

**可用字体大小**:
- `largeTitle`: 28pt (基准)
- `title1`: 24pt
- `title2`: 20pt
- `title3`: 18pt
- `body`: 16pt
- `subheadline`: 14pt
- `footnote`: 12pt
- `caption`: 11pt
- `custom(size)`: 自定义大小

### 3. AdaptiveSize - 自适应尺寸

预定义的尺寸，用于图标、按钮、圆角等：

```swift
// 图标尺寸
Image(systemName: "heart.fill")
    .font(.system(size: AdaptiveSize.iconMedium))  // 基准 24pt

// 按钮高度
Button("确定") { }
    .frame(height: AdaptiveSize.buttonHeight)      // 基准 48pt

// 圆角
RoundedRectangle(cornerRadius: AdaptiveSize.cornerRadius)  // 基准 16pt
```

**可用尺寸**:
- `iconSmall`: 16pt
- `iconMedium`: 24pt
- `iconLarge`: 32pt
- `buttonHeight`: 48pt
- `buttonHeightSmall`: 40pt
- `cornerRadiusSmall`: 8pt
- `cornerRadius`: 16pt
- `cornerRadiusLarge`: 24pt
- `custom(size)`: 自定义尺寸

### 4. AdaptiveSpacing - 自适应间距

预定义的间距，用于布局：

```swift
VStack(spacing: AdaptiveSpacing.item) {  // 基准 16pt
    // 内容
}

.padding(AdaptiveSpacing.card)  // 基准 20pt
```

**可用间距**:
- `section`: 24pt (大区块间距)
- `item`: 16pt (列表项间距)
- `card`: 20pt (卡片内边距)
- `compact`: 8pt (紧凑间距)

## 使用示例

### 示例 1: 导航栏

```swift
struct CustomNavBar: View {
    var body: some View {
        HStack(spacing: ScaleFactor.spacing(12)) {
            // 返回按钮
            Button(action: {}) {
                Image(systemName: "chevron.left")
                    .font(.system(size: AdaptiveFont.title3))
            }
            
            // 标题
            Text("页面标题")
                .font(.system(size: AdaptiveFont.body, weight: .medium))
            
            Spacer()
            
            // 工具按钮
            Button(action: {}) {
                Image(systemName: "ellipsis")
                    .font(.system(size: AdaptiveFont.title3))
            }
        }
        .padding(.horizontal, ScaleFactor.padding(16))
        .padding(.vertical, ScaleFactor.padding(12))
    }
}
```

### 示例 2: 卡片组件

```swift
struct InfoCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: AdaptiveSpacing.item) {
            // 标题
            Text("卡片标题")
                .font(.system(size: AdaptiveFont.title2, weight: .bold))
            
            // 内容
            Text("卡片内容描述")
                .font(.system(size: AdaptiveFont.body))
                .foregroundColor(.secondary)
            
            // 按钮
            Button("查看详情") {}
                .frame(height: AdaptiveSize.buttonHeight)
        }
        .padding(AdaptiveSpacing.card)
        .background(Color.white)
        .cornerRadius(AdaptiveSize.cornerRadius)
    }
}
```

### 示例 3: 图标和文字组合

```swift
HStack(spacing: AdaptiveSpacing.compact) {
    Image(systemName: "star.fill")
        .font(.system(size: AdaptiveSize.iconSmall))
    
    Text("评分 4.8")
        .font(.system(size: AdaptiveFont.footnote))
}
```

## 迁移现有代码

### 替换硬编码值

**之前**:
```swift
Text("标题")
    .font(.system(size: 20))
    .padding(.horizontal, 16)

Circle()
    .frame(width: 32, height: 32)

VStack(spacing: 12) { }
```

**之后**:
```swift
Text("标题")
    .font(.system(size: AdaptiveFont.title2))
    .padding(.horizontal, ScaleFactor.padding(16))

Circle()
    .frame(width: ScaleFactor.size(32), height: ScaleFactor.size(32))

VStack(spacing: ScaleFactor.spacing(12)) { }
```

### 替换条件判断

**之前**:
```swift
private var fontSize: CGFloat {
    if DeviceType.isVeryCompactWidth { return 14 }
    if DeviceType.isCompactWidth { return 15 }
    return 16
}
```

**之后**:
```swift
private var fontSize: CGFloat {
    AdaptiveFont.body  // 自动适配所有设备
}
```

## 最佳实践

### ✅ 推荐做法

1. **使用预定义的字体和尺寸**
   ```swift
   .font(.system(size: AdaptiveFont.body))
   ```

2. **所有尺寸都使用缩放**
   ```swift
   .frame(width: ScaleFactor.size(100), height: ScaleFactor.size(50))
   ```

3. **间距使用 AdaptiveSpacing 或 ScaleFactor**
   ```swift
   VStack(spacing: AdaptiveSpacing.item) { }
   .padding(ScaleFactor.padding(16))
   ```

### ❌ 避免做法

1. **不要硬编码数值**
   ```swift
   // ❌ 错误
   .font(.system(size: 16))
   .padding(20)
   
   // ✅ 正确
   .font(.system(size: AdaptiveFont.body))
   .padding(ScaleFactor.padding(20))
   ```

2. **不要使用复杂的条件判断**
   ```swift
   // ❌ 错误
   if DeviceType.isVeryCompactWidth { return 14 }
   else if DeviceType.isCompactWidth { return 15 }
   else { return 16 }
   
   // ✅ 正确
   AdaptiveFont.body
   ```

3. **不要混用缩放和固定值**
   ```swift
   // ❌ 错误
   .padding(.horizontal, ScaleFactor.padding(16))
   .padding(.vertical, 12)  // 固定值
   
   // ✅ 正确
   .padding(.horizontal, ScaleFactor.padding(16))
   .padding(.vertical, ScaleFactor.padding(12))
   ```

## 特殊情况处理

### 最小触摸目标

Apple 建议最小触摸目标为 44pt。对于按钮等交互元素：

```swift
Button("点击") {}
    .frame(minWidth: 44, minHeight: 44)  // 保持最小触摸目标
    .font(.system(size: AdaptiveFont.body))
```

### 固定尺寸元素

某些元素（如分隔线）可能需要固定尺寸：

```swift
// 1pt 分隔线在所有设备上保持 1pt
Divider()
    .frame(height: 1)
```

### 图片和图标

```swift
// SF Symbols 自动缩放
Image(systemName: "heart.fill")
    .font(.system(size: AdaptiveSize.iconMedium))

// 自定义图片
Image("logo")
    .resizable()
    .frame(width: ScaleFactor.size(80), height: ScaleFactor.size(80))
```

## 调试技巧

### 查看当前缩放比例

```swift
Text("缩放比例: \(ScaleFactor.width)")
Text("设备宽度: \(DeviceType.screenWidth)")
```

### 预览不同设备

在 Xcode Preview 中测试多个设备：

```swift
struct MyView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            MyView()
                .previewDevice("iPhone SE (3rd generation)")
                .previewDisplayName("iPhone SE")
            
            MyView()
                .previewDevice("iPhone 14")
                .previewDisplayName("iPhone 14")
            
            MyView()
                .previewDevice("iPhone 14 Pro Max")
                .previewDisplayName("iPhone 14 Pro Max")
        }
    }
}
```

## 已应用页面

- ✅ `DoctorChatView` - ChatNavBar 已完全迁移
- ⏳ 其他页面待迁移

## 总结

使用这套响应式缩放系统的优势：

1. **一致性**: 所有设备上保持相同的视觉比例
2. **可维护性**: 统一的 API，易于理解和修改
3. **官方推荐**: 符合 Apple 的响应式设计最佳实践
4. **自动适配**: 无需为每个设备单独调整
5. **易于迁移**: 简单替换硬编码值即可

记住：**所有尺寸、字体、间距都应该使用缩放系统**，这样才能确保在所有 iPhone 设备上都有完美的显示效果。
