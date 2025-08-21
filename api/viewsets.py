from django.shortcuts import redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from cinema.models import Movie, Author
from api.serializers import (
    MovieDetailsSerializer,
    MovieListSerializer,
    AuthorDetailsSerializer,
    AuthorListSerializer,
)

from api.filters import CreationSourceFilterMixin


class MovieViewSet(CreationSourceFilterMixin, ModelViewSet):
    queryset = Movie.objects.all()
    http_method_names = ["get", "put", "patch", "head", "options"]

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


class AuthorViewSet(CreationSourceFilterMixin, ModelViewSet):
    queryset = Author.objects.all()
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

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
