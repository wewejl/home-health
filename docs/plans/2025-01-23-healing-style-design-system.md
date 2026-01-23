# 治愈系日式诊所风格 - 设计系统规范

> **版本**: v1.0
> **更新日期**: 2025-01-23
> **适用范围**: 鑼琳医生 iOS 应用

## 设计理念

治愈系日式诊所风格旨在为医疗健康应用创造一个**温暖、安全、专业**的视觉体验。通过柔和的色彩、圆润的造型和细腻的交互，降低用户的焦虑感，传递可信赖的医疗专业性。

**核心价值**:
- **温暖感** - 使用奶油色、陶土色等温暖色调
- **安心感** - 圆润造型、柔和过渡、呼吸感动画
- **专业感** - 清晰的层级、一致的对齐、适度的留白

---

## 1. 色彩系统

### 1.1 主色系 - 鼠尾草绿（治愈绿）

| 色彩名称 | RGB | Hex | 用途 |
|---------|-----|-----|------|
| `softSage` | (0.71, 0.82, 0.76) | #B5D1C2 | 装饰背景、浅色强调 |
| `deepSage` | (0.45, 0.62, 0.54) | #739E89 | 次要按钮、渐变终点 |
| `forestMist` | (0.32, 0.48, 0.42) | #517A6B | 主操作色、重要强调 |

```swift
HealingColors.softSage    // 浅鼠尾草绿 - 装饰背景
HealingColors.deepSage    // 深鼠尾草绿 - 渐变终点
HealingColors.forestMist   // 森林雾绿 - 主操作色
```

### 1.2 温暖色系 - 奶油与陶土

| 色彩名称 | RGB | Hex | 用途 |
|---------|-----|-----|------|
| `warmCream` | (0.97, 0.95, 0.91) | #F7F2E8 | 页面主背景 |
| `softPeach` | (0.96, 0.90, 0.85) | #F5E6D9 | 渐变叠加层 |
| `terracotta` | (0.82, 0.52, 0.42) | #D1856B | 错误提示、警告 |
| `warmSand` | (0.88, 0.82, 0.74) | #E0D2BD | 次要背景、输入框 |

```swift
HealingColors.warmCream    // 奶油白 - 主背景
HealingColors.softPeach    // 柔桃色 - 渐变叠加
HealingColors.terracotta   // 陶土红 - 警告/错误
HealingColors.warmSand     // 暖沙色 - 次要背景
```

### 1.3 点缀色系

| 色彩名称 | RGB | Hex | 用途 |
|---------|-----|-----|------|
| `mutedCoral` | (0.90, 0.62, 0.55) | #E69E8D | AI分析标签 |
| `dustyBlue` | (0.65, 0.72, 0.80) | #A6B8CC | 症状标签、链接 |
| `lavenderHaze` | (0.78, 0.73, 0.85) | #C7BAD9 | 紫色标签 |

```swift
HealingColors.mutedCoral   // 柔和珊瑚 - AI分析
HealingColors.dustyBlue    // 尘灰蓝 - 症状/链接
HealingColors.lavenderHaze // 薰衣雾 - 紫色
```

### 1.4 功能色

| 色彩名称 | RGB | Hex | 用途 |
|---------|-----|-----|------|
| `textPrimary` | (0.22, 0.22, 0.20) | #383833 | 主要文本、标题 |
| `textSecondary` | (0.42, 0.42, 0.40) | #6B6B66 | 次要文本、说明 |
| `textTertiary` | (0.62, 0.62, 0.60) | #9E9E99 | 辅助文本、占位符 |
| `background` | = warmCream | - | 页面背景 |
| `cardBackground` | (1.00, 1.00, 1.00) | #FFFFFF | 卡片背景 |

### 1.5 色彩使用规则

**渐变使用**:
- 主按钮: `LinearGradient([forestMist, deepSage], ...)`
- 卡片激活状态: 使用 forestMist 的渐变

**透明度使用**:
- 装饰光晕: `opacity(0.04 - 0.08)`
- 按钮禁用态: `opacity(0.5)`
- 辅助背景: `opacity(0.1 - 0.2)`

---

## 2. 布局系统

### 2.1 屏幕尺寸适配

```swift
struct AdaptiveLayout {
    let screenWidth: CGFloat

    // 屏幕分类
    isCompact: Bool   // < 380pt (iPhone SE)
    isRegular: Bool  // 380-400pt (iPhone 13/14)
    isLarge: Bool     // > 400pt (Pro Max)

    // 间距缩放
    paddingScale: CGFloat     // 0.8 / 1.0 / 1.2
    iconScale: CGFloat        // 0.85 / 1.0 / 1.1
}
```

### 2.2 标准间距值

| 属性名 | Compact | Regular | Large | 用途 |
|--------|---------|---------|-------|------|
| `cardSpacing` | 12 | 16 | 20 | 卡片垂直间距 |
| `horizontalPadding` | 16 | 20 | 24 | 页面水平内边距 |
| `cardInnerPadding` | 12 | 16 | 18 | 卡片内边距 |

### 2.3 圆角规范

| 组件类型 | 圆角值 | 样式 |
|---------|--------|------|
| 卡片/按钮 | 18pt | `.continuous` |
| 输入框 | 12-14pt | `.continuous` |
| 小组件 | 8-10pt | `.continuous` |
| 圆形按钮/图标 | 直径的一半 | - |

```swift
.clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
```

---

## 3. 字体系统

### 3.1 字号规范

| 字体名 | Compact | Regular | Large | 用途 |
|--------|---------|---------|-------|------|
| `titleFontSize` | 18 | 20 | 22 | 页面大标题 |
| `bodyFontSize` | 15 | 17 | 18 | 正文内容 |
| `captionFontSize` | 11 | 12 | 13 | 辅助说明 |

### 3.2 字重使用

- **Bold (`.semibold`)**: 页面标题、按钮文本
- **Medium**: 卡片标题、标签
- **Regular**: 正文内容
- **Light**: 装饰性元素

---

## 4. 组件规范

### 4.1 卡片组件

**结构**:
```
┌─────────────────────────────────┐
│  [图标] 标题                      │  ← 标题栏
├─────────────────────────────────┤
│                                  │
│  内容区域                        │  ← 内容
│                                  │
└─────────────────────────────────┘
```

**样式规范**:
- 背景: `HealingColors.cardBackground` (白色)
- 阴影: `Color.black.opacity(0.04), radius: 8, y: 2`
- 边框: `HealingColors.softSage.opacity(0.2), lineWidth: 1`
- 内边距: `layout.cardInnerPadding`

### 4.2 按钮组件

**主按钮**:
```swift
.background(
    LinearGradient(
        colors: [HealingColors.forestMist, HealingColors.deepSage],
        startPoint: .leading,
        endPoint: .trailing
    )
)
.clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
.shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 2)
```

**次要按钮**:
```swift
.background(HealingColors.cardBackground)
.clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
.overlay(stroke: HealingColors.forestMist.opacity(0.5), lineWidth: 1.5)
```

### 4.3 图标按钮

```swift
ZStack {
    Circle()
        .fill(HealingColors.forestMist.opacity(0.15))
        .frame(width: 44, height: 44)

    Image(systemName: "icon.name")
        .font(.system(size: 18))
        .foregroundColor(HealingColors.forestMist)
}
```

---

## 5. 背景设计

### 5.1 标准页面背景

```swift
ZStack {
    // 渐变底色
    LinearGradient(
        colors: [
            HealingColors.warmCream,
            HealingColors.softPeach.opacity(0.4),
            HealingColors.softSage.opacity(0.2)
        ],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
    .ignoresSafeArea()

    // 装饰光晕
    GeometryReader { geo in
        Circle()
            .fill(HealingColors.softSage.opacity(0.08))
            .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
            .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)

        Circle()
            .fill(HealingColors.mutedCoral.opacity(0.04))
            .frame(width: layout.decorativeCircleSize * 0.4, height: layout.decorativeCircleSize * 0.4)
            .offset(x: -geo.size.width * 0.4, y: geo.size.height * 0.2)
    }
}
```

---

## 6. 动画规范

### 6.1 标准动画参数

```swift
// 弹簧动画
.animation(.spring(response: 0.3, dampingFraction: 0.8), value: animatedValue)

// 渐入渐出
.animation(.easeInOut(duration: 0.2), value: isVisible)

// 呼吸效果
.animation(.spring(response: 0.4, dampingFraction: 0.7), value: isPresented)
```

### 6.2 加载动画

使用呼吸动画:
```swift
Circle()
    .fill(HealingColors.forestMist.opacity(0.1))
    .frame(width: 50 + CGFloat(sin(Date().timeIntervalSince1970) * 10) * 10)
    .animation(.easeInOut(duration: 1).repeatForever(autoreverses: true), value: true)
```

---

## 7. 状态处理

### 7.1 加载状态

```swift
VStack(spacing: layout.cardSpacing) {
    ProgressView().tint(HealingColors.forestMist)
    Text("加载中...")
        .font(.system(size: layout.captionFontSize + 1))
        .foregroundColor(HealingColors.textSecondary)
}
```

### 7.2 空状态

```swift
VStack(spacing: layout.cardSpacing) {
    Image(systemName: "doc.text.fill")
        .font(.system(size: layout.bodyFontSize + 8, weight: .light))
        .foregroundColor(HealingColors.textTertiary)

    Text("暂无内容")
        .font(.system(size: layout.bodyFontSize + 1, weight: .semibold))
        .foregroundColor(HealingColors.textPrimary)
}
```

### 7.3 错误状态

```swift
Image(systemName: "exclamationmark.triangle")
    .foregroundColor(HealingColors.terracotta)

Text("错误信息")
    .foregroundColor(HealingColors.terracotta)
```

---

## 8. 代码模板

### 8.1 页面模板

```swift
struct YourHealingStyleView: View {
    var body: some View {
        GeometryReader { geometry in
            let layout = AdaptiveLayout(screenWidth: geometry.size.width)

            ZStack {
                // 治愈系背景
                HealingYourBackground(layout: layout)

                VStack(spacing: layout.cardSpacing) {
                    // 内容
                }
                .padding(.horizontal, layout.horizontalPadding)
            }
        }
    }
}
```

### 8.2 卡片标题栏模板

```swift
HStack(spacing: layout.cardSpacing / 3) {
    ZStack {
        Circle()
            .fill(HealingColors.forestMist.opacity(0.15))
            .frame(width: 32, height: 32)

        Image(systemName: "icon.name")
            .font(.system(size: 14))
            .foregroundColor(HealingColors.forestMist)
    }

    Text("标题")
        .font(.system(size: layout.bodyFontSize, weight: .semibold))
        .foregroundColor(HealingColors.textPrimary)
}
```

---

## 9. 命名约定

### 9.1 组件命名

治愈系组件使用 `Healing` 前缀:
```swift
HealingEventDetailBackground
HealingExportScopeCard
HealingPDFViewerInfoBar
```

### 9.2 文件组织

```
Views/HealingStyle/
├── Backgrounds/         # 背景组件
├── Cards/               # 卡片组件
├── Buttons/             # 按钮组件
├── Status/              # 状态视图
└── Templates/           # 页面模板
```

---

## 10. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2025-01-23 | 初始版本，定义治愈系日式诊所风格 |

---

## 附录：快速参考

### 常用代码片段

**渐变主按钮**:
```swift
.background(
    LinearGradient(
        colors: [HealingColors.forestMist, HealingColors.deepSage],
        startPoint: .leading,
        endPoint: .trailing
    )
)
.clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
.shadow(color: HealingColors.forestMist.opacity(0.3), radius: 6, y: 2)
```

**图标按钮**:
```swift
Button(action: action) {
    ZStack {
        Circle()
            .fill(HealingColors.forestMist.opacity(0.15))
            .frame(width: 44, height: 44)
        Image(systemName: "icon.name")
            .foregroundColor(HealingColors.forestMist)
    }
}
```

**装饰光晕背景**:
```swift
GeometryReader { geo in
    Circle()
        .fill(HealingColors.softSage.opacity(0.08))
        .frame(width: layout.decorativeCircleSize * 0.5, height: layout.decorativeCircleSize * 0.5)
        .offset(x: geo.size.width * 0.3, y: -geo.size.height * 0.15)
}
```
