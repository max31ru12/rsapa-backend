from app.domains.membership.models import MembershipStatusEnum, MembershipType, UserMembership


def get_checkout_session_summary_dictionary(user_membership: UserMembership, membership_type: MembershipType, session):
    return {
        "membership": {
            "id": user_membership.id,
            "type": membership_type.type,
            "status_db": user_membership.status,
            "current_period_end": user_membership.current_period_end,
        },
        "subscription": {
            "id": session["subscription"]["id"],
            "status": MembershipStatusEnum(session["subscription"]["status"]),
        },
        "payment": {
            "amount_total": session.get("amount_total"),
            "currency": session.get("currency"),
            "invoice_id": session["invoice"]["id"],
        },
    }
