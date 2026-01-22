# 短信服务配置

**更新日期:** 2026-01-22
**状态:** ✅ 已配置

---

## 快速参考

| 配置项 | 说明 |
|--------|------|
| 服务提供商 | 阿里云号码认证服务 (Dypnsapi) |
| AccessKey ID | [从阿里云控制台获取] |
| AccessKey Secret | [从阿里云控制台获取] |
| 签名名称 | `速通互联验证码` |
| 模板代码 | `100001` |

---

## 环境变量配置

```bash
# backend/.env 或 .env.production

SMS_PROVIDER=aliyun
SMS_ACCESS_KEY_ID=[你的AccessKey ID]
SMS_ACCESS_KEY_SECRET=[你的AccessKey Secret]
SMS_SIGN_NAME=速通互联验证码
SMS_TEMPLATE_CODE=100001

ENABLE_SMS_VERIFICATION=true
TEST_MODE=false  # 生产环境设为 false
```

---

## Python 依赖

```txt
# requirements.txt
alibabacloud-dypnsapi20170525>=3.0.0
alibabacloud-credentials>=0.3.0
```

---

## API 调用示例

```python
from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
from alibabacloud_tea_util import models as util_models

config = open_api_models.Config(
    access_key_id=os.getenv('SMS_ACCESS_KEY_ID'),
    access_key_secret=os.getenv('SMS_ACCESS_KEY_SECRET')
)
config.endpoint = 'dypnsapi.aliyuncs.com'
client = DypnsapiClient(config)

request = dypnsapi_models.SendSmsVerifyCodeRequest(
    sign_name='速通互联验证码',
    template_code='100001',
    phone_number='18107300167',
    template_param='{"code":"888888","min":"5"}'
)

runtime = util_models.RuntimeOptions()
response = client.send_sms_verify_code_with_options(request, runtime)
# response.body.code == 'OK' 表示成功
```

---

## 重要说明

### 号码认证服务 vs 传统短信服务

| 特性 | 号码认证服务 (Dypnsapi) | 传统短信服务 (Dysmsapi) |
|------|------------------------|------------------------|
| API文档 | [链接](https://help.aliyun.com/document_detail/2299872.html) | [链接](https://help.aliyun.com/document_detail/101414.html) |
| 用途 | 验证码发送（推荐） | 通用短信 |
| SDK | `alibabacloud-dypnsapi20170525` | `alibabacloud-dysmsapi20170525` |
| Endpoint | `dypnsapi.aliyuncs.com` | `dysmsapi.aliyuncs.com` |

**本项目使用号码认证服务！**

---

## 部署检查清单

生产环境部署前确认：

- [ ] 安装 SDK 依赖
- [ ] 设置 `TEST_MODE=false`
- [ ] 设置 `ENABLE_SMS_VERIFICATION=true`
- [ ] 确认签名和模板已通过审核
- [ ] 发送测试短信验证

---

## 常见错误

| 错误码 | 说明 | 解决方法 |
|--------|------|----------|
| `biz.FREQUENCY` | 发送频率过高 | 等待几分钟后重试 |
| `isv.SMS_TEMPLATE_ILLEGAL` | 模板不存在 | 检查模板代码是否正确 |
| `isv.SMS_SIGNATURE_ILLEGAL` | 签名不存在 | 检查签名名称是否正确 |
