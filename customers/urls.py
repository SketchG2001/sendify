from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, ConfigurationsView
from django.urls import path

router = DefaultRouter()
router.register(r"auth", AuthViewSet, basename="auth")

urlpatterns = [
    path("email/configurations/", ConfigurationsView.as_view(), name="configurations"),
    path("email/configurations/<int:config_id>/", ConfigurationsView.as_view(), name="configuration-detail"),
]

urlpatterns += router.urls
