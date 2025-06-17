from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: int
    firstname: str
    lastname: str
    email: str
    stuff: bool
    description: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }
