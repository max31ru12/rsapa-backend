from datetime import datetime, timezone

from app.domains.membership.models import MembershipStatusEnum, MembershipType, UserMembership


def check_membership_type_already_purchased(
    existing_user_membership: UserMembership,
    target_membership_type: MembershipType,
) -> bool:
    is_same = existing_user_membership.membership_type_id == target_membership_type.id
    is_active = existing_user_membership.status in {
        MembershipStatusEnum.ACTIVE,
        MembershipStatusEnum.TRIALING,
        MembershipStatusEnum.PAST_DUE,
    }
    not_expired = existing_user_membership.end_date > datetime.utcnow().replace(tzinfo=timezone.utc)

    return is_same and is_active and not_expired


def check_session_is_locked(user_membership: UserMembership) -> bool:
    is_status_incomplete = user_membership.status == MembershipStatusEnum.INCOMPLETE
    checkout_locked = bool(user_membership.checkout_session_expires_at) and (
        user_membership.checkout_session_expires_at > datetime.now(tz=timezone.utc)
    )

    return is_status_incomplete and checkout_locked
