from rest_framework.routers import DefaultRouter

from apps.inspections.views import (
    EvidenceViewSet,
    InspectionItemViewSet,
    InspectionViewSet,
)

app_name = "inspections"

router = DefaultRouter()
router.register("inspections", InspectionViewSet, basename="inspection")
router.register("inspection-items", InspectionItemViewSet, basename="inspection-item")
router.register("evidence", EvidenceViewSet, basename="evidence")

urlpatterns = router.urls
