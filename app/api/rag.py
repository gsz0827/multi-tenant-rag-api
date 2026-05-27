from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_accessible_knowledge_base
from app.api.users import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.services.embedding_service import create_embedding
from app.services.llm_service import generate_answer_with_context
from app.models.rag_qa_record import RagQaRecord
from app.schemas.rag import (
    RagAskRequest,
    RagAskResponse,
    RagHistoryItem,
    RagSourceChunk,
)
from app.core.config import settings

router = APIRouter(prefix="/rag", tags=["rag"])


def build_no_relevant_sources_answer(answer_language: str) -> str:
    language = answer_language.lower().strip()

    if language == "zh":
        return "根据已提供的文档，我不知道答案。没有找到与这个问题足够相关的来源片段。"

    if language == "en":
        return (
            "I don't know based on the provided documents. "
            "I could not find sufficiently relevant source chunks for this question."
        )

    return (
        "I don't know based on the provided documents. "
        "I could not find sufficiently relevant source chunks for this question."
    )

@router.post("/ask", response_model=RagAskResponse)
def ask_knowledge_base(
    request: RagAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=request.knowledge_base_id,
    )

    answer_language = request.answer_language.lower().strip()

    if answer_language not in {"auto", "zh", "en"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="answer_language must be one of: auto, zh, en",
        )
        
    query_embedding = create_embedding(request.question)

    rows = (
        db.query(
            DocumentChunk,
            Document,
            DocumentChunk.embedding.l2_distance(query_embedding).label("distance"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.knowledge_base_id == request.knowledge_base_id)
        .filter(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.l2_distance(query_embedding))
        .limit(request.top_k)
        .all()
    )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No embedded chunks found for this knowledge base",
        )

    sources: list[RagSourceChunk] = []

    context_parts = []

    for index, row in enumerate(rows, start=1):
        chunk = row[0]
        document = row[1]
        distance = float(row[2])
        score = 1 / (1 + distance)

        sources.append(
            RagSourceChunk(
                document_id=chunk.document_id,
                filename=document.filename,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )

        context_parts.append(
            f"[{index}] filename={document.filename} | "
            f"document_id={chunk.document_id} | "
            f"chunk_id={chunk.id} | chunk_index={chunk.chunk_index}\n"
            f"{chunk.content}"
        )

    best_score = sources[0].score if sources else 0.0

    if best_score < settings.RAG_MIN_SCORE:
        answer = build_no_relevant_sources_answer(answer_language)

        record = RagQaRecord(
            knowledge_base_id=request.knowledge_base_id,
            user_id=current_user.id,
            question=request.question,
            answer=answer,
            sources=[source.model_dump() for source in sources],
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return RagAskResponse(
            answer=answer,
            sources=sources,
            history_id=record.id,
        )
        
    context = "\n\n---\n\n".join(context_parts)

    answer = generate_answer_with_context(
        question=request.question,
        context=context,
        answer_language=answer_language,
    )

    record = RagQaRecord(
        knowledge_base_id=request.knowledge_base_id,
        user_id=current_user.id,
        question=request.question,
        answer=answer,
        sources=[source.model_dump() for source in sources],
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return RagAskResponse(
        answer=answer,
        sources=sources,
        history_id=record.id,
    )


@router.get("/history", response_model=list[RagHistoryItem])
def list_rag_history(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=knowledge_base_id,
    )

    records = (
        db.query(RagQaRecord)
        .filter(RagQaRecord.knowledge_base_id == knowledge_base_id)
        .filter(RagQaRecord.user_id == current_user.id)
        .order_by(RagQaRecord.created_at.desc())
        .all()
    )

    return records
    

@router.get("/history/{history_id}", response_model=RagHistoryItem)
def get_rag_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(RagQaRecord)
        .filter(RagQaRecord.id == history_id)
        .filter(RagQaRecord.user_id == current_user.id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG history record not found",
        )

    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=record.knowledge_base_id,
    )

    return record


@router.delete("/history/{history_id}")
def delete_rag_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.query(RagQaRecord)
        .filter(RagQaRecord.id == history_id)
        .filter(RagQaRecord.user_id == current_user.id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RAG history record not found",
        )

    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=record.knowledge_base_id,
    )

    db.delete(record)
    db.commit()

    return {
        "message": "RAG history record deleted successfully",
        "history_id": history_id,
    }