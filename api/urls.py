from django.urls import include, path
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import APIRootView, DefaultRouter
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from api.views import (
    RegisterSpectatorView,
)
from api.viewsets import (
    AuthorViewSet,
    FavoriteAuthorsViewSet,
    FavoriteMoviesViewSet,
    MovieViewSet,
)


class ApiRoot(APIRootView):
    """
    Django Cinema API
    """

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "authors": reverse("author-list", request=request),
                "movies": reverse("movie-list", request=request),
                "favorite_movies": reverse(
                    "favorite-movie-list", request=request
                ),
                "favorite_authors": reverse(
                    "favorite-author-list", request=request
                ),
                "register": reverse("register", request=request),
                "token_obtain": reverse("token_obtain", request=request),
                "token_refresh": reverse("token_refresh", request=request),
                "token_invalidate": reverse(
                    "token_invalidate", request=request
                ),
            }
        )


api_router = DefaultRouter()
api_router.APIRootView = ApiRoot
api_router.register(r"movies", MovieViewSet, basename="movie")
api_router.register(r"authors", AuthorViewSet, basename="author")
api_router.register(
    r"favorites/movies", FavoriteMoviesViewSet, basename="favorite-movie"
)
api_router.register(
    r"favorites/authors", FavoriteAuthorsViewSet, basename="favorite-author"
)

urlpatterns = [
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    # auth
    path("register/", RegisterSpectatorView.as_view(), name="register"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "token/invalidate/",
        TokenBlacklistView.as_view(),
        name="token_invalidate",
    ),
    # custom API views
    # viewsets routes
    path("", include(api_router.urls)),
]
