from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.database.setup_db import session_getter
from app.domains.auth.schemas import AccessToken, JWTTokenResponse, LoginForm, RegisterFormData
from app.domains.auth.services import AuthServiceDep
from app.domains.auth.use_cases import RegisterResponses, get_subscriptions
from app.domains.auth.utils import (
    CurrentUserDep,
    RefreshTokenDep,
    create_access_token,
    create_refresh_token,
)
from app.domains.users.schemas import User
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    summary="User registration",
    responses=RegisterResponses.responses,
    status_code=201,
)
async def register(
    register_form_data: RegisterFormData,
    auth_service: AuthServiceDep,
) -> User:
    user = await auth_service.register_user(register_form_data)
    return User.from_orm(user)


class LoginResponses(Responses):
    WRONG_CREDENTIALS = 401, "Wrong credentials"


@router.post("/login", summary="User login", responses=LoginResponses.responses)
async def login(
    response: Response,
    login_data: LoginForm,
    user_service: UserServiceDep,
) -> JWTTokenResponse:
    email, password, remember = login_data.model_dump().values()
    user = await user_service.get_by_kwargs(email=email)

    if user is None or not user.verify_password(password):
        raise LoginResponses.WRONG_CREDENTIALS

    access_token = create_access_token({"email": user.email})
    refresh_token = create_refresh_token({"email": user.email}, remember_me=remember)

    # Optional adding access_token into Headers
    response.headers["Authorization"] = f"Bearer {access_token}"
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

    return JWTTokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token_payload: RefreshTokenDep,
) -> AccessToken:
    access_token = create_access_token({"email": refresh_token_payload["email"]})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return AccessToken(access_token=access_token)


@router.post("/logout")
async def logout(response: Response) -> str:
    response.delete_cookie("refresh_token")
    return "successfully logged out"


@router.get("/subscriptions")
async def get_all_subscriptions(session: Annotated[AsyncSession, Depends(session_getter)]):
    subscriptions = await get_subscriptions(session)
    return subscriptions


@router.get("/current-user")
async def get_current_user(user: CurrentUserDep) -> User:
    return user
