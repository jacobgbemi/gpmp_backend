from rest_framework.routers import DefaultRouter

from apps.variations.views import VariationViewSet

app_name = "variations"

router = DefaultRouter()
router.register("variations", VariationViewSet, basename="variation")

urlpatterns = router.urls
