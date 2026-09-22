from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.schemas import LoginRequest, SignupRequest, UserOut
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = "creatoros_session"


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=int(service.SESSION_LIFETIME.total_seconds()),
    )


@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(data: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await service.create_user(db, data)
    session = await service.create_session(db, user.id)
    _set_session_cookie(response, str(session.id))
    return user


@router.post("/login", response_model=UserOut)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await service.authenticate_user(db, data)
    session = await service.create_session(db, user.id)
    _set_session_cookie(response, str(session.id))
    return user


@router.post("/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)