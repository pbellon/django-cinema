from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from api.routers import api_router

urlpatterns = [
    path("", RedirectView.as_view(url="admin/", permanent=True)),
    path("admin/", admin.site.urls),
    path("api/", include(api_router.urls)),
    path(
        "api-auth/", include("rest_framework.urls", namespace="rest_framework")
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
