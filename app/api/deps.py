from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.models.membership import Membership
from app.models.user import User


def check_organization_membership(
    db: Session,
    user: User,
    organization_id: int,
) -> Membership:
    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id,
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization",
        )

    return membership


def get_accessible_knowledge_base(
    db: Session,
    user: User,
    knowledge_base_id: int,
) -> KnowledgeBase:
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
        user=user,
        organization_id=knowledge_base.organization_id,
    )

    return knowledge_base