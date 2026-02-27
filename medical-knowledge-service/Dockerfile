FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 先安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY medical_knowledge_service/ /app/medical_knowledge_service/

# 复制数据文件
COPY data/ /app/data/

# 设置 PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8200

CMD ["uvicorn", "medical_knowledge_service.api.main:app", "--host", "0.0.0.0", "--port", "8200"]
