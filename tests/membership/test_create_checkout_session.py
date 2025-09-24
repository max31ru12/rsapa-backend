import json
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient

from app.domains.memberships.models import ApprovalStatusEnum, MembershipStatusEnum

pytestmark = pytest.mark.anyio


available_for_users_membership_types_ids = [1, 2, 3, 5]

purchased_membership_statuses = [
    MembershipStatusEnum.ACTIVE,
    MembershipStatusEnum.TRIALING,
    MembershipStatusEnum.PAST_DUE,
]


@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_create_checkout_session(
    client: AsyncClient, membership_uow, authentication_data, faker: Faker, membership_type_id
) -> None:
    authorization_header, refresh_token_cookie, email = authentication_data
    response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=authorization_header,
    )

    async with membership_uow:
        user = await membership_uow.user_repository.get_first_by_kwargs(email=email)
        created_user_membership = await membership_uow.user_membership_repository.get_first_by_kwargs(user_id=user.id)

    assert response.status_code == 201
    assert created_user_membership.membership_type_id == membership_type_id
    assert created_user_membership.status == MembershipStatusEnum.INCOMPLETE
    assert json.loads(response.text).startswith("https://checkout.stripe.com")


@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_user_not_authorized(
    client: AsyncClient,
    membership_type_id,
) -> None:
    response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
    )

    assert response.status_code == 401


async def test_purchasing_honorary_membership(
    client: AsyncClient,
    membership_uow,
    authentication_data,
) -> None:
    authorization_header, refresh_token_cookie, email = authentication_data
    honorary_membership_id = 4
    response = await client.post(
        f"api/memberships/membership-types/{honorary_membership_id}/checkout-sessions",
        headers=authorization_header,
    )

    assert response.status_code == 403


@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_checkout_session_lock(
    client: AsyncClient, membership_uow, authentication_data, faker: Faker, membership_type_id
):
    authorization_header, refresh_token_cookie, email = authentication_data

    first_response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=authorization_header,
    )
    second_response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=authorization_header,
    )

    assert first_response.json() == second_response.json()


@pytest.mark.parametrize("membership_status", purchased_membership_statuses)
@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_membership_already_purchased(
    client: AsyncClient,
    membership_uow,
    authentication_data,
    faker: Faker,
    membership_type_id: int,
    membership_status: MembershipStatusEnum,
) -> None:
    authorization_header, refresh_token_cookie, email = authentication_data

    user = await membership_uow.user_repository.get_first_by_kwargs(email=email)

    async with membership_uow:
        await membership_uow.user_membership_repository.create(
            status=membership_status,
            approval_status=ApprovalStatusEnum.PENDING,
            user_id=user.id,
            membership_type_id=membership_type_id,
        )

    response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=authorization_header,
    )

    assert response.status_code == 409


@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_expired_checkout_session_creates_new_session(
    client: AsyncClient,
    membership_uow,
    authentication_data,
    membership_type_id,
):
    authorization_header, refresh_token_cookie, email = authentication_data

    async with membership_uow:
        user = await membership_uow.user_repository.get_first_by_kwargs(email=email)

        old_checkout_url = "https://checkout.stripe.com/old-session"
        await membership_uow.user_membership_repository.create(
            status=MembershipStatusEnum.INCOMPLETE,
            approval_status=ApprovalStatusEnum.APPROVED,
            user_id=user.id,
            membership_type_id=membership_type_id,
            checkout_url=old_checkout_url,
            checkout_session_expires_at=datetime.now(tz=timezone.utc) - timedelta(minutes=1),
        )

    response = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=authorization_header,
    )

    assert response.status_code == 201
    assert response.text != old_checkout_url
    assert response.text.startswith('"https://checkout.stripe.com')

    async with membership_uow:
        updated_membership = await membership_uow.user_membership_repository.get_first_by_kwargs(user_id=user.id)
        assert updated_membership.checkout_url != old_checkout_url
        assert updated_membership.checkout_session_expires_at > datetime.now(tz=timezone.utc)


@pytest.mark.parametrize("membership_type_id", available_for_users_membership_types_ids)
async def test_multiple_users_can_create_independent_sessions(
    client: AsyncClient,
    membership_uow,
    authentication_data_factory,
    membership_type_id,
):
    auth_1, _, email_1 = await authentication_data_factory()
    async with membership_uow:
        user_1 = await membership_uow.user_repository.get_first_by_kwargs(email=email_1)
        await membership_uow.user_membership_repository.create(
            status=MembershipStatusEnum.INCOMPLETE,
            approval_status=ApprovalStatusEnum.APPROVED,
            user_id=user_1.id,
            membership_type_id=membership_type_id,
            checkout_url="https://checkout.stripe.com/active-session-user1",
            checkout_session_expires_at=datetime.now(tz=timezone.utc) + timedelta(minutes=30),
        )

    response_1 = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=auth_1,
    )
    assert response_1.status_code == 200 or response_1.status_code == 201
    session_url_1 = response_1.json() if isinstance(response_1.json(), str) else response_1.text
    assert "stripe.com" in session_url_1

    auth_2, _, email_2 = await authentication_data_factory()
    response_2 = await client.post(
        f"api/memberships/membership-types/{membership_type_id}/checkout-sessions",
        headers=auth_2,
    )
    session_url_2 = response_2.json() if isinstance(response_2.json(), str) else response_2.text
    assert response_2.status_code == 201
    assert "stripe.com" in session_url_2
    assert session_url_1 != session_url_2

    async with membership_uow:
        user_2 = await membership_uow.user_repository.get_first_by_kwargs(email=email_2)
        membership_1 = await membership_uow.user_membership_repository.get_first_by_kwargs(user_id=user_1.id)
        membership_2 = await membership_uow.user_membership_repository.get_first_by_kwargs(user_id=user_2.id)

        assert membership_1.user_id != membership_2.user_id
        assert membership_1.checkout_url != membership_2.checkout_url
