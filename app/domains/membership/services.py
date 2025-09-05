from datetime import datetime, timezone
from typing import Annotated, Any, Sequence

import stripe
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.domains.membership.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.membership.models import MembershipStatusEnum, MembershipType, UserMembership

stripe.api_key = settings.STRIPE_API_KEY


class MembershipService:
    def __init__(self, uow):
        self.uow: MembershipUnitOfWork = uow

    async def get_all_membership_types(self) -> Sequence[MembershipType]:
        async with self.uow:
            return await self.uow.membership_repository.list()

    async def get_membership_type_by_kwargs(self, **kwargs) -> MembershipType:
        async with self.uow:
            return await self.uow.membership_repository.get_first_by_kwargs(**kwargs)

    async def update_membership_type(self, membership_type_id: int, update_data: dict) -> MembershipType:
        async with self.uow:
            return await self.uow.membership_repository.update(membership_type_id, update_data)

    async def get_all_paginated_counted_user_memberships(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ) -> [list[UserMembership], int]:
        async with self.uow:
            return await self.uow.user_membership_repository.list(limit, offset, order_by, filters)

    async def create_membership(self, **kwargs) -> UserMembership:
        async with self.uow:
            return await self.uow.user_membership_repository.create(**kwargs)

    async def get_membership_by_kwargs(self, **kwargs) -> UserMembership:
        stmt = select(UserMembership).options(
            selectinload(UserMembership.user), selectinload(UserMembership.membership_type)
        )
        async with self.uow:
            return await self.uow.user_membership_repository.get_first_by_kwargs(stmt, **kwargs)

    async def update_user_membership(self, user_membership_id: int, update_data: dict) -> UserMembership:
        async with self.uow:
            return await self.uow.user_membership_repository.update(user_membership_id, update_data)

    async def get_joined_membership(
        self, limit: int = None, offset: int = None, order_by: str = None, filters: dict[str, Any] = None
    ):
        stmt = (
            select(UserMembership)
            .join(UserMembership.user)
            .join(UserMembership.membership_type)
            .options(selectinload(UserMembership.user), selectinload(UserMembership.membership_type))
        )
        async with self.uow:
            result = await self.uow.user_membership_repository.list(limit, offset, order_by, filters, stmt)
            return result

    async def cancel_membership(self, user_id: int):
        membership = await self.get_membership_by_kwargs(user_id=user_id, status=MembershipStatusEnum.ACTIVE)

        if membership is None:
            raise ValueError("Active membership with provided ID not found")

        # updated_membership = await self.update_user_membership(membership.id, {"status": MembershipStatusEnum.CANCELED})
        stripe.Subscription.modify(membership.stripe_subscription_id, cancel_at_period_end=True)

        # return updated_membership

    async def process_stripe_webhook_event(self, event):  # noqa
        data = event["data"]["object"]
        parent = data.get("parent", {})
        metadata = parent.get("subscription_details", {}).get("metadata", {})
        user_membership_id = metadata.get("user_membership_id")

        if event.type == "invoice.paid":
            invoice_id = data["id"]

            invoice = stripe.Invoice.retrieve(invoice_id, expand=["subscription", "customer"])

            if invoice.get("billing_reason") == "subscription_create":
                subscription_details = parent.get("subscription_details", {})
                subscription_id = subscription_details.get("subscription")
            else:
                subscription_id = invoice.get("subscription")

            subscription = stripe.Subscription.retrieve(subscription_id)

            items = subscription.get("items", {}).get("data", [])
            if not items:
                raise ValueError("No subscription items found")

            current_period_end = items[0].get("current_period_end")
            if current_period_end:
                current_period_end = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

            update_data = {
                "status": MembershipStatusEnum(subscription.status),
                "stripe_subscription_id": subscription.id,
                "current_period_end": current_period_end,
                "stripe_customer_id": invoice["customer"]["id"],
                "has_access": True,
                "checkout_url": None,
                "checkout_session_expires_at": None,
            }

            await self.update_user_membership(int(user_membership_id), update_data)

        elif event.type == "customer.subscription.updated":
            user_membership = await self.get_membership_by_kwargs(stripe_subscription_id=data["id"])
            if not user_membership:
                raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")

            update_data = {"status": MembershipStatusEnum(data["status"])}
            current_period_end = data.get("current_period_end")
            if current_period_end:
                update_data["current_period_end"] = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

            if cancel_at_period_end := data.get("cancel_at_period_end"):
                update_data["cancel_at_period_end"] = cancel_at_period_end

            await self.update_user_membership(user_membership.id, update_data)

        elif event.type == "payment_intent.payment_failed":
            pass  # вызывается при отклонеии карты в checkout session

        elif event.type == "invoice.payment_failed":
            # вызывается когда не удалось провести месячный платеж
            stripe_sub_id = data["id"]
            membership = await self.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
            if membership:
                await self.update_user_membership(membership.id, {"status": MembershipStatusEnum.PAST_DUE})
            else:
                raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")

        elif event.type == "customer.subscription.deleted":
            stripe_sub_id = data["id"]
            user_membership = await self.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
            if user_membership:
                await self.update_user_membership(user_membership.id, {"status": MembershipStatusEnum.CANCELED})
            else:
                raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")

        return


def get_membership_service(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
