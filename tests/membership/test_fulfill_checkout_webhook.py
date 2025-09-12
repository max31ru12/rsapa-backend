import hashlib
import hmac

import pytest
from faker import Faker
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


def _stripe_sig(secret: str, raw_body: bytes, ts: int) -> str:
    payload = f"{ts}.{raw_body.decode('utf-8')}".encode("utf-8")
    v1 = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={v1}"


async def test_invalid_signature(
    client: AsyncClient,
    faker: Faker,
) -> None:
    response = await client.post("api/payments/stripe/webhook", headers={"Stripe-Signature": faker.pystr()})

    assert response.status_code == 400


# Техдолг протестировать вебхук
