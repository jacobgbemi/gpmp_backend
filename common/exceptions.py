"""
Custom DRF exception handler.

Wraps DRF's default handler so every error response — validation errors,
permission denials, 404s, throttling, unexpected server errors — is returned
in the same envelope shape as `common.responses.error_response`.
"""

import logging

from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def glintpm_exception_handler(exc, context):
    """
    Normalize all DRF-handled exceptions into a consistent error envelope:

        {
            "success": false,
            "message": "...",
            "errors": {...} | [...] | null
        }
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception (bug, DB error, etc.) — DRF would otherwise
        # let this propagate as a raw 500. Log it and return a safe,
        # consistent envelope instead of leaking internals to the client.
        logger.exception("Unhandled exception in %s", context.get("view"))
        return None

    errors = response.data
    message = "Request failed."

    if isinstance(errors, dict) and "detail" in errors:
        message = str(errors["detail"])
        errors = (
            None
            if len(errors) == 1
            else {k: v for k, v in errors.items() if k != "detail"}
        )

    response.data = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    return response
