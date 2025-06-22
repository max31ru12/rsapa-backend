from pydantic import BaseModel


class RegisterFormData(BaseModel):
    email: str
    password: str
    repeat_password: str
    firstname: str
    lastname: str
    institution: str
    role: str
    subscription_id: int


class LoginForm(BaseModel):
    email: str
    password: str
    remember: bool = False


class AccessToken(BaseModel):
    access_token: str
    type: str = "Bearer"


class JWTTokenResponse(AccessToken):
    refresh_token: str | None
