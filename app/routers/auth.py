from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_password,
    decode_token
)
from app.models.user import User, AuthProvider
from app.schemas.user import UserRegister, UserLogin, UserResponse, RefreshRequest, TokenResponse
from app.services.oauth_service import (
    get_github_auth_url,
    get_github_user,
    get_google_auth_url,
    get_google_user
)
from app.utils.validators import validate_password_strength

router = APIRouter(prefix="/auth", tags=["Auth"])

def _build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserResponse.model_validate(user),
    )
 
 
def _get_user_or_404(user_id: int, db: Session) -> User:
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    validate_password_strength(payload.password)
    
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        provider=AuthProvider.local
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credientials")
    
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credientials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token, expected_type="refresh")
    user = _get_user_or_404(int(data["sub"]), db)
    return _build_token_response(user)


@router.get("/google", summary="Redirect to google login")
def google_login():
    return RedirectResponse(get_google_auth_url())


@router.get("/google/callback", response_model=TokenResponse)
async def google_callback(code: str, db: Session = Depends(get_db)):
    google_user = await get_google_user(code)

    if not google_user.get("email"):
        raise HTTPException(status_code=400, detail="Google account has no email")

    user = db.query(User).filter(User.email == google_user["email"]).first()

    if not user:
        user = User(
            name=google_user.get("name", ""),
            email=google_user["email"],
            avatar_url=google_user.get("picture"),
            provider=AuthProvider.google,
            provider_id=str(google_user.get("id", "")),
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
 
    return _build_token_response(user)


@router.get("/github", summary="Redirect to GitHub login")
def github_login():
    return RedirectResponse(get_github_auth_url())
 
 
@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(code: str, db: Session = Depends(get_db)):
    github_user = await get_github_user(code)
 
    if not github_user.get("email"):
        raise HTTPException(
            status_code=400,
            detail="GitHub account has no verified public email. Please add one at github.com/settings/emails",
        )
 
    user = db.query(User).filter(User.email == github_user["email"]).first()
 
    if not user:
        user = User(
            name=github_user.get("name") or github_user.get("login", ""),
            email=github_user["email"],
            avatar_url=github_user.get("avatar_url"),
            provider=AuthProvider.github,
            provider_id=str(github_user.get("id", "")),
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
 
    return _build_token_response(user)