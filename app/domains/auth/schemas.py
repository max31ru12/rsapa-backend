from pydantic import BaseModel


class RegisterFormData(BaseModel):
    email: str
    password: str
    repeat_password: str
    firstname: str
    lastname: str


class LoginForm(BaseModel):
    email: str
    password: str
    remember: bool = False


class AccessToken(BaseModel):
    access_token: str
    type: str = "Bearer"


class JWTTokenResponse(AccessToken):
    refresh_token: str | None
