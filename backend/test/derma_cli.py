#!/usr/bin/env python3
"""
皮肤科智能体 API 交互式命令行调试工具

功能：
- 自动登录获取 Token（测试模式验证码 000000）
- 自动创建/恢复会话
- 交互式 REPL：chat / skin / report 命令
- 自动管理历史记录
"""

import base64
import json
import os
import sys
import readline
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

try:
    import httpx
except ImportError:
    print("错误: 需要安装 httpx 库")
    print("请运行: pip install httpx")
    sys.exit(1)


# ==================== 配置 ====================

DEFAULT_BASE_URL = "http://localhost:8100"
DEFAULT_TEST_PHONE = "13800138000"
DEFAULT_TEST_CODE = "000000"
SESSION_CACHE_DIR = Path.home() / ".derma_cli"
SESSION_CACHE_FILE = SESSION_CACHE_DIR / "session.json"

SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
}

HELP_TEXT = """
╔══════════════════════════════════════════════════════════════════╗
║                    皮肤科智能体 CLI 交互模式                       ║
╠══════════════════════════════════════════════════════════════════╣
║  命令说明：                                                        ║
║                                                                    ║
║  chat <消息>          发送文字消息进行问诊对话                      ║
║  skin <图片路径> [描述] 上传皮肤照片进行影像分析                    ║
║  report <图片路径> [类型] 上传报告图片进行解读                      ║
║                                                                    ║
║  history             查看当前对话历史                              ║
║  status              查看当前会话状态                              ║
║  reset               重置会话（开始新对话）                        ║
║  stream on/off       开启/关闭流式输出（默认开启）                 ║
║                                                                    ║
║  help                显示此帮助                                    ║
║  exit / quit         退出程序                                      ║
╚══════════════════════════════════════════════════════════════════╝
"""


# ==================== 工具函数 ====================

def load_image_as_base64(image_path: str) -> str:
    """将本地图片转换为纯 base64 字符串（不带 data URL 前缀）"""
    path = Path(image_path).expanduser()
    
    if not path.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    
    ext = path.suffix.lower()
    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError(f"不支持的图片格式: {ext}，支持: {', '.join(SUPPORTED_IMAGE_EXTENSIONS.keys())}")
    
    with open(path, 'rb') as f:
        image_data = f.read()
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return base64_data


def print_json(data: dict, indent: int = 2):
    """格式化打印 JSON"""
    print(json.dumps(data, ensure_ascii=False, indent=indent))


def print_assistant_message(message: str):
    """打印助手消息"""
    print(f"\n🤖 助手: {message}\n")


def print_error(message: str):
    """打印错误消息"""
    print(f"\n❌ 错误: {message}\n")


def print_info(message: str):
    """打印信息消息"""
    print(f"\n💡 {message}\n")


def print_success(message: str):
    """打印成功消息"""
    print(f"\n✅ {message}\n")


# ==================== 会话缓存 ====================

class SessionCache:
    """会话缓存管理"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
        self.history: List[Dict] = []
        self.stage: str = "greeting"
        self.progress: int = 0
        
    def save(self):
        """保存到文件"""
        SESSION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "token": self.token,
            "session_id": self.session_id,
            "history": self.history,
            "stage": self.stage,
            "progress": self.progress,
            "saved_at": datetime.now().isoformat()
        }
        with open(SESSION_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self) -> bool:
        """从文件加载，返回是否成功"""
        if not SESSION_CACHE_FILE.exists():
            return False
        try:
            with open(SESSION_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.token = data.get("token")
            self.session_id = data.get("session_id")
            self.history = data.get("history", [])
            self.stage = data.get("stage", "greeting")
            self.progress = data.get("progress", 0)
            return True
        except:
            return False
    
    def clear(self):
        """清除缓存"""
        self.session_id = None
        self.history = []
        self.stage = "greeting"
        self.progress = 0
        if SESSION_CACHE_FILE.exists():
            SESSION_CACHE_FILE.unlink()
    
    def add_message(self, role: str, message: str):
        """添加消息到历史"""
        self.history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })


# ==================== API 客户端 ====================

class DermaClient:
    """皮肤科 API 客户端"""
    
    def __init__(self, base_url: str, cache: SessionCache):
        self.base_url = base_url.rstrip('/')
        self.cache = cache
        self.client = httpx.Client(timeout=120.0)
        self.stream_enabled = True
    
    def _headers(self, stream: bool = False) -> dict:
        headers = {
            "Content-Type": "application/json",
        }
        if self.cache.token:
            headers["Authorization"] = f"Bearer {self.cache.token}"
        if stream and self.stream_enabled:
            headers["Accept"] = "text/event-stream"
        return headers
    
    def login(self, phone: str, code: str) -> bool:
        """登录获取 Token"""
        url = f"{self.base_url}/auth/login"
        try:
            resp = self.client.post(url, json={"phone": phone, "code": code})
            if resp.status_code == 200:
                data = resp.json()
                self.cache.token = data.get("token")
                self.cache.save()
                return True
            else:
                print_error(f"登录失败: {resp.text}")
                return False
        except Exception as e:
            print_error(f"登录请求失败: {e}")
            return False
    
    def verify_token(self) -> bool:
        """验证 Token 是否有效"""
        if not self.cache.token:
            return False
        url = f"{self.base_url}/auth/me"
        try:
            resp = self.client.get(url, headers=self._headers())
            return resp.status_code == 200
        except:
            return False
    
    def start_session(self, chief_complaint: str = "") -> bool:
        """开始新会话"""
        url = f"{self.base_url}/derma/start"
        try:
            resp = self.client.post(
                url, 
                headers=self._headers(),
                json={"chief_complaint": chief_complaint}
            )
            if resp.status_code == 200:
                data = resp.json()
                self.cache.session_id = data.get("session_id")
                self.cache.history = []
                self.cache.stage = data.get("stage", "greeting")
                self.cache.progress = data.get("progress", 0)
                
                # 添加助手的开场白到历史
                if data.get("message"):
                    self.cache.add_message("assistant", data["message"])
                    print_assistant_message(data["message"])
                
                self.cache.save()
                return True
            else:
                print_error(f"创建会话失败: {resp.text}")
                return False
        except Exception as e:
            print_error(f"创建会话请求失败: {e}")
            return False
    
    def get_session(self) -> Optional[dict]:
        """获取当前会话状态"""
        if not self.cache.session_id:
            return None
        url = f"{self.base_url}/derma/{self.cache.session_id}"
        try:
            resp = self.client.get(url, headers=self._headers())
            if resp.status_code == 200:
                return resp.json()
            return None
        except:
            return None
    
    def continue_session(
        self, 
        message: str,
        task_type: str = "conversation",
        image_base64: Optional[str] = None,
        report_type: Optional[str] = None
    ) -> Optional[dict]:
        """继续会话"""
        if not self.cache.session_id:
            print_error("没有活动会话")
            return None
        
        url = f"{self.base_url}/derma/{self.cache.session_id}/continue"
        
        # 构建请求
        json_data = {
            "history": self.cache.history,
            "current_input": {"message": message},
            "task_type": task_type
        }
        
        if image_base64:
            json_data["image_base64"] = image_base64
        
        if report_type:
            json_data["report_type"] = report_type
        
        # 添加用户消息到历史
        self.cache.add_message("user", message)
        
        try:
            if self.stream_enabled:
                return self._stream_request(url, json_data)
            else:
                resp = self.client.post(url, headers=self._headers(), json=json_data)
                if resp.status_code == 200:
                    data = resp.json()
                    self._process_response(data)
                    return data
                else:
                    print_error(f"请求失败: {resp.text}")
                    return None
        except Exception as e:
            print_error(f"请求失败: {e}")
            return None
    
    def _stream_request(self, url: str, json_data: dict) -> Optional[dict]:
        """流式请求"""
        final_data = None
        full_text = ""
        
        print("\n🤖 助手: ", end="", flush=True)
        
        try:
            with self.client.stream(
                "POST", url, 
                headers=self._headers(stream=True), 
                json=json_data
            ) as response:
                if response.status_code != 200:
                    print_error(f"请求失败: {response.read().decode()}")
                    return None
                
                current_event = None
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    line = line.strip()
                    if line.startswith("event:"):
                        current_event = line[6:].strip()
                    elif line.startswith("data:") and current_event:
                        try:
                            data = json.loads(line[5:].strip())
                            
                            if current_event == "chunk":
                                text = data.get("text", "")
                                print(text, end="", flush=True)
                                full_text += text
                            elif current_event == "complete":
                                final_data = data
                            elif current_event == "error":
                                print(f"\n❌ {data.get('error', '未知错误')}")
                        except json.JSONDecodeError:
                            pass
                        current_event = None
            
            print("\n")
            
            if final_data:
                self._process_response(final_data, skip_print=True)
                # 用完整文本更新历史
                if full_text:
                    self.cache.add_message("assistant", full_text)
                    self.cache.save()
            
            return final_data
            
        except Exception as e:
            print(f"\n❌ 流式请求失败: {e}")
            return None
    
    def _process_response(self, data: dict, skip_print: bool = False):
        """处理响应数据"""
        self.cache.stage = data.get("stage", self.cache.stage)
        self.cache.progress = data.get("progress", self.cache.progress)
        
        # 检测是否为总结阶段：后端尚未透出 next_action，因此以 stage 为主
        is_summary = data.get("stage") == "summary" or data.get("next_action") == "complete"
        
        message = data.get("message", "")
        if message and not skip_print:
            print_assistant_message(message)
            self.cache.add_message("assistant", message)
        
        # 如果是总结阶段，显示明显标识
        if is_summary:
            print("╔" + "═" * 58 + "╗")
            print("║" + " " * 18 + "📋 问诊总结完成" + " " * 18 + "║")
            print("╚" + "═" * 58 + "╝")
            print()
        
        # 显示快捷选项（总结阶段通常不需要快捷选项）
        quick_options = data.get("quick_options", [])
        if quick_options and not is_summary:
            print("  💬 快捷回复:")
            for opt in quick_options:
                print(f"     • {opt.get('text', '')}")
            print()
        
        # 显示皮肤分析结果
        skin_analysis = data.get("skin_analysis")
        if skin_analysis:
            print("  🔬 皮肤分析结果:")
            print(f"     描述: {skin_analysis.get('lesion_description', '')}")
            print(f"     风险等级: {skin_analysis.get('risk_level', '')}")
            conditions = skin_analysis.get("possible_conditions", [])
            if conditions:
                print("     可能情况:")
                for c in conditions:
                    print(f"       - {c.get('name')}: {c.get('description', '')}")
            print()
        
        # 显示报告解读结果
        report_interp = data.get("report_interpretation")
        if report_interp:
            print("  📋 报告解读:")
            print(f"     报告类型: {report_interp.get('report_type', '')}")
            print(f"     摘要: {report_interp.get('summary', '')}")
            abnormal = report_interp.get("abnormal_findings", [])
            if abnormal:
                print("     异常发现:")
                for a in abnormal:
                    print(f"       - {a}")
            print()
        
        self.cache.save()
    
    def close(self):
        """关闭客户端"""
        self.client.close()


# ==================== 交互式 REPL ====================

class DermaREPL:
    """交互式命令行"""
    
    def __init__(self, base_url: str, phone: str, code: str):
        self.cache = SessionCache()
        self.client = DermaClient(base_url, self.cache)
        self.phone = phone
        self.code = code
        self.running = False
    
    def setup(self) -> bool:
        """初始化：登录 + 恢复/创建会话"""
        print("\n" + "="*60)
        print("        皮肤科智能体 CLI - 交互模式")
        print("="*60)
        
        # 尝试加载缓存
        if self.cache.load() and self.cache.token:
            print_info("发现缓存的会话，正在验证...")
            if self.client.verify_token():
                print_success(f"Token 有效，会话 ID: {self.cache.session_id}")
                if self.cache.session_id:
                    # 验证会话是否还存在
                    session = self.client.get_session()
                    if session:
                        print_success("已恢复之前的会话")
                        return True
                    else:
                        print_info("之前的会话已失效，将创建新会话")
            else:
                print_info("Token 已过期，需要重新登录")
        
        # 登录
        print_info(f"正在登录 (手机号: {self.phone})...")
        if not self.client.login(self.phone, self.code):
            return False
        print_success("登录成功")
        
        # 创建新会话
        print_info("正在创建新会话...")
        if not self.client.start_session():
            return False
        print_success(f"会话已创建，ID: {self.cache.session_id}")
        
        return True
    
    def run(self):
        """运行 REPL"""
        self.running = True
        print(HELP_TEXT)
        
        while self.running:
            try:
                user_input = input("👤 你: ").strip()
                if not user_input:
                    continue
                
                self._handle_input(user_input)
                
            except KeyboardInterrupt:
                print("\n")
                self._cmd_exit()
            except EOFError:
                print("\n")
                self._cmd_exit()
    
    def _handle_input(self, user_input: str):
        """处理用户输入"""
        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["exit", "quit", "q"]:
            self._cmd_exit()
        elif cmd == "help":
            print(HELP_TEXT)
        elif cmd == "chat":
            self._cmd_chat(args)
        elif cmd == "skin":
            self._cmd_skin(args)
        elif cmd == "report":
            self._cmd_report(args)
        elif cmd == "history":
            self._cmd_history()
        elif cmd == "status":
            self._cmd_status()
        elif cmd == "reset":
            self._cmd_reset()
        elif cmd == "stream":
            self._cmd_stream(args)
        else:
            # 默认当作 chat 处理
            self._cmd_chat(user_input)
    
    def _cmd_exit(self):
        """退出"""
        print_info("正在保存会话...")
        self.cache.save()
        self.client.close()
        print_success("再见！")
        self.running = False
    
    def _cmd_chat(self, message: str):
        """发送聊天消息"""
        if not message:
            print_error("请输入消息内容")
            return
        self.client.continue_session(message, task_type="conversation")
    
    def _cmd_skin(self, args: str):
        """皮肤影像分析"""
        parts = args.split(maxsplit=1)
        if not parts:
            print_error("请指定图片路径: skin <图片路径> [描述]")
            return
        
        image_path = parts[0]
        description = parts[1] if len(parts) > 1 else "请帮我分析这张皮肤照片"
        
        try:
            print_info(f"正在加载图片: {image_path}")
            image_base64 = load_image_as_base64(image_path)
            print_success("图片加载成功，正在分析...")
            self.client.continue_session(
                message=description,
                task_type="skin_analysis",
                image_base64=image_base64
            )
        except (FileNotFoundError, ValueError) as e:
            print_error(str(e))
    
    def _cmd_report(self, args: str):
        """报告解读"""
        parts = args.split(maxsplit=1)
        if not parts:
            print_error("请指定图片路径: report <图片路径> [报告类型]")
            return
        
        image_path = parts[0]
        report_type = parts[1] if len(parts) > 1 else "皮肤科检查报告"
        
        try:
            print_info(f"正在加载报告图片: {image_path}")
            image_base64 = load_image_as_base64(image_path)
            print_success("图片加载成功，正在解读...")
            self.client.continue_session(
                message=f"请帮我解读这份{report_type}",
                task_type="report_interpret",
                image_base64=image_base64,
                report_type=report_type
            )
        except (FileNotFoundError, ValueError) as e:
            print_error(str(e))
    
    def _cmd_history(self):
        """查看历史"""
        if not self.cache.history:
            print_info("暂无对话历史")
            return
        
        print("\n📜 对话历史:")
        print("-" * 50)
        for msg in self.cache.history:
            role = "👤 你" if msg["role"] == "user" else "🤖 助手"
            content = msg["message"]
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"{role}: {content}")
        print("-" * 50)
        print(f"共 {len(self.cache.history)} 条消息\n")
    
    def _cmd_status(self):
        """查看状态"""
        print("\n📊 当前状态:")
        print("-" * 30)
        print(f"  会话 ID: {self.cache.session_id or '无'}")
        print(f"  阶段: {self.cache.stage}")
        print(f"  进度: {self.cache.progress}%")
        print(f"  历史消息: {len(self.cache.history)} 条")
        print(f"  流式输出: {'开启' if self.client.stream_enabled else '关闭'}")
        print("-" * 30 + "\n")
    
    def _cmd_reset(self):
        """重置会话"""
        print_info("正在重置会话...")
        self.cache.history = []
        if self.client.start_session():
            print_success(f"新会话已创建，ID: {self.cache.session_id}")
        else:
            print_error("创建新会话失败")
    
    def _cmd_stream(self, args: str):
        """切换流式输出"""
        if args.lower() == "on":
            self.client.stream_enabled = True
            print_success("流式输出已开启")
        elif args.lower() == "off":
            self.client.stream_enabled = False
            print_success("流式输出已关闭")
        else:
            print_info(f"当前流式输出: {'开启' if self.client.stream_enabled else '关闭'}")
            print("使用 'stream on' 或 'stream off' 切换")


# ==================== 主入口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="皮肤科智能体 API 交互式调试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认测试账号启动
  python derma_cli.py

  # 指定手机号
  python derma_cli.py --phone 13900139000

  # 指定后端地址
  python derma_cli.py --base-url http://192.168.1.100:8000

  # 清除缓存后启动
  python derma_cli.py --clear-cache
"""
    )
    
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API 基础 URL（默认: {DEFAULT_BASE_URL}）"
    )
    parser.add_argument(
        "--phone",
        default=DEFAULT_TEST_PHONE,
        help=f"测试手机号（默认: {DEFAULT_TEST_PHONE}）"
    )
    parser.add_argument(
        "--code",
        default=DEFAULT_TEST_CODE,
        help=f"验证码（默认: {DEFAULT_TEST_CODE}，测试模式始终有效）"
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="清除缓存后启动"
    )
    
    args = parser.parse_args()
    
    # 清除缓存
    if args.clear_cache:
        cache = SessionCache()
        cache.clear()
        print_info("缓存已清除")
    
    # 启动 REPL
    repl = DermaREPL(args.base_url, args.phone, args.code)
    
    if repl.setup():
        repl.run()
    else:
        print_error("初始化失败，请检查后端服务是否正常运行")
        sys.exit(1)


if __name__ == "__main__":
    main()
