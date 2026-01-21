# 阿里云短信服务接入指南

## 概述

本项目已集成阿里云短信验证码服务，用于用户注册、登录和密码重置等场景。

## 功能特性

- ✅ 验证码发送与验证
- ✅ 防刷机制（冷却期、频率限制）
- ✅ 自动降级（配置错误时使用模拟模式）
- ✅ 完整的错误处理和日志记录

## 配置步骤

### 1. 获取阿里云 AccessKey

1. 登录[阿里云控制台](https://ram.console.aliyun.com/manage/ak)
2. 创建 AccessKey ID 和 AccessKey Secret
3. **重要**: 妥善保管 Secret，不要泄露

### 2. 开通短信服务

1. 访问[阿里云短信服务控制台](https://dysms.console.aliyun.com/)
2. 开通短信服务
3. 申请短信签名（如：速通互联验证码）
4. 申请短信模板（验证码类型）
   - 模板示例：`您的验证码是：${code}，${min}分钟内有效`
   - 获得模板 CODE（如：100001）

### 3. 配置环境变量

在 `backend/.env` 文件中添加以下配置：

```bash
# 启用短信验证功能
ENABLE_SMS_VERIFICATION=true

# 阿里云短信服务配置
ALIYUN_SMS_ACCESS_KEY_ID=your-aliyun-access-key-id
ALIYUN_SMS_ACCESS_KEY_SECRET=your-aliyun-access-key-secret
ALIYUN_SMS_SIGN_NAME=速通互联验证码
ALIYUN_SMS_TEMPLATE_CODE=100001
ALIYUN_SMS_VALID_TIME=5
```

**配置说明**：
- `ENABLE_SMS_VERIFICATION`: 是否启用短信验证（false 时所有验证码自动通过）
- `ALIYUN_SMS_ACCESS_KEY_ID`: 阿里云 AccessKey ID
- `ALIYUN_SMS_ACCESS_KEY_SECRET`: 阿里云 AccessKey Secret
- `ALIYUN_SMS_SIGN_NAME`: 短信签名名称
- `ALIYUN_SMS_TEMPLATE_CODE`: 短信模板 CODE
- `ALIYUN_SMS_VALID_TIME`: 验证码有效时间（分钟）

### 4. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 5. 重启服务

```bash
# 开发环境
uvicorn app.main:app --reload

# 生产环境
docker-compose restart backend
```

## 使用方式

### API 接口

#### 1. 发送验证码

```http
POST /api/auth/send-code
Content-Type: application/json

{
  "phone": "18107300167"
}
```

**响应**：
```json
{
  "message": "验证码发送成功",
  "expires_in": 300
}
```

#### 2. 验证码登录/注册

```http
POST /api/auth/login
Content-Type: application/json

{
  "phone": "18107300167",
  "code": "123456"
}
```

**响应**：
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "phone": "18107300167",
    "nickname": "用户0167"
  },
  "is_new_user": true
}
```

### 防刷策略

系统内置多层防刷机制：

1. **冷却期**: 同一手机号 60 秒内只能发送一次
2. **手机号频率限制**: 每小时最多 10 次
3. **IP 频率限制**: 每小时最多 30 次
4. **验证次数限制**: 每个验证码最多验证 5 次
5. **锁定机制**: 超过限制后锁定 30 分钟

## 测试模式

### 开发环境测试

设置 `TEST_MODE=true` 时，验证码 `000000` 始终有效，方便开发测试。

```bash
# .env
TEST_MODE=true
ENABLE_SMS_VERIFICATION=false
```

### 模拟模式

当以下任一条件满足时，系统自动使用模拟模式（不实际发送短信）：

1. `ENABLE_SMS_VERIFICATION=false`
2. 未配置阿里云 AccessKey
3. 阿里云 SDK 未安装
4. 阿里云服务调用失败

模拟模式下会在日志中输出验证码，方便调试。

## 代码示例

### Python 客户端

```python
import httpx

# 发送验证码
response = httpx.post(
    "http://localhost:8000/api/auth/send-code",
    json={"phone": "18107300167"}
)
print(response.json())

# 登录
response = httpx.post(
    "http://localhost:8000/api/auth/login",
    json={"phone": "18107300167", "code": "123456"}
)
token = response.json()["token"]
```

### iOS 客户端

```swift
// 发送验证码
func sendVerificationCode(phone: String) async throws {
    let url = URL(string: "\(baseURL)/auth/send-code")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = ["phone": phone]
    request.httpBody = try JSONEncoder().encode(body)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    let response = try JSONDecoder().decode(SendCodeResponse.self, from: data)
    print("验证码已发送，有效期: \(response.expires_in)秒")
}

// 验证码登录
func login(phone: String, code: String) async throws -> LoginResponse {
    let url = URL(string: "\(baseURL)/auth/login")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    
    let body = ["phone": phone, "code": code]
    request.httpBody = try JSONEncoder().encode(body)
    
    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(LoginResponse.self, from: data)
}
```

## 故障排查

### 1. 短信发送失败

**检查清单**：
- ✅ AccessKey 配置正确
- ✅ 短信签名已审核通过
- ✅ 短信模板已审核通过
- ✅ 账户余额充足
- ✅ 手机号格式正确（11位，1开头）

**查看日志**：
```bash
# 查看短信服务日志
docker-compose logs -f backend | grep SMS
```

### 2. 验证码验证失败

**常见原因**：
- 验证码已过期（默认 5 分钟）
- 验证次数超过限制（5 次）
- 手机号不匹配
- 验证码输入错误

### 3. 频率限制触发

**解决方案**：
- 等待锁定时间结束（30 分钟）
- 或在开发环境设置 `TEST_MODE=true` 使用测试验证码 `000000`

## 安全建议

1. **AccessKey 安全**
   - 不要将 AccessKey 提交到代码仓库
   - 使用环境变量或密钥管理服务
   - 定期轮换 AccessKey

2. **防刷加固**
   - 前端添加图形验证码
   - 使用设备指纹识别
   - 监控异常发送行为

3. **日志脱敏**
   - 日志中只记录手机号后 4 位
   - 不记录完整验证码

## 成本优化

1. **合理设置有效期**: 默认 5 分钟，避免用户重复发送
2. **启用冷却期**: 60 秒冷却期减少重复发送
3. **监控发送量**: 定期检查异常发送行为
4. **使用测试模式**: 开发环境使用 `TEST_MODE` 避免产生费用

## 相关文档

- [阿里云短信服务文档](https://help.aliyun.com/document_detail/419273.html)
- [Python SDK 文档](https://help.aliyun.com/document_detail/215759.html)
- [短信服务定价](https://www.aliyun.com/price/product#/sms/detail)

## 技术支持

如有问题，请联系：
- 阿里云工单系统
- 项目技术负责人
