from rest_framework.routers import DefaultRouter
from .views import TripViewSet, LocationViewSet

router = DefaultRouter()
router.register(r"locations", LocationViewSet, basename="locations")
router.register("", TripViewSet, basename="trip")

urlpatterns = router.urls