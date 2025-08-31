from datetime import datetime, timedelta, timezone

import stripe

from app.core.config import settings
from app.domains.membership.models import MembershipStatusEnum, UserMembershipSchema
from app.domains.membership.services import MembershipService

stripe.api_key = settings.STRIPE_API_KEY


async def process_checkout_session_completed(
    data: dict,
    metadata: dict,
    service: MembershipService,
) -> UserMembershipSchema:
    subscription_id = data["subscription"]
    subscription = stripe.Subscription.retrieve(subscription_id)
    user_membership_id = int(metadata["user_membership_id"])

    update_data = {
        "status": MembershipStatusEnum(subscription.status),
        "stripe_subscription_id": subscription_id,
    }
    end_date = subscription.get("current_period_end")

    if end_date:
        update_data["end_date"] = datetime.fromtimestamp(end_date, tz=timezone.utc)
    else:
        update_data["end_date"] = datetime.utcnow() + timedelta(days=365)

    user_membership = await service.update_user_membership(user_membership_id, update_data)

    return UserMembershipSchema.from_orm(user_membership)


async def process_customer_subscription_updated(
    data: dict,
    service: MembershipService,
) -> UserMembershipSchema | None:
    user_membership = await service.get_membership_by_kwargs(stripe_subscription_id=data["id"])
    if not user_membership:
        return  # опционально залогировать/проигнорировать

    update_data = {"status": MembershipStatusEnum(data["status"])}
    end_date = data.get("current_period_end")
    if end_date:
        update_data["end_date"] = datetime.fromtimestamp(end_date, tz=timezone.utc)

    user_membership = await service.update_user_membership(user_membership.id, update_data)

    return UserMembershipSchema.from_orm(user_membership)


async def process_customer_subscription_deleted(
    data: dict,
    service: MembershipService,
) -> UserMembershipSchema | None:
    stripe_sub_id = data["id"]
    user_membership = await service.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
    if user_membership:
        user_membership = await service.update_user_membership(
            user_membership.id, {"status": MembershipStatusEnum.CANCELED}
        )
    return UserMembershipSchema.from_orm(user_membership)


async def process_invoice_payment_failed(
    data: dict,
    service: MembershipService,
) -> UserMembershipSchema | None:
    # Неоплата подписки
    stripe_sub_id = data["id"]
    membership = await service.get_membership_by_kwargs(stripe_subscription_id=stripe_sub_id)
    if membership:
        user_membership = await service.update_user_membership(membership.id, {"status": MembershipStatusEnum.PAST_DUE})
        return UserMembershipSchema.from_orm(user_membership)
