# 状态: 已完成

# 语音模式专业版实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现完整的语音模式功能，包括语音识别、语音播报、智能打断和图片上传

**Architecture:** 三层架构（View → ViewModel → Services），使用原生 Speech Framework 和 AVFoundation

**Tech Stack:** Swift, SwiftUI, Speech Framework, AVFoundation, Combine

---

## 功能需求

### 底部按钮（4个）
1. **麦克风** - 控制用户麦克风开关（静音/取消静音）
2. **拍照** - 直接打开相机
3. **相册** - 打开照片选择器
4. **退出** - 关闭语音模式

### 核心功能
- 语音识别：实时语音转文字
- 语音播报：AI回复自动播报
- 智能打断：检测到用户说话时自动停止AI播报
- 与后端集成：通过 UnifiedChatViewModel 发送/接收消息

---

## Task 1: 创建 VoiceActivityDetector 智能打断检测服务

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/Services/VoiceActivityDetector.swift`

**实现内容:**
- 使用 AVAudioEngine 实时监听麦克风音量
- 检测用户是否开始说话
- 触发打断回调

---

## Task 2: 增强 RealtimeSpeechService

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Services/RealtimeSpeechService.swift`

**实现内容:**
- 添加 pauseRecognition() 方法
- 添加 resumeRecognition() 方法
- 优化音频会话配置

---

## Task 3: 增强 SpeechSynthesisService

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Services/SpeechSynthesisService.swift`

**实现内容:**
- 添加 onInterrupted 回调
- 添加 pause/resume 方法

---

## Task 4: 创建 VoiceModeViewModel

**Files:**
- Create: `ios/xinlingyisheng/xinlingyisheng/ViewModels/VoiceModeViewModel.swift`

**实现内容:**
- 统一管理语音模式状态
- 协调语音识别、播报和打断检测服务
- 与 UnifiedChatViewModel 集成

---

## Task 5: 重构 FullScreenVoiceModeView

**Files:**
- Modify: `ios/xinlingyisheng/xinlingyisheng/Views/FullScreenVoiceModeView.swift`

**实现内容:**
- 修改按钮布局：麦克风、拍照、相册、退出
- 集成 VoiceModeViewModel
- 更新状态显示

---

## Task 6-10: 功能集成和测试

依次完成麦克风控制、图片功能、智能打断、后端集成和测试修复。
