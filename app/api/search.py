from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_accessible_knowledge_base
from app.api.users import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse, SearchResultChunk
from app.services.embedding_service import create_embedding


router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_knowledge_base(
    search_in: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=search_in.knowledge_base_id,
    )

    query_text = search_in.query.strip()

    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    query_embedding = create_embedding(query_text)

    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label(
        "distance"
    )

    rows = (
        db.query(
            DocumentChunk,
            Document.filename.label("document_filename"),
            distance,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .filter(Document.knowledge_base_id == search_in.knowledge_base_id)
        .filter(DocumentChunk.embedding.isnot(None))
        .order_by(distance.asc())
        .limit(search_in.top_k)
        .all()
    )

    results: list[SearchResultChunk] = []

    for chunk, document_filename, distance_value in rows:
        score = 1.0 - float(distance_value)

        results.append(
            SearchResultChunk(
                document_id=chunk.document_id,
                document_filename=document_filename,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )

    return SearchResponse(
        knowledge_base_id=search_in.knowledge_base_id,
        query=query_text,
        results=results,
    )
