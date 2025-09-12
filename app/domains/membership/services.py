from datetime import datetime, timezone
from typing import Annotated, Any, Sequence

import stripe
from fastapi.params import Depends
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from stripe import Invoice

from app.core.config import settings
from app.domains.membership.infrastructure import MembershipUnitOfWork, get_membership_unit_of_work
from app.domains.membership.models import MembershipStatusEnum, MembershipType, UserMembership
from app.domains.payments.models import PaymentStatus, PaymentType

stripe.api_key = settings.STRIPE_API_KEY


logger.add("logs/invoice_info.log", rotation="365 days", level="INFO")


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

        stripe.Subscription.modify(membership.stripe_subscription_id, cancel_at_period_end=True)

    async def resume_membership(self, user_id):
        membership = await self.get_membership_by_kwargs(user_id=user_id, status=MembershipStatusEnum.ACTIVE)

        if membership is None:
            raise ValueError("Active membership with provided ID not found")

        stripe.Subscription.modify(membership.stripe_subscription_id, cancel_at_period_end=False)

    async def create_subscription_initial_payment(self, invoice: Invoice, payment_type: PaymentType):
        """Creates payment in case of invoice.paid"""
        subscription_details = invoice.parent.subscription_details
        line = invoice.lines.data[0]
        price_details = line.pricing.price_details

        async with self.uow:
            exists = await self.uow.payment_repository.get_first_by_kwargs(invoice_id=invoice.id)
            if exists:
                return
            await self.uow.payment_repository.create(
                type=payment_type,
                status=PaymentStatus.SUCCEEDED,
                amount_total=invoice.total,
                currency=invoice.currency,
                billing_reason=invoice.billing_reason,
                # stripe ids
                invoice_id=invoice.id,
                subscription_id=subscription_details.subscription,
                stripe_customer_id=invoice.customer.id,
                charge_id=invoice.get("charge"),
                # price_product
                price_id=price_details.price,
                product_id=price_details.product,
                # invoice context,
                livemode=invoice.livemode,
                description=invoice.description,
                _metadata=subscription_details.metadata,
                stripe_created_at=datetime.fromtimestamp(invoice.created, tz=timezone.utc),
            )

    async def handle_invoice_paid(self, data, parent) -> None:
        invoice_id = data["id"]
        invoice = stripe.Invoice.retrieve(
            invoice_id, expand=["subscription", "customer", "payment_intent.latest_charge"]
        )
        billing_reason = invoice.billing_reason
        metadata = parent.get("subscription_details", {}).get("metadata", {})
        user_membership_id = metadata.get("user_membership_id")

        if billing_reason == "subscription_create":
            subscription_details = parent.get("subscription_details", {})
            subscription_id = subscription_details.get("subscription")
            payment_type = PaymentType.SUBSCRIPTION_INITIAL
        elif billing_reason == "subscription_cycle":
            subscription_details = parent.get("subscription_details", {})
            subscription_id = subscription_details.get("subscription")
            payment_type = PaymentType.SUBSCRIPTION_RENEWAL
        else:
            subscription_id = invoice.get("subscription")
            payment_type = PaymentType.SUBSCRIPTION_RENEWAL

        subscription = stripe.Subscription.retrieve(subscription_id)
        items = subscription.get("items", {}).get("data", [])

        if not items:
            raise ValueError("No subscription items found")

        current_period_end = items[0].get("current_period_end")

        if current_period_end is not None:
            current_period_end = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

        update_data = {
            "status": MembershipStatusEnum(subscription.status),
            "stripe_subscription_id": subscription.id,
            "current_period_end": current_period_end,
            "stripe_customer_id": invoice.customer.id,
            "has_access": True,
            "checkout_url": None,
            "checkout_session_expires_at": None,
            "latest_invoice_id": invoice.id,
        }
        payment_exists = await self.uow.payment_repository.get_first_by_kwargs(invoice_id=invoice_id)

        if not payment_exists:
            await self.create_subscription_initial_payment(invoice, payment_type)

        await self.update_user_membership(int(user_membership_id), update_data)

        logger.info(
            f"""Event type: invoice.paid
            user membership ID: {user_membership_id}
            stripe subscription id: {subscription.id}
            invoice ID: {invoice_id}
            subscription status: {subscription.status}
            metadata: {metadata}\n"""
        )

    async def handle_customer_subscription_updated(self, data) -> None:
        user_membership = await self.get_membership_by_kwargs(stripe_subscription_id=data["id"])
        if not user_membership:
            raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")

        update_data = {"status": MembershipStatusEnum(data["status"])}
        current_period_end = data.get("current_period_end")
        cancel_at_period_end = data.get("cancel_at_period_end")

        if current_period_end is not None:
            update_data["current_period_end"] = datetime.fromtimestamp(current_period_end, tz=timezone.utc)

        if cancel_at_period_end is not None:
            update_data["cancel_at_period_end"] = cancel_at_period_end

        await self.update_user_membership(user_membership.id, update_data)

        logger.info(
            f"""
            Event type: customer.subscription.updated
            User membership ID: {user_membership.id}
            Stripe subscription ID: {data["id"]}
            Membership status: {data["status"]}
            current_period_end: {current_period_end}
            cancel_at_period_end: {cancel_at_period_end}\n
            """
        )

    async def handle_invoice_payment_failed(self, data) -> None:
        stripe_sub_id = data["id"]
        user_membership = await self.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
        if user_membership:
            await self.update_user_membership(user_membership.id, {"status": MembershipStatusEnum.PAST_DUE})
            logger.info(
                f"""
                Event type: invoice.payment_failed
                Membership ID: {user_membership.id}
                Stripe subscription ID: {stripe_sub_id}
                Stripe subscription status: {MembershipStatusEnum.PAST_DUE}\n
                """
            )
        else:
            raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")

    async def handle_customer_subscription_deleted(self, data) -> None:
        stripe_sub_id = data["id"]
        user_membership = await self.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
        if user_membership:
            await self.update_user_membership(user_membership.id, {"status": MembershipStatusEnum.CANCELED})
        else:
            raise ValueError("Membership with provided STRIPE_SUBSCRIPTION_ID not found")
        logger.info(
            f"""
                Event type: invoice.payment_failed
                Membership ID: {user_membership.id}
                Stripe subscription ID: {stripe_sub_id}
                Stripe subscription status: {MembershipStatusEnum.PAST_DUE}\n
            """
        )

    async def process_stripe_webhook_event(self, event):  # noqa
        data = event["data"]["object"]
        parent = data.get("parent", {})

        if event.type == "invoice.paid":
            await self.handle_invoice_paid(data, parent)

        elif event.type == "customer.subscription.updated":
            await self.handle_customer_subscription_updated(data)

        elif event.type == "payment_intent.payment_failed":
            pass  # вызывается при отклонеии карты в checkout session

        elif event.type == "invoice.payment_failed":
            # вызывается когда не удалось провести месячный платеж
            await self.handle_invoice_payment_failed(data)

        elif event.type == "customer.subscription.deleted":
            await self.handle_customer_subscription_deleted(data)
        return


def get_membership_service(
    uow: Annotated[MembershipUnitOfWork, Depends(get_membership_unit_of_work)],
) -> MembershipService:
    return MembershipService(uow)


MembershipServiceDep = Annotated[MembershipService, Depends(get_membership_service)]
