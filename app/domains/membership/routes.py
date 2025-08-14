import stripe
from fastapi import APIRouter
from starlette.responses import RedirectResponse

from app.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY
router = APIRouter(prefix="/membership", tags=["Payments"])


@router.post("/checkout-session")
async def create_checkout_session():
    session = stripe.checkout.Session.create(
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "T-shirt",
                    },
                    "unit_amount": 2000,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://localhost:4242/success",
        cancel_url="http://localhost:4242/cancel",
    )

    return RedirectResponse(session.url)
