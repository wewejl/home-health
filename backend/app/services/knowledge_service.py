import json
import math
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models.knowledge_base import KnowledgeBase, KnowledgeDocument
from ..config import get_settings

settings = get_settings()


class KnowledgeService:
    """知识库服务 - 简化版 RAG 实现"""
    
    @staticmethod
    def create_knowledge_base(
        db: Session,
        kb_id: str,
        name: str,
        description: str = None,
        doctor_id: int = None,
        department_id: int = None
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            id=kb_id,
            name=name,
            description=description,
            doctor_id=doctor_id,
            department_id=department_id
        )
        db.add(kb)
        db.commit()
        db.refresh(kb)
        return kb

    @staticmethod
    def add_document(
        db: Session,
        knowledge_base_id: str,
        title: str,
        content: str,
        doc_type: str = None,
        source: str = None,
        tags: List[str] = None,
        metadata: dict = None
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            knowledge_base_id=knowledge_base_id,
            title=title,
            content=content,
            doc_type=doc_type,
            source=source,
            tags=tags,
            doc_metadata=metadata,
            status="pending"
        )
        db.add(doc)
        
        # 更新知识库统计
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if kb:
            kb.total_documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).count() + 1
        
        db.commit()
        db.refresh(doc)
        return doc

    @staticmethod
    def search_documents(
        db: Session,
        knowledge_base_id: str,
        query: str,
        top_k: int = 5
    ) -> List[KnowledgeDocument]:
        """简化版搜索 - 基于关键词匹配"""
        # 获取所有已审核的文档
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.status == "approved"
        ).all()
        
        if not documents:
            return []
        
        # 简单的关键词匹配打分
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in documents:
            content_lower = (doc.title + " " + doc.content).lower()
            score = sum(1 for word in query_words if word in content_lower)
            
            # 标签匹配加分
            if doc.tags:
                for tag in doc.tags:
                    if tag.lower() in query.lower():
                        score += 2
            
            if score > 0:
                scored_docs.append((doc, score))
        
        # 按分数排序并返回 top_k
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:top_k]]

    @staticmethod
    def get_context_for_query(
        db: Session,
        knowledge_base_id: str,
        query: str,
        max_tokens: int = 2000
    ) -> str:
        """获取用于 RAG 的上下文"""
        if not knowledge_base_id:
            return ""
        
        docs = KnowledgeService.search_documents(db, knowledge_base_id, query, top_k=3)
        
        if not docs:
            return ""
        
        context_parts = []
        total_len = 0
        
        for doc in docs:
            doc_text = f"【{doc.title}】\n{doc.content}"
            if total_len + len(doc_text) > max_tokens * 2:  # 粗略估计
                break
            context_parts.append(doc_text)
            total_len += len(doc_text)
        
        if context_parts:
            return "参考资料:\n" + "\n\n".join(context_parts)
        return ""

    @staticmethod
    def approve_document(
        db: Session,
        doc_id: int,
        approved: bool,
        reviewed_by: int,
        review_notes: str = None
    ) -> KnowledgeDocument:
        doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
        if doc:
            doc.status = "approved" if approved else "rejected"
            doc.reviewed_by = reviewed_by
            doc.review_notes = review_notes
            from datetime import datetime
            doc.reviewed_at = datetime.utcnow()
            
            if approved:
                doc.is_indexed = True
                doc.chunk_count = 1
            
            db.commit()
            db.refresh(doc)
        return doc

    @staticmethod
    def update_kb_stats(db: Session, knowledge_base_id: str):
        """更新知识库统计信息"""
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
        if kb:
            kb.total_documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id
            ).count()
            kb.total_chunks = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                KnowledgeDocument.is_indexed == True
            ).count()
            db.commit()
