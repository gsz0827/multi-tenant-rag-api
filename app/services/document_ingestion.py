from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_parser import parse_document_file
from app.services.text_splitter import split_text
from app.services.embedding_service import create_embedding


def build_cancelled_result(
    document: Document,
    embedded_count: int = 0,
    chunk_count: int = 0,
) -> dict:
    return {
        "document_id": document.id,
        "status": document.status,
        "text_length": len(document.extracted_text or ""),
        "chunk_count": chunk_count,
        "embedded_chunk_count": embedded_count,
        "message": "Document ingestion task was cancelled",
    }


def is_document_ready_for_rag(document: Document, db: Session) -> bool:
    if document.status != "completed":
        return False

    if not document.extracted_text:
        return False

    embedded_chunk_count = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
        .filter(DocumentChunk.embedding.isnot(None))
        .count()
    )

    return embedded_chunk_count > 0


def prepare_document_for_rag_sync(
    db: Session,
    document_id: int,
    force: bool = False,
) -> dict:
    document = db.query(Document).filter(Document.id == document_id).first()

    if document is None:
        raise ValueError("Document not found")

    if document.status == "cancelled":
        return build_cancelled_result(document=document)

    if not document.storage_path:
        document.status = "failed"
        document.error_message = "Document does not have a stored file"
        db.commit()
        raise ValueError("Document does not have a stored file")

    if not force and is_document_ready_for_rag(document=document, db=db):
        total_chunk_count = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .count()
        )

        embedded_chunk_count = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .filter(DocumentChunk.embedding.isnot(None))
            .count()
        )

        return {
            "document_id": document.id,
            "status": document.status,
            "text_length": len(document.extracted_text or ""),
            "chunk_count": total_chunk_count,
            "embedded_chunk_count": embedded_chunk_count,
            "message": "Document is already prepared for RAG",
        }

    try:
        document.status = "processing"
        document.error_message = None
        db.commit()

        extracted_text = parse_document_file(
            path=document.storage_path,
            content_type=document.content_type,
        )

        db.refresh(document)

        if document.status == "cancelled":
            db.commit()
            return build_cancelled_result(document=document)

        if not extracted_text or not extracted_text.strip():
            raise ValueError("No text could be extracted from this document")

        document.extracted_text = extracted_text
        db.commit()
        db.refresh(document)

        if document.status == "cancelled":
            db.commit()
            return build_cancelled_result(document=document)

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document.id
        ).delete()

        chunks = split_text(
            text=extracted_text,
            chunk_size=1000,
            chunk_overlap=200,
        )

        db.refresh(document)

        if document.status == "cancelled":
            db.commit()
            return build_cancelled_result(
                document=document,
                embedded_count=0,
                chunk_count=len(chunks),
            )

        embedded_count = 0

        for index, chunk_text in enumerate(chunks):
            db.refresh(document)

            if document.status == "cancelled":
                db.commit()
                return build_cancelled_result(
                    document=document,
                    embedded_count=embedded_count,
                    chunk_count=len(chunks),
                )

            embedding = create_embedding(chunk_text)

            db.refresh(document)

            if document.status == "cancelled":
                db.commit()
                return build_cancelled_result(
                    document=document,
                    embedded_count=embedded_count,
                    chunk_count=len(chunks),
                )

            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk_text,
                content_length=len(chunk_text),
                embedding=embedding,
            )
            db.add(db_chunk)
            embedded_count += 1

        db.refresh(document)

        if document.status == "cancelled":
            db.commit()
            return build_cancelled_result(
                document=document,
                embedded_count=embedded_count,
                chunk_count=len(chunks),
            )

        document.status = "completed"
        document.error_message = None

        db.commit()
        db.refresh(document)

        return {
            "document_id": document.id,
            "status": document.status,
            "text_length": len(extracted_text),
            "chunk_count": len(chunks),
            "embedded_chunk_count": embedded_count,
            "message": "Document prepared for RAG successfully",
        }

    except Exception as exc:
        db.rollback()

        document = db.query(Document).filter(Document.id == document_id).first()

        if document and document.status != "cancelled":
            document.status = "failed"
            document.error_message = str(exc)
            db.commit()

        raise