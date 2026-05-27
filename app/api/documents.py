from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_accessible_knowledge_base
from app.api.users import get_current_user
from app.db.session import get_db
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.membership import Membership
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead


router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentRead)
def create_document(
    document_in: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=document_in.knowledge_base_id,
    )

    document = Document(
        knowledge_base_id=document_in.knowledge_base_id,
        filename=document_in.filename,
        content_type=document_in.content_type,
        file_size=document_in.file_size,
        status="pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("", response_model=list[DocumentRead])
def list_documents(
    knowledge_base_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=knowledge_base_id,
    )

    documents = (
        db.query(Document)
        .filter(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return documents


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=document.knowledge_base_id,
    )

    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    knowledge_base = get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=document.knowledge_base_id,
    )

    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == current_user.id,
            Membership.organization_id == knowledge_base.organization_id,
        )
        .first()
    )

    if membership is None or membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can delete documents",
        )

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}
