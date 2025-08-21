from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action

from cinema.models import Movie
from api.serializers import MovieDetailsSerializer, MovieListSerializer


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
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
