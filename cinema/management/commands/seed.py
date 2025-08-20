from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cinema.models import (
    Spectator,
    Movie,
    SpectatorAuthorEvaluation,
    SpectatorMovieEvaluation,
    SpectatorFavoriteMovie,
    SpectatorFavoriteAuthor,
    Author,
)


class Command(BaseCommand):
    help = "Populate DB with initial data to speedup testing"

    def handle(self, *args, **opts):
        try:
            with transaction.atomic():
                # create an author with a movie
                nolan, _ = Author.objects.get_or_create(
                    first_name="Christopher", last_name="Nolan", username="cnolan", password="notverysecurepassword"
                )

                self.stdout.write(f"Christopher Nollan created: {nolan}")

                interstellar, _ = Movie.objects.get_or_create(
                    title="Interstellar",
                )

                interstellar.authors.add(nolan)

                # another author with a movie
                spielberg, _ = Author.objects.get_or_create(
                    first_name="Steven", last_name="Spielberg", username="spielberg", password="newhollywood1970"
                )
                third_encounter, _ = Movie.objects.get_or_create(
                    title="Close Encounters of the Third Kind",
                )
                third_encounter.authors.add(spielberg)

                # create an author without attached movies
                atarkovski, _ = Author.objects.get_or_create(
                    first_name="Andreï",
                    last_name="Tarkovski",
                    username="atarkovski",
                    password="againthisisnotreallysecure",
                )

                # create a spectator without favorites or evaluations
                johndoe, _ = Spectator.objects.get_or_create(
                    first_name="John",
                    last_name="Doe",
                    username="johndoe",
                    email="johndoe@not-real-email.com",
                    password="johndoe1234",
                )

                # create a spectator with some favorites & evaluations
                janedoe, _ = Spectator.objects.get_or_create(
                    first_name="Jane",
                    last_name="Doe",
                    username="janedoe",
                    email="janedoe@not-real-email.com",
                    password="janedoe1234",
                )
                # Add Interstallar to Jane's favorite movies
                jane_fav_movie, _ = SpectatorFavoriteMovie.objects.get_or_create(spectator=janedoe, movie=interstellar)
                jane_fav_author, _ = SpectatorFavoriteAuthor.objects.get_or_create(spectator=janedoe, author=nolan)

                # Jane evaluation on interstellar with a comment
                jane_interstellar_eval, _ = SpectatorMovieEvaluation.objects.get_or_create(
                    spectator=janedoe,
                    movie=interstellar,
                    score=98,
                    comment="My favorite movie of all time",
                )

                # Jane evaluation on nollan
                jane_nolan_eval, _ = SpectatorAuthorEvaluation.objects.get_or_create(
                    spectator=janedoe,
                    author=nolan,
                    score=90,
                    comment="I love his movies, huge fan of the batman trilogy",
                )

                jane_third_encounter_eval, _ = SpectatorMovieEvaluation.objects.get_or_create(
                    spectator=janedoe, movie=third_encounter, score=20, comment="Not a fan at all..."
                )

                self.stdout.write(self.style.SUCCESS("Seed data created"))

        except Exception as e:
            # transaction.atomic() rolls back automatically on exceptions
            raise CommandError(f"Seeding failed and was rolled back: {e}")
