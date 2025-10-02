#!/bin/sh

# write the webhook_secret into shared with backend volume
mkdir -p /run/stripe
SECRET="$(stripe listen --api-key "$STRIPE_API_KEY" --print-secret)"
printf "%s" "$SECRET" > /run/stripe/webhook_secret

exec stripe listen \
  --api-key "$STRIPE_API_KEY" \
  --forward-to "${BACKEND_DOMAIN}:${BACKEND_PORT}/api/payments/stripe/webhook" \
  --events "$STRIPE_EVENTS" \
  --skip-verify \
