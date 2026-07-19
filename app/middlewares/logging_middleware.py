import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"request started | method:{request.method} path:{request.url.path}")

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"request failed | method:{request.method} path:{request.url.path} error:{e}")
            raise

        duration = round(time.time() - start_time, 4)
        logger.info(
            f"request completed | method:{request.method} path:{request.url.path} "
            f"status:{response.status_code} duration:{duration}s"
        )
        return response