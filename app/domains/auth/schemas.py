from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterFormData(BaseModel):
    email: EmailStr = Field(min_length=6)
    password: str = Field(min_length=4)
    repeat_password: str = Field(min_length=4)
    firstname: str = Field(min_length=2)
    lastname: str = Field(min_length=2)
    institution: str = Field(min_length=2)
    role: str = Field(min_length=2)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match")
        return self


class LoginForm(BaseModel):
    email: str
    password: str
    remember: bool = False

    class Config:
        json_schema_extra = {"examples": [{"email": "admin@mail.com", "password": "admin", "remember": True}]}


class AccessToken(BaseModel):
    access_token: str
    type: str = "Bearer"


class JWTTokenResponse(AccessToken):
    refresh_token: str | None
