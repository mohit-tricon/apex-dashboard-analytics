from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi.responses import JSONResponse


class CustomJSONResponse(JSONResponse):
    """
    Custom JSON response that wraps data with metadata.
    Includes request ID, timestamp, and API version in every response.
    """

    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background=None,
        request_id: str = None,
        api_version: str = "1.0",
    ) -> None:
        # Read from structlog contextvars when not explicitly passed
        if request_id is None:
            ctx = structlog.contextvars.get_contextvars()
            request_id = ctx.get("request_id", "NA")

        self.request_id = request_id
        self.api_version = api_version

        # Wrap content with metadata
        wrapped_content = {
            "data": content,
            "meta": {
                "request_id": self.request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "api_version": self.api_version,
            },
        }

        # Initialize headers dict if None
        headers = headers or {}

        # Add custom headers for easy access
        headers["X-Request-ID"] = self.request_id
        headers["X-API-Version"] = self.api_version

        super().__init__(
            content=wrapped_content,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
