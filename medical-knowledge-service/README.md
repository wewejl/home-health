# Medical Knowledge Service

> 医学知识库向量检索服务 - 可复用的独立服务组件

这是一个独立的医学知识库服务，使用向量数据库进行语义检索，可以被其他项目复用。

## 特性

- **向量检索**: 基于 PostgreSQL + pgvector 的语义搜索
- **医学知识**: 内置 ICD-10 常见疾病知识库
- **独立部署**: 可作为独立服务部署，多个项目共享
- **Python SDK**: 提供异步/同步 SDK，易于集成
- **RESTful API**: 标准的 HTTP API 接口
- **多 Embedding 支持**: Mock、OpenAI、Qwen(通义千问) 等

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     医学知识库服务                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   API 层     │  │   SDK 层      │  │     数据加载器        │ │
│  │  (FastAPI)  │  │ (异步/同步)   │  │   (ICD-10 数据)     │ │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────┘ │
│         │                │                     │              │
│         └────────────────┴─────────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │ 知识库服务层     │                        │
│                    │KnowledgeService│                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐              │
│         ▼                                     ▼              │
│  ┌────────────────┐                  ┌────────────────┐     │
│  │ Embedding 服务  │                  │  向量存储        │     │
│  │ - Mock         │                  │ - Pgvector      │     │
│  │ - OpenAI       │                  │ - (可扩展)       │     │
│  │ - Qwen         │                  │                 │     │
│  └────────────────┘                  └────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │ PostgreSQL +     │
                  │ pgvector        │
                  └─────────────────┘
```

## 快速开始

### 1. Docker 部署（推荐）

```bash
# 克隆项目
git clone <repo-url>
cd medical-knowledge-service

# 启动服务（包括数据库）
./start.sh
# 或
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

服务启动后：
- API 地址: http://localhost:8200
- 数据库: localhost:5433

### 2. 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接

# 启动 API 服务
uvicorn medical_knowledge_service.api:app --reload --host 0.0.0.0 --port 8200
```

### 3. 作为 Python 包使用

```bash
# 安装到项目
pip install -e .

# 或从其他项目引用
pip install git+<repo-url>
```

## 使用方法

### Python SDK

```python
import asyncio
from medical_knowledge_service import KnowledgeClient

async def main():
    # 创建客户端
    client = KnowledgeClient(
        base_url="http://localhost:8200",
        api_key="your-api-key"  # 如果配置了
    )

    # 搜索知识
    results = await client.search(
        query="湿疹的症状和治疗方法",
        specialty="dermatology",
        top_k=5
    )

    for item in results["results"]:
        print(f"[{item['score']}] {item['content'][:100]}...")

# 同步客户端
from medical_knowledge_service import SyncKnowledgeClient

client = SyncKnowledgeClient(base_url="http://localhost:8200")
results = client.search("高血压的治疗")
```

### REST API

```bash
# 健康检查
curl http://localhost:8200/health

# 搜索知识
curl -X POST http://localhost:8200/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "湿疹",
    "specialty": "dermatology",
    "top_k": 5
  }'

# 获取统计信息
curl http://localhost:8200/api/v1/stats \
  -H "X-API-Key: your-api-key"

# 获取科室列表
curl http://localhost:8200/api/v1/specialties
```

### 在其他项目中集成

```python
# 方式1: 使用 SDK
from medical_knowledge_service import SyncKnowledgeClient

class MedicalAgent:
    def __init__(self):
        self.kb_client = SyncKnowledgeClient(
            base_url="http://localhost:8200"
        )

    def answer_question(self, question: str, specialty: str = None):
        # 检索相关知识
        kb_results = self.kb_client.search(
            query=question,
            specialty=specialty
        )

        # 使用检索到的知识生成回答
        # ...

# 方式2: 直接嵌入
from medical_knowledge_service import KnowledgeService
import asyncio

async def main():
    service = KnowledgeService()
    await service.initialize()
    await service.load_data()

    results = await service.search("心梗的症状")
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | postgresql://postgres:postgres@localhost:5432/medical_knowledge |
| `API_KEY` | API 密钥（留空则不验证） | - |
| `EMBEDDING_PROVIDER` | Embedding 提供商 | mock |
| `EMBEDDING_API_KEY` | Embedding API 密钥 | - |
| `EMBEDDING_BASE_URL` | Embedding API 地址 | - |
| `EMBEDDING_MODEL` | Embedding 模型 | text-embedding-v3 |
| `DIMENSION` | 向量维度 | 1024 |
| `VECTOR_TABLE` | 向量表名 | knowledge_vectors |

### Embedding 提供商

- **mock**: 伪随机向量，用于开发测试
- **openai**: OpenAI text-embedding-3 模型
- **qwen**: 阿里云通义千问 Embedding
- **dashscope**: 阿里云 DashScope API

## 支持的科室

| 代码 | 科室 | 疾病 |
|------|------|------|
| `dermatology` | 皮肤科 | 湿疹、银屑病、特应性皮炎、甲癣 |
| `cardiology` | 心内科 | 高血压、心肌梗死、心力衰竭 |
| `respiratory` | 呼吸科 | 支气管哮喘、慢阻肺 |
| `gastroenterology` | 消化科 | 胃食管反流病、胃溃疡 |
| `neurology` | 神经内科 | 偏头痛、多发性硬化 |
| `endocrinology` | 内分泌科 | 2型糖尿病 |
| `orthopedics` | 骨科 | 下腰痛 |
| `ophthalmology` | 眼科 | 近视 |
| `otorhinolaryngology` | 耳鼻喉科 | 过敏性鼻炎 |
| `obstetrics_gynecology` | 妇产科 | 痛经 |
| `pediatrics` | 儿科 | 急性上呼吸道感染 |

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查 |
| `/api/v1/search` | POST | 搜索知识 |
| `/api/v1/stats` | GET | 获取统计信息 |
| `/api/v1/specialties` | GET | 获取科室列表 |
| `/api/v1/data/load` | POST | 加载知识数据 |

## 项目结构

```
medical-knowledge-service/
├── medical_knowledge_service/
│   ├── core/              # 核心抽象接口
│   │   ├── vector_store.py
│   │   ├── embedding.py
│   │   └── config.py
│   ├── stores/            # 向量存储实现
│   │   └── pgvector_store.py
│   ├── embeddings/        # Embedding 服务实现
│   │   ├── mock_embedding.py
│   │   └── openai_embedding.py
│   ├── loaders/           # 数据加载器
│   │   └── icd10_loader.py
│   ├── api/               # REST API
│   │   └── main.py
│   ├── sdk/               # Python SDK
│   │   └── client.py
│   └── knowledge_service.py  # 核心服务类
├── docker-compose.yml     # Docker 编排
├── Dockerfile             # API 镜像
├── requirements.txt       # Python 依赖
├── setup.py               # 包安装
├── start.sh               # 快速启动脚本
└── README.md
```

## 许可证

MIT License
