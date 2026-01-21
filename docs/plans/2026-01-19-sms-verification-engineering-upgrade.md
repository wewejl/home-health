# 短信验证码工程化改进实施文档

**实施日期**: 2026-01-19  
**方案版本**: 方案一（渐进式改进）  
**实施状态**: ✅ 已完成

---

## 一、改进概述

本次改进在现有内存存储基础上进行工程化升级，主要解决以下问题：
1. 验证码缺少用途区分，存在跨场景滥用风险
2. 验证码验证后立即删除，无法追溯使用记录
3. 测试模式存在安全隐患
4. 缺少完整的审计日志
5. 内存数据无定期清理机制

---

## 二、核心改进内容

### 2.1 验证码用途（Purpose）机制

**实施位置**: `backend/app/services/sms_service.py`

**数据结构调整**:
```python
@dataclass
class VerificationCode:
    code: str
    phone: str
    purpose: str  # 新增：LOGIN/REGISTER/RESET_PASSWORD/SET_PASSWORD
    created_at: float
    expires_at: float
    attempts: int = 0
    verified: bool = False  # 新增：是否已验证成功
    verified_at: Optional[float] = None  # 新增：验证成功时间
    used_for_auth: bool = False  # 新增：是否已用于认证
```

**存储Key调整**:
- 原来：`phone` → `VerificationCode`
- 现在：`phone:purpose` → `VerificationCode`

**优势**:
- 同一手机号可同时存在多个不同用途的验证码
- 验证时必须匹配用途，防止跨场景攻击
- 便于后续审计和统计分析

---

### 2.2 验证码一次性使用机制

**实施位置**: `backend/app/services/sms_service.py`

**状态流转**:
```
[未使用] → [验证中] → [已验证] → [已用于认证]
   ↓
[验证失败] → [超过5次] → [失效]
```

**关键方法**:

1. **verify_code(phone, code, purpose)**: 验证验证码
   - 验证成功后标记 `verified=True`, `verified_at=now`
   - 不立即删除，保留用于审计

2. **mark_used_for_auth(phone, purpose)**: 标记已用于认证
   - 业务逻辑完成后调用
   - 标记 `used_for_auth=True`
   - 防止验证码重放攻击

3. **cleanup_expired()**: 清理过期数据
   - 未验证的验证码：过期即删除
   - 已验证的验证码：保留10分钟后删除（用于审计）

---

### 2.3 测试模式安全加固

**实施位置**: `backend/app/services/sms_service.py`, `backend/app/config.py`

**多层防护**:

1. **环境检查**:
```python
if settings.ENVIRONMENT == "production" and settings.TEST_MODE:
    raise RuntimeError("[SMS] 生产环境禁止开启测试模式！")
```

2. **白名单机制**:
```python
# 配置文件
TEST_PHONE_WHITELIST: str = ""  # 逗号分隔的测试手机号

# 验证逻辑
if settings.TEST_MODE and code == settings.TEST_VERIFICATION_CODE:
    if self.test_phone_whitelist and phone not in self.test_phone_whitelist:
        return False, "测试验证码仅对白名单手机号有效"
```

3. **配置项**:
- `ENVIRONMENT`: development/staging/production
- `TEST_PHONE_WHITELIST`: 测试手机号白名单
- `TEST_VERIFICATION_CODE`: 测试验证码（默认000000）

---

### 2.4 API接口调整

**发送验证码接口**:
```json
POST /auth/send-code
{
  "phone": "13800138000",
  "purpose": "LOGIN"  // 新增必填字段，默认LOGIN
}

响应:
{
  "message": "验证码发送成功",
  "expires_in": 300,
  "purpose": "LOGIN"  // 新增返回字段
}
```

**验证码用途枚举**:
- `LOGIN`: 验证码登录
- `REGISTER`: 密码注册
- `RESET_PASSWORD`: 重置密码
- `SET_PASSWORD`: 设置密码

**各认证接口调整**:
- `/auth/login`: 使用 `purpose="LOGIN"`
- `/auth/register-password`: 使用 `purpose="REGISTER"`
- `/auth/password/set`: 使用 `purpose="SET_PASSWORD"`
- `/auth/password/reset`: 使用 `purpose="RESET_PASSWORD"`

---

### 2.5 定时清理任务

**实施位置**: `backend/app/main.py`

**实现方式**:
```python
async def cleanup_task():
    """定时清理任务"""
    while True:
        try:
            await asyncio.sleep(settings.CLEANUP_INTERVAL_MINUTES * 60)
            logger.info("[CLEANUP] 开始执行定时清理任务")
            sms_service.store.cleanup_expired()
            logger.info("[CLEANUP] 定时清理任务完成")
        except Exception as e:
            logger.error(f"[CLEANUP] 清理任务异常: {e}")

@app.on_event("startup")
async def startup_event():
    # ... 其他初始化代码
    
    # 启动定时清理任务
    if settings.ENABLE_AUTO_CLEANUP:
        logger.info(f"[SMS] 启动定时清理任务，间隔: {settings.CLEANUP_INTERVAL_MINUTES}分钟")
        asyncio.create_task(cleanup_task())
```

**配置项**:
- `ENABLE_AUTO_CLEANUP`: 是否启用自动清理（默认True）
- `CLEANUP_INTERVAL_MINUTES`: 清理间隔（默认5分钟）
- `VERIFICATION_CODE_RETENTION_SECONDS`: 验证码保留时间（默认600秒）

---

### 2.6 增强审计日志

**实施位置**: 所有SMS相关服务和路由

**日志增强点**:

1. **验证码存储**:
```python
logger.info(f"[SMS] 验证码已存储: phone={phone[-4:]}, purpose={purpose}, key={key}")
```

2. **验证成功/失败**:
```python
logger.info(f"[SMS] 验证成功: phone={phone[-4:]}, purpose={purpose}")
logger.warning(f"[SMS] 验证失败-验证码错误: phone={phone[-4:]}, purpose={purpose}, remaining={remaining}")
```

3. **标记已使用**:
```python
logger.info(f"[SMS] 验证码已标记为已使用: phone={phone[-4:]}, purpose={purpose}")
```

4. **清理任务**:
```python
logger.info(f"[SMS] 清理过期验证码: count={len(expired_keys)}")
```

---

## 三、配置文件变更

**文件**: `backend/app/config.py`

**新增配置项**:
```python
# 环境配置
ENVIRONMENT: str = "development"  # development/staging/production

# 测试模式安全配置
TEST_PHONE_WHITELIST: str = ""  # 逗号分隔的测试手机号白名单
TEST_VERIFICATION_CODE: str = "000000"  # 测试验证码

# 验证码保留时间（用于审计）
VERIFICATION_CODE_RETENTION_SECONDS: int = 600  # 10分钟

# 清理任务配置
ENABLE_AUTO_CLEANUP: bool = True
CLEANUP_INTERVAL_MINUTES: int = 5
```

---

## 四、代码变更清单

### 修改的文件

1. **backend/app/config.py**
   - 新增环境配置和测试模式安全配置
   - 新增验证码保留时间和清理任务配置

2. **backend/app/services/sms_service.py**
   - 更新 `VerificationCode` 数据类，添加 purpose、verified 等字段
   - 更新 `VerificationCodeStore`，实现 purpose 机制
   - 实现 `mark_used_for_auth()` 方法
   - 增强 `cleanup_expired()` 方法
   - 添加环境安全检查和白名单机制
   - 更新所有方法签名以支持 purpose 参数

3. **backend/app/services/auth_service.py**
   - 更新 `send_verification_code()` 方法签名
   - 更新 `verify_code()` 方法签名
   - 新增 `mark_code_used()` 方法

4. **backend/app/schemas/auth.py**
   - `SendCodeRequest` 添加 purpose 字段
   - `SendCodeResponse` 添加 purpose 字段
   - 添加 purpose 字段验证器

5. **backend/app/routes/auth.py**
   - 更新所有认证路由以传递 purpose 参数
   - 在业务逻辑完成后调用 `mark_code_used()`
   - 增强日志记录，包含 purpose 信息

6. **backend/app/main.py**
   - 添加定时清理任务 `cleanup_task()`
   - 在启动事件中启动清理任务

---

## 五、向后兼容性

### 兼容策略

1. **purpose 字段**:
   - 新接口：默认值为 "LOGIN"
   - 客户端可选择性传递，不传则使用默认值
   - 服务端强制校验，确保值在枚举范围内

2. **测试模式**:
   - 保持 000000 测试验证码
   - 新增白名单限制（可选配置）
   - 生产环境强制关闭

3. **API响应**:
   - 保持现有字段不变
   - 新增字段向后兼容
   - 客户端可选择性使用新字段

---

## 六、测试建议

### 6.1 功能测试

1. **验证码发送**:
   - 测试不同 purpose 的验证码发送
   - 验证冷却期机制
   - 验证频率限制

2. **验证码验证**:
   - 测试正确验证码
   - 测试错误验证码
   - 测试过期验证码
   - 测试已使用验证码
   - 测试跨 purpose 验证（应失败）

3. **测试模式**:
   - 测试白名单内手机号使用测试验证码
   - 测试白名单外手机号使用测试验证码（应失败）
   - 验证生产环境禁止开启测试模式

4. **定时清理**:
   - 验证过期验证码被清理
   - 验证已验证验证码保留10分钟
   - 验证清理任务不影响正常业务

### 6.2 安全测试

1. **重放攻击**:
   - 验证验证码只能使用一次
   - 验证 `used_for_auth` 标记生效

2. **跨场景攻击**:
   - 验证登录验证码不能用于重置密码
   - 验证 purpose 隔离机制

3. **环境安全**:
   - 验证生产环境无法开启测试模式
   - 验证测试验证码白名单机制

### 6.3 性能测试

1. **并发测试**:
   - 测试高并发发送验证码
   - 测试高并发验证验证码
   - 验证线程锁机制

2. **清理任务**:
   - 验证清理任务不阻塞主业务
   - 验证清理效率

---

## 七、部署说明

### 7.1 环境变量配置

**开发环境** (.env.development):
```bash
ENVIRONMENT=development
TEST_MODE=true
TEST_PHONE_WHITELIST=13800138000,13800138001
TEST_VERIFICATION_CODE=000000
ENABLE_AUTO_CLEANUP=true
CLEANUP_INTERVAL_MINUTES=5
VERIFICATION_CODE_RETENTION_SECONDS=600
```

**生产环境** (.env.production):
```bash
ENVIRONMENT=production
TEST_MODE=false  # 强制关闭
ENABLE_AUTO_CLEANUP=true
CLEANUP_INTERVAL_MINUTES=5
VERIFICATION_CODE_RETENTION_SECONDS=600
```

### 7.2 部署步骤

1. **备份现有配置**
2. **更新代码**
3. **更新环境变量**
4. **重启服务**
5. **验证功能正常**
6. **监控日志**

---

## 八、监控指标

### 关键指标

1. **发送成功率** = 发送成功数 / 发送请求数
2. **验证成功率** = 验证成功数 / 验证请求数
3. **平均验证尝试次数**
4. **频率限制触发次数**
5. **锁定事件次数**
6. **测试验证码使用次数**（生产环境应为0）

### 告警规则

- 发送成功率 < 95% → 告警
- 验证成功率 < 80% → 告警
- 1小时内锁定事件 > 100 → 告警（可能遭受攻击）
- 生产环境测试验证码使用次数 > 0 → 严重告警

---

## 九、后续演进路径

### 短期（1-2个月）
- 收集运行数据和用户反馈
- 优化频率限制参数
- 完善监控告警

### 中期（3-6个月）
- 迁移到数据库持久化（方案三）
- 实现完整的审计追踪
- 添加管理后台查询功能

### 长期（6个月以上）
- 引入 Redis 实现分布式存储（方案二）
- 支持多实例部署
- 实现实时监控大屏

---

## 十、常见问题

### Q1: 为什么不直接使用数据库或Redis？
A: 方案一是渐进式改进，风险最小，可快速上线。后续可平滑迁移到数据库或Redis。

### Q2: 验证码保留10分钟会不会占用太多内存？
A: 验证码数据结构很小（约100字节），即使1000个验证码也只占用约100KB内存，可忽略不计。

### Q3: 如何确保生产环境不会误开启测试模式？
A: 代码中有强制检查，如果 `ENVIRONMENT=production` 且 `TEST_MODE=true`，服务启动时会抛出异常。

### Q4: 定时清理任务会影响性能吗？
A: 不会。清理任务使用异步执行，不阻塞主业务。清理操作有锁保护，执行时间很短。

### Q5: 如何查看验证码使用情况？
A: 查看日志文件，搜索 `[SMS]` 或 `[EVENT]` 标签，可以看到完整的验证码生命周期。

---

## 十一、总结

本次工程化改进在不改变底层存储的前提下，显著提升了短信验证码系统的安全性、可靠性和可追溯性：

✅ **安全性提升**：purpose机制防止跨场景攻击，测试模式加固防止生产环境误用  
✅ **可靠性提升**：一次性使用机制防止重放攻击，定时清理防止内存泄漏  
✅ **可追溯性提升**：完整的审计日志，验证码保留机制  
✅ **向后兼容**：API变更向后兼容，平滑升级  
✅ **可演进性**：为后续迁移到持久化存储打好基础  

**实施状态**: ✅ 已完成所有核心功能  
**建议**: 在测试环境充分验证后再部署到生产环境
