import json
from datetime import datetime, timezone

from app.domains.membership.schemas import PayloadSchema


def parse_stripe_event(event_data: bytes) -> PayloadSchema:
    return PayloadSchema(**json.loads(event_data))


def make_datetime_from_timestamp(unix_timestamp: int) -> datetime:
    return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)


# def get_payment_data(payload: bytes)
