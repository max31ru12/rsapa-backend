from fastapi_exception_responses import Responses


class RegisterResponses(Responses):
    PASSWORDS_DONT_MATCH = 400, "Passwords don't match"
    EMAIL_ALREADY_IN_USE = 409, "Provided email is already in use"


async def register_user(register_form_data, user_service):
    data = register_form_data.model_dump()

    if (await user_service.get_by_kwargs(email=data["email"])) is not None:
        raise RegisterResponses.EMAIL_ALREADY_IN_USE

    if data["password"] != data["repeat_password"]:
        raise RegisterResponses.PASSWORDS_DONT_MATCH

    del data["repeat_password"]
    return await user_service.create(**data)
