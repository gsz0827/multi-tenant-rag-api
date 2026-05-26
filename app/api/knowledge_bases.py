from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import check_organization_membership
from app.api.users import get_current_user
from app.db.session import get_db
from app.models.knowledge_base import KnowledgeBase
from app.models.membership import Membership
from app.models.user import User
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseRead)
def create_knowledge_base(
    knowledge_base_in: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    check_organization_membership(
        db=db,
        user=current_user,
        organization_id=knowledge_base_in.organization_id,
    )

    knowledge_base = KnowledgeBase(
        organization_id=knowledge_base_in.organization_id,
        name=knowledge_base_in.name,
        description=knowledge_base_in.description,
    )

    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)

    return knowledge_base


@router.get("", response_model=list[KnowledgeBaseRead])
def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    knowledge_bases = (
        db.query(KnowledgeBase)
        .join(Membership, Membership.organization_id == KnowledgeBase.organization_id)
        .filter(Membership.user_id == current_user.id)
        .all()
    )

    return knowledge_bases


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    knowledge_base = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == knowledge_base_id)
        .first()
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    check_organization_membership(
        db=db,
        user=current_user,
        organization_id=knowledge_base.organization_id,
    )

    return knowledge_base


@router.delete("/{knowledge_base_id}")
def delete_knowledge_base(
    knowledge_base_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    knowledge_base = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == knowledge_base_id)
        .first()
    )

    if knowledge_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    membership = check_organization_membership(
        db=db,
        user=current_user,
        organization_id=knowledge_base.organization_id,
    )

    if membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can delete knowledge bases",
        )

    db.delete(knowledge_base)
    db.commit()

    return {"message": "Knowledge base deleted"}
