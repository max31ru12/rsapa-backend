from fastapi_mail import FastMail, MessageSchema, MessageType

from app.core.config import MAIL_CONFIG


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    plain: bool = False,
):
    subtype = MessageType.plain if plain else MessageType.html
    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=body,
        subtype=subtype,
    )
    fm = FastMail(MAIL_CONFIG)
    await fm.send_message(message)
