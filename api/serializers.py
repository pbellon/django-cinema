from rest_framework import serializers

from cinema.models import Movie, Author, Spectator, SpectatorFavoriteAuthor


class AuthorListSerializer(serializers.ModelSerializer):
    details = serializers.HyperlinkedIdentityField(
        view_name="author-detail", lookup_field="pk"
    )

    class Meta:
        model = Author
        fields = ["id", "full_name", "details"]


class MovieListSerializer(serializers.ModelSerializer):
    details = serializers.HyperlinkedIdentityField(
        view_name="movie-detail", lookup_field="pk"
    )

    class Meta:
        model = Movie
        fields = ["id", "title", "details", "release_date"]


class AuthorDetailsSerializer(serializers.ModelSerializer):
    # full_name = CharField(read_only=True)

    first_name = serializers.CharField()
    last_name = serializers.CharField()
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


class FavoriteAuthorSerializer(serializers.ModelSerializer):
    movie = MovieDetailsSerializer()
    delete_url = serializers.HyperlinkedIdentityField(
        view_name="favorite-movie", lookup_field="pk"
    )

    class Meta:
        model = SpectatorFavoriteAuthor
        fields = ["id", "delete_url", "movie"]


class FavoriteMovieSerializer(serializers.ModelSerializer):
    author = AuthorDetailsSerializer()
    delete_url = serializers.HyperlinkedIdentityField(
        view_name="favorite-author", lookup_field="pk"
    )

    class Meta:
        model = SpectatorFavoriteAuthor
        fields = ["id", "delete_url", "author"]
