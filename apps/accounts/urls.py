from django.urls import path

from apps.accounts.views import LoginView, MeView, RefreshView

app_name = "accounts"

urlpatterns = [
    path("token/", LoginView.as_view(), name="token"),
    path("token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
]