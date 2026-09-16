from typing import ClassVar

from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from common.responses import success_response


class HealthCheckView(APIView):
    """
    GET /api/health/

    Simple liveness/readiness probe. Confirms:
        - the Django process is up and able to handle requests
        - the configured database is reachable

    Intentionally unauthenticated so it can be used by load balancers,
    container orchestrators, and uptime monitors.
    """

    permission_classes: ClassVar = [AllowAny]
    authentication_classes: ClassVar = []

    @extend_schema(
        summary="Health check",
        description="Returns service status and confirms the database connection is alive.",
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        db_status = "ok"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:  # noqa: BLE001 - deliberately broad for a health probe
            db_status = "unavailable"

        overall_status = "ok" if db_status == "ok" else "degraded"
        http_status = 200 if db_status == "ok" else 503

        return success_response(
            data={
                "status": overall_status,
                "database": db_status,
                "timestamp": timezone.now().isoformat(),
                "service": "glintpm-private-backend",
            },
            message="Service is healthy." if overall_status == "ok" else "Service is degraded.",
            status_code=http_status,
            success=(overall_status == "ok"),
        )