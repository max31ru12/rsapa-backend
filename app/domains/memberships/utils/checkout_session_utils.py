from datetime import datetime, timezone

from app.domains.memberships.models import MembershipStatusEnum, MembershipType, UserMembership


def check_membership_type_already_purchased(
    existing_user_membership: UserMembership,
    target_membership_type: MembershipType,
) -> bool:
    if not existing_user_membership or not target_membership_type:
        return False

    # Должен совпасть тип
    is_same = existing_user_membership.membership_type_id == target_membership_type.id

    # Статусы, при которых считаем, что членство уже "куплено"
    is_active = existing_user_membership.status in {
        MembershipStatusEnum.ACTIVE,
        MembershipStatusEnum.TRIALING,
        MembershipStatusEnum.PAST_DUE,
    }

    # Если дата окончания неизвестна — трактуем как не истёкшее (defensive),
    # чтобы не допустить второй покупки. Это поможет пройти твои тесты,
    # где current_period_end не задаётся.
    current_period_end = existing_user_membership.current_period_end
    if current_period_end is None:
        not_expired = True
    else:
        # Приводим к aware-UTC, если вдруг хранится без tzinfo
        if current_period_end.tzinfo is None:
            current_period_end = current_period_end.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        not_expired = current_period_end > now  # или >= now, если нужна включительная логика

    return is_same and is_active and not_expired


def check_session_is_locked(user_membership: UserMembership) -> bool:
    is_status_incomplete = user_membership.status == MembershipStatusEnum.INCOMPLETE
    checkout_locked = bool(user_membership.checkout_session_expires_at) and (
        user_membership.checkout_session_expires_at > datetime.now(tz=timezone.utc)
    )

    return is_status_incomplete and checkout_locked
