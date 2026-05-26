from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationRead


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=list[OrganizationRead])
def read_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    organizations = (
        db.query(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == current_user.id)
        .all()
    )

    return organizations