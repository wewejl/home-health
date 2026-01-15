# CrewAI Telemetry 超时问题修复指南

## 问题描述

CrewAI 默认启用遥测数据上报到 `telemetry.crewai.com:4319`，在网络受限环境下会导致：
- ❌ 每次 AI 对话增加 30 秒超时延迟
- ❌ 严重影响用户体验
- ❌ 浪费服务器资源

## 解决方案

### 1. 配置环境变量（必须）

在实际的 `.env` 文件中添加：

```bash
# CrewAI 配置
# 禁用遥测数据上报，避免网络超时影响性能
OTEL_SDK_DISABLED=true
```

### 2. 重启后端服务

```bash
# Docker 环境
docker-compose restart backend

# 本地开发环境
# 停止当前进程，然后重新启动
uvicorn app.main:app --reload
```

### 3. 验证修复

观察后端日志，确认不再出现：
```
HTTPSConnectionPool(host='telemetry.crewai.com', port=4319): Read timed out.
```

### 4. 性能对比

**修复前**：
- API 响应时间：正常时间 + 30秒
- 用户等待时间：极差

**修复后**：
- API 响应时间：正常（通常 2-5 秒）
- 用户等待时间：正常

## 已修改的文件

1. ✅ `.env.example` - 添加配置说明
2. ✅ `app/services/dermatology/derma_crew_service.py` - 关闭 verbose
3. ✅ `app/services/dermatology/derma_agents.py` - 关闭 verbose
4. ✅ `app/services/cardiology/cardio_crew_service.py` - 关闭 verbose
5. ✅ `app/services/cardiology/cardio_agents.py` - 关闭 verbose
6. ✅ `app/services/orthopedics/ortho_crew_service.py` - 关闭 verbose
7. ✅ `app/services/orthopedics/ortho_agents.py` - 关闭 verbose

## 注意事项

- 环境变量必须在 `.env` 文件中配置，`.env.example` 仅作为模板
- 修改后必须重启服务才能生效
- 如果使用 Docker，确保环境变量正确传递到容器内

## 参考文档

- [CrewAI Telemetry Documentation](https://docs.crewai.com/telemetry)
- [OpenTelemetry SDK Configuration](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/)
