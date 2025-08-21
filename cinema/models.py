from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CreationSource(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    TMDB = "TMDB", "TMDb"


class User(AbstractUser):
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class Author(User):
    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    # For every of those fields, we allow null with blank=True and null=True.
    # This means we didn't populate them via TMDB and it could be populated
    # with dedicated `populate_from_tmdb` commmand.
    imdb_id = models.CharField(max_length=150, blank=True)
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    birth_day = models.DateField(null=True, blank=True)
    death_day = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)
    tmdb_population_date = models.DateTimeField(null=True, blank=True)
    creation_source = models.CharField(
        max_length=5,
        choices=CreationSource,
        default=CreationSource.ADMIN,
        editable=False,
    )

    @property
    def imdb_page(self):
        if len(self.imdb_id) > 0:
            return f"https://www.imdb.com/name/{self.imdb_id}/"

        return ""


class MovieStatus(models.TextChoices):
    UNKNOWN = "Unknown"
    RUMORED = "Rumored"
    IN_PRODUCTION = "In Production"
    POST_PRODUCTION = "Post Production"
    RELEASED = "Released"
    CANCELED = "Canceled"

    # Not sure
    def from_status(status: str):
        if status in MovieStatus.values:
            return status

        return MovieStatus.UNKNOWN


class MovieEvaluation(models.IntegerChoices):
    NOT_RATED = 0, _("Not Rated")
    VERY_BAD = 1, _("Very Bad")
    BAD = 2, _("Bad")
    MEDIUM = 3, _("Medium")
    GOOD = 4, _("Good")
    VERY_GOOD = 5, _("Very Good")

    def from_vote(vote: float) -> int:
        """
        Convert TMDB vote to MovieEvaluation
        """
        if vote > 0 and vote <= 2.2:
            return MovieEvaluation.VERY_BAD

        if vote > 2.2 and vote <= 4.5:
            return MovieEvaluation.BAD

        if vote > 4.5 and vote <= 5.5:
            return MovieEvaluation.MEDIUM

        if vote > 5.5 and vote < 7.5:
            return MovieEvaluation.GOOD

        if vote > 7.5 and vote <= 10:
            return MovieEvaluation.VERY_GOOD

        return MovieEvaluation.NOT_RATED  # either vote == 0 or invalid vote


# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=300)
    imdb_id = models.CharField(max_length=150, blank=True)
    tmdb_id = models.IntegerField(null=True, blank=True, unique=True)
    description = models.TextField(blank=True)
    original_title = models.CharField(max_length=300, blank=True)
    evaluation = models.IntegerField(
        choices=MovieEvaluation, default=MovieEvaluation.NOT_RATED
    )
    tmdb_population_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=15,
        choices=MovieStatus,
        default=MovieStatus.UNKNOWN,
    )
    budget = models.IntegerField(
        null=True,
        blank=True,
        validators=(
            MinValueValidator(
                limit_value=0, message="Budget can't be negative"
            ),
        ),
    )
    release_date = models.DateField(null=True, blank=True)
    creation_source = models.CharField(
        max_length=5,
        choices=CreationSource,
        default=CreationSource.ADMIN,
        editable=False,
    )

    authors = models.ManyToManyField(Author, related_name="movies")

    @property
    def imdb_page(self):
        if len(self.imdb_id) > 0:
            return f"https://www.imdb.com/title/{self.imdb_id}/"

        return ""

    def __str__(self):
        return self.title


class Spectator(User):
    class Meta:
        verbose_name = "Spectator"
        verbose_name_plural = "Spectators"

    biography = models.TextField(blank=True)

    favorite_movies = models.ManyToManyField(Movie, related_name="favorited_by")

    favorite_authors = models.ManyToManyField(
        Author,
        related_name="favorited_by",
    )


# Spectator Evaluations
class Evaluation(models.Model):
    score = models.IntegerField(
        blank=False,
        help_text="Evaluation score",
        validators=(
            MinValueValidator(
                limit_value=0, message="Score must be superior or equal to 0"
            ),
            MaxValueValidator(
                limit_value=100,
                message="Score must be inferior or equal to 100",
            ),
        ),
    )
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True


class SpectatorMovieEvaluation(Evaluation):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["spectator", "movie"],
                name="unique_spectator_movie_evaluation",
            )
        ]

    movie = models.ForeignKey(
        Movie, related_name="evaluations", on_delete=models.CASCADE
    )
    spectator = models.ForeignKey(
        Spectator, related_name="movies_evaluations", on_delete=models.CASCADE
    )

    def __str__(self):
        return (
            f"{self.spectator.full_name} evaluation on {self.movie.title} movie"
        )


class SpectatorAuthorEvaluation(Evaluation):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["spectator", "author"],
                name="unique_spectator_author_evaluation",
            )
        ]

    author = models.ForeignKey(
        Author, related_name="evaluations", on_delete=models.CASCADE
    )
    spectator = models.ForeignKey(
        Spectator, related_name="authors_evaluations", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.spectator.full_name} evaluation on {self.author.full_name} author"
