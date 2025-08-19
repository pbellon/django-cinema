from rest_framework.serializers import ModelSerializer

from cinema.models import Movie


class MovieSerializer(ModelSerializer):
    class Meta:
        model = Movie
        field = ["id", "title"]
