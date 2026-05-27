import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_accessible_knowledge_base
from app.api.users import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.models.membership import Membership
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead


router = APIRouter(prefix="/documents", tags=["documents"])


ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


@router.post("/upload", response_model=DocumentRead)
def upload_document(
    knowledge_base_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_accessible_knowledge_base(
        db=db,
        user=current_user,
        knowledge_base_id=knowledge_base_id,
    )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, TXT, and DOCX files are supported",
        )

    storage_root = Path(settings.STORAGE_DIR)
    document_dir = storage_root / "documents" / str(knowledge_base_id)
    document_dir.mkdir(parents=True, exist_ok=True)

    extension = get_file_extension(file.filename or "")
    stored_filename = f"{uuid.uuid4()}{extension}"
    storage_path = document_dir / stored_filename

    file_size = 0

    try:
        with storage_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break

                file_size += len(chunk)
                buffer.write(chunk)

    except Exception as exc:
        if storage_path.exists():
            storage_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {exc}",
        )

    finally:
        file.file.close()

    document = Document(
        knowledge_base_id=knowledge_base_id,
        filename=file.filename or stored_filename,
        content_type=file.content_type,
        file_size=file_size,
        storage_path=str(storage_path),
        status="pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


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

    if document.storage_path:
        path = Path(document.storage_path)
        if path.exists():
            path.unlink()

    db.delete(document)
    db.commit()

    return {"message": "Document deleted"}