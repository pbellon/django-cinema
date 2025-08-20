from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


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
    birth_day = models.DateField(null=True, blank=True)
    death_day = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)
    last_tmdb_populated = models.DateTimeField(null=True, blank=True)

    def imdb_page(self):
        if len(self.imdb_id) > 0:
            return f"https://www.imdb.com/name/{self.imdb_id}/"

        return ""


class Spectator(User):
    class Meta:
        verbose_name = "Spectator"
        verbose_name_plural = "Spectators"

    biography = models.TextField(blank=True)
    avatar = models.FileField(blank=True)


class MovieStatus(models.TextChoices):
    UNKNOWN = "Unknown"
    RUMORED = "Rumored"
    IN_PRODUCTION = "In Production"
    POST_PRODUCTION = "Post Production"
    RELEASED = "Released"
    CANCELED = "Canceled"


class MovieEvaluation(models.IntegerChoices):
    NOT_RATED = 0, _("Not Rated")
    VERY_BAD = 1, _("Very Bad")
    BAD = 2, _("Bad")
    MEDIUM = 3, _("Medium")
    GOOD = 4, _("Good")
    VERY_GOOD = 5, _("Very Good")


# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=300)
    imdb_id = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    original_title = models.CharField(max_length=300, blank=True)
    evaluation = models.IntegerField(choices=MovieEvaluation, default=MovieEvaluation.NOT_RATED)
    status = models.CharField(
        max_length=15,
        choices=MovieStatus,
        default=MovieStatus.UNKNOWN,
    )
    budget = models.IntegerField(
        null=True, blank=True, validators=(MinValueValidator(limit_value=0, message="Budget can't be negative"),)
    )
    release_date = models.DateField(null=True, blank=True)
    authors = models.ManyToManyField(Author, related_name="movies")

    @property
    def imdb_page(self):
        if len(self.imdb_id) > 0:
            return f"https://www.imdb.com/title/{self.imdb_id}/"

        return ""

    def __str__(self):
        return self.title


# Spectator Evaluations
class Evaluation(models.Model):
    score = models.IntegerField(
        blank=False,
        help_text="Evaluation score",
        validators=(
            MinValueValidator(limit_value=0, message="Score must be superior or equal to 0"),
            MaxValueValidator(limit_value=100, message="Score must be inferior or equal to 100"),
        ),
    )
    comment = models.TextField(blank=True)

    class Meta:
        abstract = True


class SpectatorMovieEvaluation(Evaluation):
    movie = models.ForeignKey(Movie, related_name="evaluations", on_delete=models.CASCADE)
    spectator = models.ForeignKey(Spectator, related_name="movies_evaluations", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.spectator.full_name} evaluation on {self.movie.title} movie"


class SpectatorAuthorEvaluation(Evaluation):
    author = models.ForeignKey(Author, related_name="evaluations", on_delete=models.CASCADE)
    spectator = models.ForeignKey(Spectator, related_name="authors_evaluations", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.spectator.full_name} evaluation on {self.author.full_name} author"


# Spectator Favorites
class SpectatorFavoriteMovie(models.Model):
    spectator = models.ForeignKey(Spectator, related_name="favorite_movies", on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)

    def __str__(self):
        return f"Movie favorite ({self.pk}) of {self.spectator.full_name}"


class SpectatorFavoriteAuthor(models.Model):
    spectator = models.ForeignKey(Spectator, related_name="favorite_authors", on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    def __str__(self):
        return f"Author favorite ({self.pk}) of {self.spectator.full_name}"
