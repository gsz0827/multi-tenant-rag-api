from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Text, func

from app.db.session import Base


class RagQaRecord(Base):
    __tablename__ = "rag_qa_records"

    id = Column(Integer, primary_key=True, index=True)

    knowledge_base_id = Column(
        Integer,
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    sources = Column(JSON, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
