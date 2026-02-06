import os
import subprocess
import sys

# 不再硬编码 SQLite，使用 .env 中的 DATABASE_URL 配置

subprocess.run([
    sys.executable, "-m", "uvicorn", "app.main:app",
    "--host", "0.0.0.0", "--port", "8100", "--reload"
])
