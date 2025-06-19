from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.core.config import DEV_MODE
from app.domains.users.api import router as users_router
from app.domains.auth.api import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown


app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)


app.include_router(users_router, prefix="/api/users")
app.include_router(auth_router, prefix="/api/auth")


@app.get("/")
async def root():
    return {"message": f"Hello World DEV_MODE: {DEV_MODE}"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name} "}
