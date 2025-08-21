from rest_framework.serializers import (
    ModelSerializer,
    HyperlinkedIdentityField,
    CharField,
)

from cinema.models import Movie, Author


class AuthorListSerializer(ModelSerializer):
    details = HyperlinkedIdentityField(
        view_name="author-detail", lookup_field="pk"
    )

    class Meta:
        model = Author
        fields = ["id", "full_name", "details"]


class MovieListSerializer(ModelSerializer):
    details = HyperlinkedIdentityField(
        view_name="movie-detail", lookup_field="pk"
    )

    class Meta:
        model = Movie
        fields = ["id", "title", "details", "release_date"]


class AuthorDetailsSerializer(ModelSerializer):
    # full_name = CharField(read_only=True)

    first_name = CharField()
    last_name = CharField()
    movies = MovieListSerializer(many=True, read_only=True)

    class Meta:
        model = Author
        fields = [
            "id",
            "full_name",
            "biography",
            "imdb_page",
            "first_name",
            "last_name",
            "imdb_id",
            "birth_day",
            "death_day",
            "movies",
        ]


class MovieDetailsSerializer(ModelSerializer):
    authors = AuthorListSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "release_date",
            "status",
            "evaluation",
            "imdb_page",
            "authors",
        ]
