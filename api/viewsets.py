from rest_framework.viewsets import ModelViewSet

from cinema.models import Movie


class MovieViewSet(ModelViewSet):
    queryset = Movie.objects.all()
