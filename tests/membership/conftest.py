EVENTS = [
    ("customer.subscription.updated", {"status": "trialing"}),
    ("customer.subscription.updated", {"status": "active"}),
    ("customer.subscription.updated", {"status": "past_due"}),
    ("customer.subscription.deleted", {}),
    ("invoice.payment_failed", {"attempt_count": 1}),
]
