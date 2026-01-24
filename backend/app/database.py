from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings

settings = get_settings()

# 主数据库引擎 (PostgreSQL)
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 知识库引擎 (SQLite，独立)
knowledge_engine = create_engine(
    settings.KNOWLEDGE_DB_URL,
    connect_args={"check_same_thread": False}
)
KnowledgeSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=knowledge_engine)
KnowledgeBase = declarative_base()


def get_db():
    """主数据库会话 (PostgreSQL)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_knowledge_db():
    """知识库会话 (SQLite)"""
    db = KnowledgeSessionLocal()
    try:
        yield db
    finally:
        db.close()
