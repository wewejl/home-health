# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **数据库清理脚本** (`backend/scripts/cleanup_incomplete_events.py`)
  - 支持 `--full` 完全清理模式
  - 正确处理外键约束，按顺序删除关联表
  - 支持 `--dry-run` 预览模式和 `--stats` 统计模式

- **聚合接口数据完整性验证** (`backend/app/routes/medical_events.py`)
  - 检查 chief_complaint（主诉）是否存在
  - 检查 symptoms（症状列表）是否为空
  - 检查对话阶段（greeting/collecting）
  - 提供详细的错误信息，列出具体缺少哪些信息

- **iOS 客户端智能病历按钮** (`ios/xinlingyisheng/`)
  - `canGenerateDossier` 计算属性（至少需要5条消息）
  - `requestGenerateDossier` 方法，对话较少时显示确认对话框
  - `ChatNavBarV2` 按钮禁用状态和动态颜色
  - 确认对话框提示用户对话较少可能导致病历不够详细

- **会话数据流全局分析文档** (`docs/architecture/会话数据流全局分析.md`)
  - 详细说明 agent_state 的存储位置和结构
  - 完整的18步数据流图
  - 关键代码路径说明

### Changed
- **聚合验证逻辑改进** - 提供更友好的错误提示，明确指出缺少哪些信息
- **API契约文档更新** - 补充聚合接口的错误响应说明

### Fixed
- **修复过早聚合导致病历信息不完整的问题** - 后端验证确保信息收集完整后才允许生成病历
- **修复 iOS Preview 代码中的类型错误** - eventId 从 Int 改为 String
- **清理旧的测试数据和空壳病历事件** - 执行完全数据库清理

### Removed
- **删除旧会话表数据** - 清空 derma_sessions 和 diagnosis_sessions 表
- **删除不完整的病历事件** - 清理无主诉、无症状的空壳事件

## [1.0.0] - 2026-01-15

### Added
- 初始版本
- 统一会话架构（sessions 表 + agent_state JSON 字段）
- 多科室智能体支持（皮肤科、心血管科、骨科等）
- iOS 客户端统一聊天界面
- 病历事件管理功能
