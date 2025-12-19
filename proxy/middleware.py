import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .utils import get_logger

logger = get_logger("interceptor")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 1. Process the request (Forward to the app)
        response = await call_next(request)

        # 2. Calculate duration
        process_time = time.time() - start_time

        # 3. Log the "Shape" of the traffic
        logger.info(
            f"Method={request.method} Path={request.url.path} "
            f"Status={response.status_code} "
            f"Duration={process_time:.4f}s"
        )

        return response
