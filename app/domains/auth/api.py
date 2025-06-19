from fastapi import APIRouter
from fastapi_exception_responses import Responses
from starlette.responses import Response

from app.domains.auth.schemas import RegisterFormData, LoginForm, JWTTokenResponse
from app.domains.auth.utils import (
    create_access_token,
    create_refresh_token,
    RefreshTokenDep,
    CurrentUserDep,
)
from app.domains.users.services import UserServiceDep

router = APIRouter(tags=["Authentication"])


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


@router.post(
    "/register",
    summary="User registration",
    responses=RegisterResponses.get_responses()
)
async def register(
        register_form_data: RegisterFormData,
        user_service: UserServiceDep,
):
    data = register_form_data.model_dump()

    if (await user_service.get_by_kwargs(email=data["email"])) is not None:
        raise RegisterResponses.EMAIL_ALREADY_IN_USE

    if data["password"] != data["repeat_password"]:
        raise RegisterResponses.PASSWORDS_DONT_MATCH

    del data["repeat_password"]
    new_user = await user_service.create(**data)
    return new_user


class LoginResponses(Responses):
    WRONG_CREDENTIALS = 401, "Wrong credentials"


@router.post(
    "/login",
    summary="User login",
    responses=LoginResponses.get_responses()
)
async def login(
        response: Response,
        login_data: LoginForm,
        user_service: UserServiceDep,
):
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
        refresh_token: RefreshTokenDep,
):
    access_token = create_access_token({"email": refresh_token})
    response.headers["Authorization"] = f"Bearer {access_token}"
    return {"access_token": access_token}


@router.get("/current-user")
async def get_current_user(user: CurrentUserDep):
    return user

