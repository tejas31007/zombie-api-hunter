import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .utils import get_logger

logger = get_logger("interceptor")


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 1. Generate Unique Request ID (Traceability)
        request_id = str(uuid.uuid4())
        
        # 2. Attach it to the request state
        # This allows other parts of the app (like router.py) to access this same ID
        request.state.request_id = request_id

        # 3. Process the request (Forward to the app)
        response = await call_next(request)

        # 4. Calculate duration
        process_time = time.time() - start_time

        # 5. Inject headers for the client
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        # 6. Log the "Shape" of the traffic (Now with ID!)
        logger.info(
            f"ID={request_id} Method={request.method} Path={request.url.path} "
            f"Status={response.status_code} "
            f"Duration={process_time:.4f}s"
        )

        return response