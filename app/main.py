from app.core.logger import setup_logger
setup_logger()
from pydantic import ValidationError
from loguru import logger
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database.db_connection import client,db
from app.middlewares.logging_middleware import LoggingMiddleware
from app.core.exception import (
    FullProjectException,
    NotFoundError,
    AlreadyExistsError,
    MaximumLimitReachedError,
    NotAuthorizedError,
    InvalidDateError,
    MemberNotInListError,
    NotCreatedError,
    UpdateFailedError,
    MinimumClreanceError,
    EnteredWrongPasswordError,
    UnauthorizedEntryError,
    InvalidTokenError
)

EXCEPTION_STATUS_MAP = {
    NotFoundError: 404,
    AlreadyExistsError: 409,
    MaximumLimitReachedError: 403,
    NotAuthorizedError: 403,
    InvalidDateError: 422,
    MemberNotInListError: 403,
    NotCreatedError: 500,
    UpdateFailedError: 500,
    MinimumClreanceError: 403,
    EnteredWrongPasswordError:401,
    UnauthorizedEntryError:403,
    InvalidTokenError:401
}
from app.routers import signup_router
from app.routers import workspace_router
from app.routers import project_router
from app.routers import sprint_router
from app.routers import task_router
from app.routers import team_router
from app.routers import workspace_member_router
from app.routers import login_router
from app.routers import dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await client.admin.command("ping")

        await db.users.create_index("email", unique=True)
        await db.workspace_members.create_index(
            [
                ("workspace_id", 1),
                ("user_id", 1)
            ],
            unique=True
        )
        await db.invitations.create_index("token", unique=True)

        logger.info("MongoDB connection established")
    except Exception as e:
        logger.error(f"MongoDB connection failed | error:{e}")
        raise
    yield
    client.close()
    logger.info("MongoDB connection closed")


app = FastAPI(title="AlienMind", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://alien-mind-frontend-2c1l0gp0o-alien-ecosystem.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

@app.exception_handler(FullProjectException)
async def project_exception_handler(request: Request, exc: FullProjectException):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 400)
    logger.error(f"{type(exc).__name__} | path:{request.url.path} error:{exc}")
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"unhandled exception | path:{request.url.path} error:{exc}")
    return JSONResponse(status_code=500, content={"detail": "internal server error"})

@app.exception_handler(ValidationError)
async def token_validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"token validation failed | path:{request.url.path} error:{exc}")
    return JSONResponse(status_code=401, content={"detail": "session expired, please log in again"})

app.include_router(login_router.router)
app.include_router(signup_router.router)
app.include_router(workspace_router.router)
app.include_router(project_router.router)
app.include_router(sprint_router.router)
app.include_router(task_router.router)
app.include_router(team_router.router)
app.include_router(workspace_member_router.router)
app.include_router(dashboard_router.router)