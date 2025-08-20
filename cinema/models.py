from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    pass


class Author(User):
    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    imdb_id = models.CharField(max_length=150)
    birthday = models.DateField()
    deathday = models.DateField(blank=True)
    biography = models.TextField()


class Spectator(User):
    class Meta:
        verbose_name = "Spectator"
        verbose_name_plural = "Spectators"

    biography = models.TextField(blank=True)
    avatar = models.FileField(blank=True)


class MovieStatus(models.TextChoices):
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
    # class MovieStatus:
    imdb_id = models.CharField(max_length=150)
    description = models.TextField()
    title = models.CharField(max_length=300)
    original_title = models.CharField(max_length=300)
    evaluation = models.IntegerField(choices=MovieEvaluation, default=MovieEvaluation.NOT_RATED)
    status = models.CharField(
        max_length=15,
        choices=MovieStatus,
        blank=False,
    )
    budget = models.IntegerField(validators=(MinValueValidator(limit_value=0, message="Budget can't be negative"),))
    release_date = models.DateField()
    authors = models.ManyToManyField(Author, related_name="movies")


# Spectator Evaluations
class Evaluation(models.Model):
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        blank=False,
        help_text="Evaluation score",
        validators=(
            MinValueValidator(limit_value=0, message="Score must be superior or equal to 0"),
            MaxValueValidator(limit_value=10, message="Score must be inferior or equal to 10"),
        ),
    )
    comment = models.TextField()

    class Meta:
        abstract = True


class SpectatorMovieEvaluation(Evaluation):
    movie = models.ForeignKey(Movie, related_name="evaluations", on_delete=models.CASCADE)
    spectator = models.ForeignKey(Spectator, related_name="movies_evaluations", on_delete=models.CASCADE)


class SpectatorAuthorEvaluation(Evaluation):
    author = models.ForeignKey(Author, related_name="evaluations", on_delete=models.CASCADE)
    spectator = models.ForeignKey(Spectator, related_name="authors_evaluations", on_delete=models.CASCADE)


# Spectator Favorites
class SpectatorFavoriteMovie(models.Model):
    spectator = models.ForeignKey(Spectator, related_name="favorite_movies", on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)


class SpectatorFavoriteAuthor(models.Model):
    spectator = models.ForeignKey(Spectator, related_name="favorite_authors", on_delete=models.CASCADE)
