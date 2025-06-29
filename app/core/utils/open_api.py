from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class Errors(BaseModel):
    errors: list[FieldError]


class Custom422Error(BaseModel):
    detail: Errors


def get_custom_open_api(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

        # Генерация всех вложенных моделей
        custom_schema = Custom422Error.model_json_schema(ref_template="#/components/schemas/{model}")

        # Объединяем их в components.schemas
        openapi_schema["components"]["schemas"].update(custom_schema["$defs"])

        # Добавляем саму основную схему
        openapi_schema["components"]["schemas"]["Custom422Error"] = {
            k: v for k, v in custom_schema.items() if k != "$defs"
        }

        # Обновим все ручки с 422
        for route in app.routes:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    operation = openapi_schema["paths"][route.path][method.lower()]
                    responses = operation.setdefault("responses", {})
                    if "422" in responses:
                        responses["422"] = {
                            "description": "Unprocessable entity",
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/Custom422Error"}}
                            },
                        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi
