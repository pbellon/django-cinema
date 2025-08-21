from django.shortcuts import get_object_or_404, redirect
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.filters import CreationSourceFilterMixin
from api.serializers import (
    AuthorDetailsSerializer,
    AuthorListSerializer,
    CreateFavoriteAuthorSerializer,
    CreateFavoriteMovieSerializer,
    MovieDetailsSerializer,
    MovieListSerializer,
    SpectatorAuthorEvaluationSerializer,
    SpectatorMovieEvaluationSerializer,
)
from api.utils import get_spectator_from_request
from cinema.models import (
    Author,
    Movie,
    SpectatorAuthorEvaluation,
    SpectatorMovieEvaluation,
)


class MovieViewSet(
    CreationSourceFilterMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Movie.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action != "list":
            return qs

        return self.filter_by_created_source(qs)

    def get_serializer_class(self):
        if self.action == "list" or self.action == "by_year":
            return MovieListSerializer

        return MovieDetailsSerializer

    def get_permissions(self):
        permissions = []

        if self.action == "list":
            permissions = [AllowAny]
        else:
            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]

    @action(detail=False, url_path=r"by-year/(?P<year>\d{4})")
    def by_year(self, request, year=None):
        # redirect to listing route if no year set
        if year is None:
            return redirect("movie-list")

        qs = self.get_queryset().filter(release_date__year=year)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk):
        movie = self.get_object()
        spectator = get_spectator_from_request(request)

        ser = SpectatorMovieEvaluationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj, created = SpectatorMovieEvaluation.objects.update_or_create(
            movie=movie,
            spectator=spectator,
            defaults={
                "score": ser.validated_data["score"],
                "comment": ser.validated_data.get("comment", ""),
            },
        )
        out = SpectatorMovieEvaluationSerializer(obj)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AuthorViewSet(
    CreationSourceFilterMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Author.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()

        if self.action != "list":
            return qs

        return self.filter_by_created_source(qs)

    def get_serializer_class(self):
        if self.action == "list":
            return AuthorListSerializer

        return AuthorDetailsSerializer

    def get_permissions(self):
        permissions = []

        if self.action == "list":
            permissions = [AllowAny]
        else:
            permissions = [IsAuthenticated]

        return [permission() for permission in permissions]

    def destroy(self, request, *args, **kwargs):
        author = self.get_object()

        if author.movies.exists():
            return Response(
                {"detail": "Cannot delete author with associated movies"},
                status=status.HTTP_409_CONFLICT,
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        author = self.get_object()
        spectator = get_spectator_from_request(request)

        ser = SpectatorAuthorEvaluationSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj, created = SpectatorAuthorEvaluation.objects.update_or_create(
            author=author,
            spectator=spectator,
            defaults={
                "score": ser.validated_data["score"],
                "comment": ser.validated_data.get("comment", ""),
            },
        )
        out = SpectatorAuthorEvaluationSerializer(obj)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# Favorites viewsets
class FavoriteMoviesViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "pk"
    lookup_field = "pk"

    def get_queryset(self):
        return get_spectator_from_request(self.request).favorite_movies.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateFavoriteMovieSerializer

        return MovieListSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        movie = ser.validated_data["movie"]
        user = get_spectator_from_request(request)
        user.favorite_movies.add(movie)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        movie_id = kwargs.get(self.lookup_url_kwarg)
        movie = get_object_or_404(Movie, pk=movie_id)
        get_spectator_from_request(request).favorite_movies.remove(movie)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteAuthorsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = "pk"  # <author_id> in URL
    lookup_field = "pk"

    def get_queryset(self):
        return get_spectator_from_request(self.request).favorite_authors.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CreateFavoriteAuthorSerializer
        return AuthorListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        author = serializer.validated_data["author"]
        get_spectator_from_request(request).favorite_authors.add(author)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, *args, **kwargs):
        author_id = kwargs.get(self.lookup_url_kwarg)
        author = get_object_or_404(Author, pk=author_id)
        get_spectator_from_request(request).favorite_authors.remove(author)
        return Response(status=status.HTTP_204_NO_CONTENT)
