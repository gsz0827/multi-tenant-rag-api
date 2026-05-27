from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id"),
        nullable=False,
        index=True,
    )

    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)

    storage_path = Column(String(500), nullable=True)

    status = Column(String(50), default="pending", nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    knowledge_base = relationship(
        "KnowledgeBase",
        back_populates="documents",
    )