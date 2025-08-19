from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Author(User):
    # TODO: add relevant fields for directors
    pass


class Spectator(User):
    # TODO:
    # - add bio
    # - add avatar
    # - add social links
    pass


# Create your models here.
class Movie(models.Model):
    author = models.ForeignKey(Author, related_name="movies", on_delete=models.DO_NOTHING)


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
