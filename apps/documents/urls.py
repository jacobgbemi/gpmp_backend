from rest_framework.routers import DefaultRouter

from apps.documents.views import DocumentViewSet, FolderViewSet

app_name = "documents"

router = DefaultRouter()
router.register("folders", FolderViewSet, basename="folder")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = router.urls
