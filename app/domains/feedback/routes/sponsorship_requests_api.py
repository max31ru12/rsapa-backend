from fastapi import APIRouter
from pydantic import TypeAdapter

from app.domains.feedback.models import CreateSponsorshipRequestSchema, SponsorshipRequestSchema
from app.domains.feedback.services import FeedbackServiceDep

router = APIRouter(prefix="/sponsorship-requests", tags=["Sponsorship Requests"])


@router.post("/")
async def create_sponsorship_request(
    sponsorship_request_data: CreateSponsorshipRequestSchema,
    service: FeedbackServiceDep,
) -> SponsorshipRequestSchema:
    sponsorship_request = await service.create_sponsorship_request(sponsorship_request_data)
    return SponsorshipRequestSchema.from_orm(sponsorship_request)


@router.get("/", response_model=list[SponsorshipRequestSchema])
async def get_all_sponsorship_requests(
    service: FeedbackServiceDep,
) -> list[SponsorshipRequestSchema]:
    data, _ = await service.get_all_sponsorship_requests()
    adapter = TypeAdapter(list[SponsorshipRequestSchema])
    return adapter.validate_python(data)
