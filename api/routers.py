from rest_framework import routers

from api.viewsets import MovieViewSet, AuthorViewSet

api_router = routers.DefaultRouter()

api_router.register(r"movies", MovieViewSet, basename="movie")
api_router.register(r"authors", AuthorViewSet, basename="author")
