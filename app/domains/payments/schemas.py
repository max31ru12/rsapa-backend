from pydantic import BaseModel, Field


class DonationRequestSchema(BaseModel):
    amount: int = Field(description="Cents")
