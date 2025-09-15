from typing import Type

from app.domains.emails.common.abstract_plugin import EmailPlugin


class EmailService:
    def __init__(self, provider: EmailPlugin):
        self.provider = provider

    async def send_email(self, to: str, subject: str, body: str):
        await self.provider.send_email(to, subject, body)


def get_email_service(provider: Type[EmailPlugin]) -> EmailService:
    provider_instance = provider()
    return EmailService(provider_instance)
