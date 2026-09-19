from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.serializers import (
    CurrentUserSerializer,
    EmailTokenObtainPairSerializer,
)


@extend_schema(tags=["auth"], summary="Obtain a JWT access/refresh pair")
class LoginView(TokenObtainPairView):
    """POST /api/auth/token/ — body: {"email": "...", "password": "..."}"""

    serializer_class = EmailTokenObtainPairSerializer


@extend_schema(tags=["auth"], summary="Refresh the JWT access token")
class RefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/ — body: {"refresh": "..."}"""


@extend_schema(tags=["auth"], summary="Current authenticated user")
class MeView(RetrieveAPIView):
    """GET /api/auth/me/ — requires a valid Bearer access token."""

    serializer_class = CurrentUserSerializer
    pagination_class = None

    def get_object(self):
        return self.request.user