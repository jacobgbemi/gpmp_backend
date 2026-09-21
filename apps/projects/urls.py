from rest_framework.routers import DefaultRouter

from apps.projects.views import PaymentViewSet, ProjectViewSet

app_name = "projects"

router = DefaultRouter()
router.register("projects", ProjectViewSet, basename="project")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls
