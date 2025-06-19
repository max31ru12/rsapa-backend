from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, APIKeyHeader
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.domains.users.models import User
from app.domains.users.services import UserServiceDep

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
refresh_token_cookie = APIKeyCookie(name="refresh_token", auto_error=False)
access_token_header = APIKeyHeader(name="Authorization", auto_error=False)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_LIFESPAN_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, remember_me: bool = False) -> str:
    data_to_encode = data.copy()
    if remember_me:
        lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS)
    else:
        lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME_DAYS_NOT_REMEMBER)
    expire = datetime.now() + lifetime
    data_to_encode.update({"exp": expire})
    refresh_token = jwt.encode(data_to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return refresh_token


def validate_bearer_token(authorization_header_value: str) -> str:
    if "Bearer" in authorization_header_value:
        _, access_token = authorization_header_value.split(" ")
        return access_token
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def verify_refresh_token(refresh_token: Annotated[str, Depends(refresh_token_cookie)]) -> dict | None:

    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")


async def get_current_user(
        user_service: UserServiceDep,
        access_token: str = Depends(access_token_header),
) -> User | None:
    access_token = validate_bearer_token(access_token)
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = payload.get("email")

    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await user_service.get_by_kwargs(email=email)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user


RefreshTokenDep = Annotated[str, Depends(verify_refresh_token)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
