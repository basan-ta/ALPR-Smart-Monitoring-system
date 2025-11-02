"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import VehicleViewSet, SightingViewSet, AlertViewSet, PredictedRouteViewSet, StatsView, VerificationView, DatasetView

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'sightings', SightingViewSet, basename='sighting')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'routes', PredictedRouteViewSet, basename='route')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/stats/', StatsView.as_view(), name='stats'),
    path('api/dataset/', DatasetView.as_view(), name='dataset'),
    path('api/verify/', VerificationView.as_view(), name='verify'),
]
