# iOS 开发安全指南

> **更新日期**: 2026-02-13
> **适用版本**: iOS 14+

---

## 安全原则

### 1. 零硬编码
- ✅ 所有配置通过 xcconfig 或环境变量注入
- ✅ 敏感信息通过 Keychain 存储
- ❌ 禁止在代码中硬编码 Token、密钥、IP 地址

### 2. HTTPS Only
- ✅ 生产环境强制使用 HTTPS
- ✅ 开发环境使用自签名证书
- ❌ 禁止生产环境使用 HTTP

### 3. Token 安全
- ✅ Token 通过 HTTP Header 传递
- ✅ Token 存储在 Keychain 中
- ❌ 禁止 Token 在 URL 参数中传递

### 4. 错误处理
- ✅ 用户友好的错误消息
- ❌ 禁止在错误消息中泄露技术细节

---

## 配置管理

### 环境配置文件

| 环境 | 文件 | 说明 |
|------|------|------|
| 开发 | `config/Development.xcconfig` | 本地开发，可覆盖 |
| 预发布 | `config/Staging.xcconfig` | 测试环境 |
| 生产 | `config/Production.xcconfig` | 生产环境 |

### 本地配置

创建 `/tmp/ios-local.xcconfig`（不提交到 git）：

```xcconfig
AUTH_TOKEN = your_dev_token
API_BASE_URL = https://127.0.0.1:8100
```

---

## 安全检查清单

### 代码提交前

- [ ] 运行 `scripts/ios/verify-security.sh`
- [ ] 确认无硬编码敏感信息
- [ ] 确认 Token 不在 URL 中
- [ ] 确认使用 HTTPS

### 发布前

- [ ] 生产环境配置正确
- [ ] API_BASE_URL 已配置
- [ ] 调试日志已关闭
- [ ] 抓包测试通过

---

## 安全架构组件

### SecurityConfig
集中式安全配置管理，编译时验证

### CertValidator
证书验证器，开发环境信任自签名证书

### TokenRefreshHandler
Token 刷新处理器，防止并发刷新

### SecureWebSocketService
安全 WebSocket 服务，Header 认证

### AppError
统一错误处理，用户友好消息

---

## 常见问题

### Q: 开发环境 HTTPS 证书错误？
A: 开发环境使用自签名证书，CertValidator 会自动信任 localhost 的证书。

### Q: 生产环境如何配置？
A: 设置环境变量 `API_BASE_URL`，Production.xcconfig 会强制要求 HTTPS。

### Q: Token 刷新失败怎么办？
A: TokenRefreshHandler 会自动登出用户并清理本地凭证。

---

## 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-02-13 | 初始版本，安全架构重构 |
