from rest_framework.routers import DefaultRouter

from apps.risks.views import IssueViewSet, RiskViewSet

app_name = "risks"

router = DefaultRouter()
router.register("risks", RiskViewSet, basename="risk")
router.register("issues", IssueViewSet, basename="issue")

urlpatterns = router.urls
