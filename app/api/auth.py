import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead


router = APIRouter(prefix="/auth", tags=["auth"])


def make_slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "workspace"


@router.post("/register", response_model=UserRead)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if user_in.username:
        existing_username = (
            db.query(User).filter(User.username == user_in.username).first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=hash_password(user_in.password),
    )

    db.add(user)
    db.flush()

    base_name = user_in.full_name or user_in.username or user_in.email.split("@")[0]
    organization_name = f"{base_name}'s Workspace"
    base_slug = make_slug(base_name)

    slug = base_slug
    counter = 1

    while db.query(Organization).filter(Organization.slug == slug).first():
        counter += 1
        slug = f"{base_slug}-{counter}"

    organization = Organization(
        name=organization_name,
        slug=slug,
    )

    db.add(organization)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role="owner",
    )

    db.add(membership)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=user.id)

    return Token(access_token=access_token)