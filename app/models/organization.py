from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    memberships = relationship(
        "Membership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    knowledge_bases = relationship(
        "KnowledgeBase",
        back_populates="organization",
        cascade="all, delete-orphan",
    )