from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_exception_responses import Responses

from app.core.database.base_repository import InvalidOrderAttributeError
from app.core.request_params import OrderingParamsDep, PaginationParamsDep
from app.core.responses import InvalidRequestParamsResponses, PaginatedResponse
from app.domains.auth.utils import AdminUserDep
from app.domains.feedback.filters import ContactMessagesFilter
from app.domains.feedback.models import ContactMessageSchema, CreateContactMessageSchema
from app.domains.feedback.services import ContactMessageServiceDep

router = APIRouter(prefix="/contact-messages", tags=["Contact Messages"])


@router.post("/")
async def create_contact_message(
    contact_message_service: ContactMessageServiceDep, message_data: CreateContactMessageSchema
) -> ContactMessageSchema:
    contact_message = await contact_message_service.create_contact_message(message_data)
    return ContactMessageSchema.from_orm(contact_message)


@router.get("/", responses=InvalidRequestParamsResponses.responses)
async def get_contact_messages(
    admin: AdminUserDep,  # noqa Admin auth argument
    contact_message_service: ContactMessageServiceDep,
    params: PaginationParamsDep,
    ordering: OrderingParamsDep = None,
    filters: Annotated[ContactMessagesFilter, Depends()] = None,
) -> PaginatedResponse[ContactMessageSchema]:
    try:
        messages, messages_count = await contact_message_service.get_all_paginated_counted(
            order_by=ordering,
            filters=filters.model_dump(exclude_none=True),
            limit=params["limit"],
            offset=params["offset"],
        )
        data = [ContactMessageSchema.from_orm(message) for message in messages]
        return PaginatedResponse(
            count=messages_count,
            data=data,
            page=params["page"],
            page_size=params["page_size"],
        )
    except InvalidOrderAttributeError:
        raise InvalidRequestParamsResponses.INVALID_SORTER_FIELD


class AnswerContactMessageResponses(Responses):
    CONTACT_MESSAGE_NOT_FOUND = 404, "There is no contact message with provided id"


@router.post(
    "/{message_id}/answers",
    responses=AnswerContactMessageResponses.responses,
    status_code=201,
    summary="Creates an answer for the contact request",
)
async def answer_contact_message(
    message_id: int,
    subject: str,
    answer_message: str,
    admin: AdminUserDep,  # noqa Admin auth argument
    contact_message_service: ContactMessageServiceDep,
):
    try:
        await contact_message_service.answer_contact_message(message_id, subject, answer_message)
    except ValueError:
        raise AnswerContactMessageResponses.CONTACT_MESSAGE_NOT_FOUND
    return "Answered"
