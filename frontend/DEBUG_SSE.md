# SSE 流式输出问题排查指南

## 问题现象
前端显示"正在思考..."后卡住，没有返回消息。

## 快速诊断步骤

### 步骤 1: 检查浏览器控制台

1. 打开浏览器开发者工具（F12）
2. 切换到 Console 标签
3. 重新发送消息
4. 查看是否有以下日志：

**正常情况应该看到：**
```
[SSE] Starting stream request to: http://localhost:8000/derma/xxx/continue
[SSE] Response status: 200
[SSE] Response headers: {content-type: "text/event-stream", ...}
[SSE] Raw line: event: meta...
[SSE] Event type: meta
[SSE] Meta event: {session_id: "...", stage: "collecting"}
[SSE] Raw line: event: chunk...
[SSE] Chunk event: 手
[SSE] Complete event: {...}
```

**如果看到错误：**
- `HTTP error! status: 401` → 需要重新登录
- `HTTP error! status: 500` → 后端错误，查看后端日志
- `Failed to parse line` → SSE 格式问题
- 完全没有日志 → 请求没发出去

### 步骤 2: 检查 Network 面板

1. 切换到 Network 标签
2. 重新发送消息
3. 找到 `/derma/{session_id}/continue` 请求
4. 查看：
   - **Status**: 应该是 200
   - **Type**: 应该是 `eventsource` 或 `fetch`
   - **Headers** → Request Headers → Accept: 应该包含 `text/event-stream`
   - **Response**: 查看是否有数据返回

### 步骤 3: 测试后端

运行测试脚本：
```bash
cd backend
python test_sse.py
```

应该看到类似输出：
```
1. 登录...
✓ 登录成功
2. 创建会话...
✓ 会话创建成功
3. 测试流式请求...
  响应状态: 200
  [0] event: meta
  [1] data: {"session_id": "..."}
  [2] 
  [3] event: chunk
  ...
✓ 流式响应完成
```

## 常见问题及解决方案

### 问题 1: 401 Unauthorized

**原因**: Token 过期或未登录

**解决**:
```javascript
// 清除本地存储并重新登录
localStorage.clear();
// 刷新页面重新登录
```

### 问题 2: CORS 错误

**原因**: 跨域配置问题

**解决**: 检查后端 CORS 配置
```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 问题 3: 后端没有返回数据

**可能原因**:
1. CrewAI 执行失败
2. LLM API 调用超时
3. 数据库连接问题

**检查后端日志**:
```bash
# 查看后端控制台输出
# 应该看到：
[DermaCrewService] 处理对话前的状态
[DermaCrewService] Agent 提取的信息
```

### 问题 4: SSE 解析失败

**原因**: SSE 格式不正确

**调试**: 查看浏览器控制台的 `[SSE] Raw line:` 日志

**正确的 SSE 格式**:
```
event: meta
data: {"session_id": "xxx"}

event: chunk
data: {"text": "你"}

event: complete
data: {"message": "完整消息", "quick_options": [...]}

```

## 临时回退方案

如果 SSE 流式有问题，可以临时使用非流式版本：

### 修改前端代码

在 `frontend/src/pages/DermaChat.tsx` 的 `handleSend` 函数中：

```typescript
// 注释掉流式请求
// dermaAgentApi.sendMessageStream(sessionId, messageText, history, {...});

// 改用非流式请求
try {
  const response = await dermaAgentApi.sendMessage(sessionId, messageText, history);
  const data = response.data;

  if (data.message) {
    const assistantMessage: Message = {
      role: 'assistant',
      content: data.message,
      timestamp: new Date().toISOString(),
      quick_options: data.quick_options || []
    };
    setMessages(prev => [...prev.slice(0, -1), assistantMessage]);
    
    if (data.quick_options && data.quick_options.length > 0) {
      setQuickOptions(data.quick_options);
    }
  }
  setLoading(false);
} catch (error) {
  console.error('Failed to send message:', error);
  message.error('发送消息失败，请重试');
  setMessages(prev => prev.slice(0, -1));
  setLoading(false);
}
```

## 下一步

请按照以上步骤排查，然后告诉我：
1. 浏览器控制台看到了什么日志？
2. Network 面板中请求的状态是什么？
3. 后端测试脚本的输出是什么？

这样我可以精确定位问题并提供解决方案。
