from rest_framework.serializers import ModelSerializer, HyperlinkedIdentityField

from cinema.models import Movie


class MovieListSerializer(ModelSerializer):
    details = HyperlinkedIdentityField(
        view_name="movie-detail", lookup_field="pk"
    )

    class Meta:
        model = Movie
        fields = ["id", "title", "details", "release_date"]


class MovieDetailsSerializer(ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "authors",
            "release_date",
            "imdb_page",
        ]
