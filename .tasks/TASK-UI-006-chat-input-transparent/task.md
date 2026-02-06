# TASK-UI-006: 对话页面输入框透明问题修复

## 状态
📋 待分配

## 优先级
P0 - UI 显示问题

## 组件
ios/

---

## 问题描述

智能体对话页面（ModernConsultationView）底部的消息输入框背景是半透明的，用户无法清楚看到输入框的边界。

---

## 根本原因

**文件**: `ios/xinlingyisheng/xinlingyisheng/Views/WeChatStyleInputBar.swift`

**位置**: 第 200-213 行

```swift
.background(
    RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
        .fill(HealingColors.warmCream.opacity(0.5))  // ← 50% 透明度
        .overlay(
            RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.3), lineWidth: 1)
        )
        .shadow(
            color: HealingColors.softSage.opacity(0.1),
            radius: 8,
            x: 0,
            y: 2
        )
)
```

**问题**: 背景色设置为 `.opacity(0.5)` = 50% 透明，导致输入框看起来透明

---

## 修复方案

将背景色从 `HealingColors.warmCream.opacity(0.5)` 改为完全不透明：

```swift
// 修改前
.fill(HealingColors.warmCream.opacity(0.5))

// 修改后
.fill(HealingColors.warmCream)
```

---

## 完整修改后的代码

```swift
.background(
    RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
        .fill(HealingColors.warmCream)  // ← 移除 .opacity(0.5)
        .overlay(
            RoundedRectangle(cornerRadius: ScaleFactor.size(24), style: .continuous)
                .stroke(HealingColors.softSage.opacity(0.5), lineWidth: 1)  // 边框加深
        )
        .shadow(
            color: HealingColors.softSage.opacity(0.2),
            radius: 8,
            x: 0,
            y: 2
        )
)
```

---

## 验收标准

- [ ] 对话页面输入框背景不再透明
- [ ] 输入框有清晰的奶白色背景
- [ ] 边框清晰可见
- [ ] iOS 编译成功 (`BUILD SUCCEEDED`)

---

## 测试场景

| 场景 | 预期行为 |
|------|----------|
| 打开智能体对话页面 | 底部输入框有清晰的不透明背景 |
| 点击输入框 | 输入框背景保持不透明 |
| 输入文字 | 文字在输入框中清晰可见 |

---

## 影响文件

- `ios/xinlingyisheng/xinlingyisheng/Views/WeChatStyleInputBar.swift`

---

## 验证命令

```bash
cd ios/xinlingyisheng
xcodebuild -project xinlingyisheng.xcodeproj -scheme 灵犀医生 \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' build
```

预期输出: `** BUILD SUCCEEDED **`

---

## 相关任务

- TASK-UI-004: 登录页输入框透明问题修复（类似问题，不同文件）
