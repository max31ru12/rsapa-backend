from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.core.config import DEV_MODE
from app.domains.auth.api import router as auth_router
from app.domains.users.api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    custom_errors = [
        {"field": ".".join(str(loc) for loc in error["loc"][1:]), "message": error["msg"]} for error in exc.errors()
    ]

    return ORJSONResponse(status_code=422, content={"detail": {"errors": custom_errors}})


app.include_router(users_router, prefix="/api/users")
app.include_router(auth_router, prefix="/api/auth")


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Разрешить передачу cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": f"Hello World DEV_MODE: {DEV_MODE}"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name} "}
