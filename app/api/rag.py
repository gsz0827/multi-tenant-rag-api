from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_accessible_knowledge_base
from app.api.users import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.rag import RagAskRequest, RagAskResponse, RagSourceChunk
from app.services.embedding_service import create_embedding
from app.services.llm_service import generate_answer_with_context


router = APIRouter(prefix="/rag", tags=["rag"])


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

    query_embedding = create_embedding(request.question)

    rows = (
        db.query(
            DocumentChunk,
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
        distance = float(row[1])
        score = 1 / (1 + distance)

        sources.append(
            RagSourceChunk(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )

        context_parts.append(
            f"[Chunk {index} | document_id={chunk.document_id} | "
            f"chunk_id={chunk.id} | chunk_index={chunk.chunk_index}]\n"
            f"{chunk.content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    answer = generate_answer_with_context(
        question=request.question,
        context=context,
    )

    return RagAskResponse(
        answer=answer,
        sources=sources,
    )
