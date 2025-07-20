from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.staticfiles import StaticFiles

from app.core.config import DEV_MODE, settings
from app.core.utils.open_api import get_custom_open_api
from app.domains.auth.api import router as auth_router
from app.domains.feedback.api import router as feedback_router
from app.domains.users.routes.admin_api import router as users_admin_router
from app.domains.users.routes.api import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
logger.add("logs/request_logs.log", rotation="10 days")


app.mount(settings.MEDIA_API_PATH, StaticFiles(directory=settings.MEDIA_DIR_NAME), name=settings.MEDIA_DIR_NAME)


@app.middleware("http")
async def log_request(request: Request, call_next):
    message = f"URL: {request.url.path} Method: {request.method}"
    logger.info(message)
    response = await call_next(request)
    return response


# --- Обработчик ошибок 422 ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    custom_errors = [
        {"field": ".".join(str(loc) for loc in error["loc"][1:]), "message": error["msg"]} for error in exc.errors()
    ]
    return ORJSONResponse(
        status_code=422,
        content={"detail": {"errors": custom_errors}},
    )


app.openapi = get_custom_open_api(app)


app.include_router(users_router, prefix="/api")
app.include_router(users_admin_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")


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


@app.get("/healthcheck")
async def healthcheck():
    return "Healthy"
