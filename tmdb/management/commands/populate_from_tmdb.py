from typing import Set

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Value
from django.db.models.functions import Concat
from cinema.models import (
    Movie,
    MovieEvaluation,
    MovieStatus,
    Author,
)

from tmdb import client


# Basic working:
# 1. Collect existing movies & author not yet populated via TMDB
# 2. Extract movie titles & authors' full names
# 3. Use TMDB API to find authors and related films. Note that this will work
#    both ways. If a matching author (aka director) is found on TMDB, then we'll
#    look for related films. Same for given movie titles, if we find a matching
#    movie in TMDB, we'll look for related directors/authors.
class Command(BaseCommand):
    help = "Populate DB by querying TMDB"

    def handle(self, *args, **opts):
        tmdb_client = client.TMDBClient(stdout=self.stdout, style=self.style)
        all_movie_titles = list(
            Movie.objects.filter(tmdb_population_date__isnull=True).values_list(
                "title", "id"
            )
        )

        all_author_names = list(
            Author.objects.filter(tmdb_population_date__isnull=True)
            .only("first_name", "last_name")
            .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .values_list("full_name", "id")
        )

        already_populated_movies: Set[int] = set()
        detected_authors_ids: Set[int] = set()

        already_populated_authors: Set[int] = set()
        detected_movie_ids: Set[int] = set()

        for tmdb_movie in tmdb_client.find_movies_by_titles(all_movie_titles):
            print(f"Found {tmdb_movie.title} from TMDB!\n{tmdb_movie}")

            if tmdb_movie.db_id is None:
                raise CommandError("Unexpected undefined db_id attribute")

            Movie.objects.update(
                title=tmdb_movie.title,
                description=tmdb_movie.overview,
                evaluation=MovieEvaluation.from_vote(tmdb_movie.vote),
                imdb_id=tmdb_movie.imdb_id,
                status=MovieStatus.from_status(tmdb_movie.status),
                tmdb_population_date=tmdb_movie.fetch_datetime,
            )
            already_populated_movies.add(tmdb_movie.db_id)

            # will fetch those if not already fetched in later stage
            detected_authors_ids.update(tmdb_movie.directors_ids)

        for tmdb_author in tmdb_client.find_authors_by_name(all_author_names):
            if tmdb_author.db_id is None:
                raise CommandError("Unexpected undefined db_id attribute")

            Author.objects.update(
                id=tmdb_author.db_id,
                biography=tmdb_author.biography,
                birth_day=tmdb_author.birthday,
                death_day=tmdb_author.deathday,
                tmdb_population_date=tmdb_author.fetch_datetime,
                imdb_id=tmdb_author.imdb_id,
            )

            already_populated_authors.add(tmdb_author.tmdb_id)
            detected_movie_ids.update(tmdb_author.directing_movies_ids)

            print(f"Found author on TMDB: {tmdb_author}")

        new_authors_detected = detected_authors_ids.difference(
            already_populated_authors
        )
        new_movies_detected = detected_movie_ids.difference(
            already_populated_movies
        )

        for author_tmdb_id in new_authors_detected:
            tmdb_author = tmdb_client.get_author(author_tmdb_id)
            if tmdb_author is None:
                continue

            Author.objects.update_or_create(
                biography=tmdb_author.biography,
                birth_day=tmdb_author.birthday,
                death_day=tmdb_author.deathday,
                tmdb_population_date=tmdb_author.fetch_datetime,
                imdb_id=tmdb_author.imdb_id,
            )

        for movie_tmdb_id in new_movies_detected:
            tmdb_movie = tmdb_client.get_movie(movie_tmdb_id)
            if tmdb_movie is None:
                continue

            Movie.objects.update_or_create(
                title=tmdb_movie.title,
                description=tmdb_movie.overview,
                evaluation=MovieEvaluation.from_vote(tmdb_movie.vote),
                id=tmdb_movie.db_id,
                imdb_id=tmdb_movie.imdb_id,
                status=MovieStatus.from_status(tmdb_movie.status),
                tmdb_population_date=tmdb_movie.fetch_datetime,
            )
