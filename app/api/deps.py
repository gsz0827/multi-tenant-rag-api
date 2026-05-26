from fastapi import HTTPException, status
from sqlalchemy.orm import Session

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
