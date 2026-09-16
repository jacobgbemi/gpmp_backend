"""
Standard API response envelope.

Keeping success and error responses in a consistent shape makes the React
frontend's API client simpler and avoids ad-hoc response formats spreading
across future business-domain apps.
"""

from rest_framework.response import Response


def success_response(data=None, message="", status_code=200, **extra):
    """Build a consistent success response envelope."""
    payload = {
        "success": True,
        "message": message,
        "data": data,
    }
    payload.update(extra)
    return Response(payload, status=status_code)


def error_response(message="", errors=None, status_code=400, **extra):
    """Build a consistent error response envelope."""
    payload = {
        "success": False,
        "message": message,
        "errors": errors,
    }
    payload.update(extra)
    return Response(payload, status=status_code)