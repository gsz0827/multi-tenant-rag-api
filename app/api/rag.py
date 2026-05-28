from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import date, datetime, time

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
    RagHistoryDeleteResponse,
    RagHistoryItem,
    RagHistoryListResponse,
    RagSourceChunk,
)
from app.core.config import settings
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/rag", tags=["rag"])


def generate_markdown(record: RagQaRecord) -> str:
    lines = [
        f"# Question\n{record.question}\n",
        f"# Answer\n{record.answer}\n",
        "# Sources\n"
    ]
    for i, source in enumerate(record.sources, start=1):
        lines.append(f"## [{i}] {source.get('filename', '')}\n")
        lines.append(f"{source.get('content','')}\n")
    lines.append(f"\n*Created at: {record.created_at}*")
    return "\n".join(lines)


def generate_pdf_bytes(record: RagQaRecord) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    def draw_text(text, font_size=12):
        nonlocal y
        c.setFont("Helvetica", font_size)
        for line in text.split("\n"):
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line)
            y -= font_size + 2

    draw_text(f"Question:\n{record.question}", 12)
    y -= 10
    draw_text(f"Answer:\n{record.answer}", 12)
    y -= 10
    draw_text("Sources:", 12)
    for i, source in enumerate(record.sources, start=1):
        y -= 5
        draw_text(f"[{i}] {source.get('filename', '')}", 12)
        draw_text(source.get("content", ""), 10)
        y -= 5
    draw_text(f"Created at: {record.created_at}", 10)

    c.save()
    buffer.seek(0)
    return buffer


def build_rag_history_query(
    db: Session,
    user_id: int,
    knowledge_base_id: int,
    keyword: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    query = (
        db.query(RagQaRecord)
        .filter(RagQaRecord.knowledge_base_id == knowledge_base_id)
        .filter(RagQaRecord.user_id == user_id)
    )

    clean_keyword = keyword.strip() if keyword else None

    if clean_keyword:
        keyword_like = f"%{clean_keyword}%"

        query = query.filter(
            or_(
                RagQaRecord.question.ilike(keyword_like),
                RagQaRecord.answer.ilike(keyword_like),
            )
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be earlier than or equal to end_date",
        )

    if start_date:
        start_datetime = datetime.combine(start_date, time.min)
        query = query.filter(RagQaRecord.created_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, time.max)
        query = query.filter(RagQaRecord.created_at <= end_datetime)

    return query


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


@router.get("/history", response_model=RagHistoryListResponse)
def list_rag_history(
    knowledge_base_id: int,
    keyword: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=knowledge_base_id,
    )

    query = build_rag_history_query(
        db=db,
        user_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )

    total = query.count()

    records = (
        query
        .order_by(RagQaRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return RagHistoryListResponse(
        knowledge_base_id=knowledge_base_id,
        total=total,
        skip=skip,
        limit=limit,
        items=records,
    )
    

@router.delete("/history", response_model=RagHistoryDeleteResponse)
def delete_rag_history_batch(
    knowledge_base_id: int,
    keyword: str | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=knowledge_base_id,
    )

    query = build_rag_history_query(
        db=db,
        user_id=current_user.id,
        knowledge_base_id=knowledge_base_id,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )

    deleted_count = query.count()

    query.delete(synchronize_session=False)
    db.commit()

    return RagHistoryDeleteResponse(
        knowledge_base_id=knowledge_base_id,
        deleted_count=deleted_count,
        message="RAG history records deleted successfully",
    )


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


@router.get("/history/{history_id}/export")
def export_rag_history(
    history_id: int,
    format: str = Query("pdf", regex="^(pdf|markdown)$"),
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
        raise HTTPException(status_code=404, detail="RAG history record not found")

    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=record.knowledge_base_id,
    )

    if format.lower() == "markdown":
        content = generate_markdown(record)
        return StreamingResponse(
            BytesIO(content.encode("utf-8")),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=rag_{history_id}.md"},
        )
    else:
        buffer = generate_pdf_bytes(record)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=rag_{history_id}.pdf"},
        )