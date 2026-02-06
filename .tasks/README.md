# 项目任务管理系统

## 概述

这是 **Home-Health (灵犀医生)** 项目的任务管理目录。

## 角色分工

| 角色 | 职责 |
|------|------|
| **领导者** | 分配任务、确认任务、验收结果 |
| **技术助手 (Claude)** | 诊断问题、创建任务、分配 Agent、验收结果 |
| **Agent** | 执行具体子任务 |

## 工作流程

```
发现问题
    ↓
技术助手诊断（查代码、看日志）
    ↓
创建任务文件 (.tasks/TASK-XXX/task.md)
    ↓
领导者确认任务
    ↓
分配给 Agent 执行
    ↓
验收结果
    ↓
更新任务状态
```

## 任务状态

- 📋 **PENDING** - 待确认
- ✅ **CONFIRMED** - 已确认，待分配
- 🔄 **IN_PROGRESS** - 执行中
- ✅ **COMPLETED** - 已完成
- ❌ **FAILED** - 失败
- ⏸️ **BLOCKED** - 阻塞中

## 目录结构

```
.tasks/
├── README.md              # 本文件
├── TASK-STATUS.md         # 状态跟踪
└── TASK-XXX/              # 具体任务
    ├── task.md            # 任务描述
    ├── result.md          # 执行结果
    └── artifacts/         # 产出物
```

## 当前任务

详见 [TASK-STATUS.md](./TASK-STATUS.md)
