# analytics/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsViewSet

router = DefaultRouter()
router.register(r'', AnalyticsViewSet, basename='analytics')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]

