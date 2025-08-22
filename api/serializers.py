from rest_framework import serializers

from cinema.models import (
    Author,
    Movie,
    Spectator,
    SpectatorAuthorEvaluation,
    SpectatorMovieEvaluation,
)


class MovieListSerializer(serializers.ModelSerializer):
    details = serializers.HyperlinkedIdentityField(
        view_name="movie-detail", lookup_field="pk"
    )

    class Meta:
        model = Movie
        fields = ["id", "title", "details", "release_date"]


class AuthorListSerializer(serializers.ModelSerializer):
    details = serializers.HyperlinkedIdentityField(
        view_name="author-detail", lookup_field="pk"
    )

    class Meta:
        model = Author
        fields = ["id", "full_name", "details"]


class AuthorDetailsSerializer(serializers.ModelSerializer):
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


class MovieDetailsSerializer(serializers.ModelSerializer):
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


class RegisterSpectatorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Spectator
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "password",
            "biography",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        spectator = Spectator(**validated_data)
        # Ensures proper hashing
        spectator.set_password(password)
        spectator.save()
        return spectator


class CreateFavoriteMovieSerializer(serializers.Serializer):
    movie_id = serializers.PrimaryKeyRelatedField(
        queryset=Movie.objects.all(), source="movie"
    )


class CreateFavoriteAuthorSerializer(serializers.Serializer):
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=Author.objects.all(), source="author"
    )


class SpectatorMovieEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpectatorMovieEvaluation
        fields = ["id", "movie", "spectator", "score", "comment"]
        read_only_fields = ["movie", "spectator"]


class SpectatorAuthorEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpectatorAuthorEvaluation
        fields = ["id", "author", "spectator", "score", "comment"]
        read_only_fields = ["author", "spectator"]
