from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    stuff: bool
    description: str | None
    created_at: datetime
    institution: str
    role: str

    model_config = {
        "from_attributes": True,
    }
