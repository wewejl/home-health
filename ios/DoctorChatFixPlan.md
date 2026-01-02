# iOS AI Doctor Chat 修复与落地方案

版本：v1.1（2025-12-27）  
负责人：Cascade + 项目组  
**状态：✅ 代码修复已完成**

---

## 0. 目标
1. 让 iOS 端 **稳定完成登录 → 建立会话 → 发送消息 → 收到 AI 回复** 的完整链路。
2. 用真实 API 数据替换所有 Mock 内容，保证与后端结构一致。
3. 处理网络与权限问题，确保真机/模拟器均可访问后端并通过 ATS 检查。
4. 增加必要的错误提示与日志，便于排查问题。

---

## 1. 后端与基础环境准备
1. **确认 FastAPI 服务已启动**：`uvicorn app.main:app --reload --port 8000`。
2. **配置 LLM 相关环境变量**（位于 `backend/.env`）：
   - `LLM_BASE_URL`
   - `LLM_API_KEY`
   - `LLM_MODEL`
   - 若为空，`QwenService` 会回退到固定文案，无法获得真实回答（@backend/app/services/qwen_service.py#54-107）。
3. **数据库数据准备**：
   - doctors 表中需包含 iOS 要展示的医生数据及 `knowledge_base_id`（如需 RAG）。
   - 若 doctor 信息缺失，`/sessions` 调用中的 `doctor_id` 将找不到匹配医生，导致 404。

---

## 2. iOS 网络与配置
1. **将 `APIConfig.baseURL` 改为可访问的局域网/线上地址**（@ios/xinlingyisheng/xinlingyisheng/Services/APIConfig.swift#3-17）。
   - 推荐：`http://<局域网IP>:8000`。
   - 保留单独的调试/生产配置（如通过 Build Configuration 或环境枚举管理）。
2. **Info.plist 添加 ATS 例外**（若仍使用 HTTP）：
   ```xml
   <key>NSAppTransportSecurity</key>
   <dict>
       <key>NSAllowsArbitraryLoads</key>
       <true/>
   </dict>
   ```
   - 生产环境建议改为 HTTPS，并仅为具体域名开放。
3. **可选：日志与抓包**
   - 接入 `OSLog` 或 `Logger` 记录 API 错误；必要时用 `Proxyman/Charles` 抓包确认链路。

---

## 3. 登录与鉴权流程
1. **清空旧 token**：在设置菜单加入“退出登录”按钮，调用 `AuthManager.logout()`（@ios/xinlingyisheng/xinlingyisheng/Services/AuthManager.swift#31-49）。
2. **首屏登录判断**：`ContentView` 已根据 `authManager.isLoggedIn` 切换视图（@ios/xinlingyisheng/xinlingyisheng/ContentView.swift#10-23）。若发现仍能直接进入主界面，排查 UserDefaults 中是否残留测试 token。
3. **LoginView 真实调用**：`handleLogin()` 已调用 `APIService.shared.login`（@ios/xinlingyisheng/xinlingyisheng/Views/LoginView.swift#242-285）。请确保后台 `/auth/login` 能返回 token 与 user 信息。
4. **Session 过期处理**：
   - `APIService.makeRequest` 对 401 抛出 `.unauthorized`（@ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift#30-81）。
   - 在全局捕获 401 时跳出登录页，避免沉默失败。

---

## 4. 医生/科室数据改造
1. **删除/替换所有 Mock 数据**：
   - `DepartmentDetailView.mockDoctors`（@ios/xinlingyisheng/xinlingyisheng/Views/DepartmentDetailView.swift#60-100）。
   - `AskDoctorView` 中科室、标签若后端已有接口也应替换。
2. **统一数据模型**：
   - 新建 `DoctorModel.swift`、`DepartmentModel.swift` 等，对应后端 JSON。
   - 若现有 `DoctorInfo` 仍需存在，增加 init(from model: DoctorModel) 便于转换。
3. **API 调用**：
   - `APIService.getDepartments()`、`getDoctors(departmentId:)` 已实现（@ios/xinlingyisheng/xinlingyisheng/Services/APIService.swift#90-98）。
   - 在 `AskDoctorView`、`DepartmentDetailView` 中通过 `Task {}` 异步加载并缓存结果，添加 loading & error state。
4. **UI 展示**：
   - 删除 `#Preview` 中的硬编码医生信息或标明仅供预览使用，避免误解。

---

## 5. 会话与聊天逻辑
1. **创建会话失败时给出提示**：
   - 目前 `createSessionIfNeeded()` 只在 catch 中添加欢迎语，`sessionId` 仍为空，导致后续 `sendMessage` 直接 return（@ios/xinlingyisheng/xinlingyisheng/Views/DoctorChatView.swift#60-134）。
   - 在 catch 中显示 Alert/HUD（例如“创建会话失败：网络错误/未登录”），并提供重试按钮。
2. **发送消息前的校验**：
   - 当 `sessionId` 为 nil 时弹 Toast/Alert，而不是无响应。
   - 在 `isSending` 状态下禁用输入，避免重复提交。
3. **拉取历史消息**：
   - 在会话创建成功后，调用 `getMessages(sessionId:)` 填充 `messages`，保持与后端一致的历史。
4. **反馈/评价**（可选）：接口已提供 `submitFeedback`，可在 UI 中加入“是否有帮助”交互。

---

## 6. 后端协同改进
1. **Doctor 数据**：确保 `id`、`name`、`ai_persona_prompt` 等字段完整。
2. **Sessions 接口**：当前逻辑：
   - 创建会话：`/sessions` 写入数据库（@backend/app/routes/sessions.py#18-48）。
   - 发送消息：`/sessions/{id}/messages` 保存用户内容、调用 `QwenService` 并保存 AI 回复（@backend/app/routes/sessions.py#75-175）。
3. **QwenService 默认回复**：如果 `LLM_API_KEY` 缺失，只会返回固定模板（@backend/app/services/qwen_service.py#54-56）。请务必正确配置。
4. **可观测性**：在 `send_message` 内添加日志，记录 session_id、doctor_id、LLM 调用结果/异常，方便排查。

---

## 7. 用户体验优化（推荐）
1. **Loading/Empty/Error 状态组件**：抽象成可复用视图，避免页面空白。
2. **消息气泡 Skeleton**：发送后先展示占位动画，再替换为 AI 回复。
3. **AI 模型切换**：若医生可配置不同模型，在 UI 中提示“由 XXX 医生 AI 分身回复”。
4. **安全提示**：在聊天顶部提示“线上问诊仅供参考，如有急症请线下就医”。

---

## 8. 实施顺序建议
1. **网络连通性**：调整 baseURL、ATS，确保能访问后端。
2. **鉴权闭环**：确认登录 → token 存储 → 授权请求正常。
3. **会话链路**：处理创建/发送/收消息的异常提示。
4. **数据换真**：替换医生/科室等 Mock 数据。
5. **UI/体验优化 + 日志监控**。

---

## 9. 验收 checklist
- [ ] 真机启动 App 自动进入登录页。
- [ ] 输入手机号 + 验证码可以获取 token，跳转到首页。
- [ ] 首页/科室/医生列表均来自真实接口且可刷新。
- [ ] 进入医生聊天页自动创建会话，失败会提示。
- [ ] 输入问题后，用户消息立即出现，AI 回复可见。
- [ ] 断网/401/LLM 失败等场景均有可感知提示。
- [ ] App 重新启动后仍可凭 token 自动登录；手动登出可清除。

---

## 10. 已完成的代码修改清单

### ✅ 网络与配置
| 文件 | 修改内容 |
|------|----------|
| `Services/APIConfig.swift` | 添加 Environment 枚举，支持开发/生产环境切换，baseURL 改为可配置 |
| `Info.plist` | **新建**，添加 ATS 例外允许 HTTP 请求 |

### ✅ 鉴权闭环
| 文件 | 修改内容 |
|------|----------|
| `Services/AuthManager.swift` | 添加 `unauthorizedNotification` 全局通知、`showLogoutAlert`/`logoutReason` 状态、`hasValidToken` 属性 |
| `Services/APIService.swift` | 401 响应时发送全局通知触发自动登出 |
| `ContentView.swift` | 添加登出提示 Alert |

### ✅ 会话链路
| 文件 | 修改内容 |
|------|----------|
| `Views/DoctorChatView.swift` | 添加 `showError`/`errorMessage`/`sessionCreateFailed` 状态；`createSessionIfNeeded()` 添加登录检查和错误提示；`sendMessage()` 添加会话状态校验；新增 `loadHistoryMessages()` 方法 |
| `Views/DoctorChatView.swift` (ChatInputBar) | 添加 `isSending`/`isDisabled` 参数，发送时显示加载动画 |

### ✅ 数据换真
| 文件 | 修改内容 |
|------|----------|
| `Views/DepartmentDetailView.swift` | 添加 `departmentId` 参数、`doctors`/`isLoading`/`errorMessage` 状态；新增 `loadDoctors()` 调用真实 API；添加 Loading/Empty/Error 状态 UI |
| `Views/DepartmentDetailView.swift` (DoctorInfo) | 新增 `init(from model: DoctorModel)` 初始化器，支持从 API 模型转换 |

### ✅ 退出登录 UI
| 文件 | 修改内容 |
|------|----------|
| `Views/ProfileView.swift` | **新建**，个人中心页面，包含用户信息卡片、功能菜单、退出登录按钮 |
| `Views/HomeView.swift` | 重构为 Tab 切换架构，添加"我的"页面入口，新增 PlaceholderView 占位视图 |

---

## 11. 下一步操作

1. **修改 `APIConfig.swift` 中的 IP 地址**：
   ```swift
   return "http://<你的Mac局域网IP>:8000"
   ```
   终端运行 `ifconfig | grep "inet "` 获取 IP。

2. **启动后端服务**：
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **配置 LLM 环境变量**（`backend/.env`）：
   ```
   LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   LLM_API_KEY=sk-xxx
   LLM_MODEL=qwen-turbo
   ```

4. **在 Xcode 中运行 iOS 应用**，验证完整链路。
