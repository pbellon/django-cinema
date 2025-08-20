from rest_framework import routers

from api.viewsets import MovieViewSet

api_router = routers.DefaultRouter()

api_router.register(r"movies", MovieViewSet, basename="movie")
