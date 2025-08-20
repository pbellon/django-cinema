from django.core.management.base import BaseCommand, CommandError
from django.db.models import Value
from django.db.models.functions import Concat
from cinema.models import (
    Movie,
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
        tmdb_client = client.TMDBClient()
        all_movie_titles = list(Movie.objects.filter(tmdb_population_date__isnull=True).values_list("title", flat=True))
        all_author_names = list(
            Author.objects.filter(tmdb_population_date__isnull=True)
            .only("first_name", "last_name")
            .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .values_list("full_name", flat=True)
        )

        self.stdout.write(f"All movie titles not populated: {all_movie_titles}")
        self.stdout.write(f"All author names not populated: {all_author_names}")

        for tmdb_movie in tmdb_client.find_movies_by_titles(all_movie_titles):
            print(f"Found {tmdb_movie.title} from TMDB!\n{tmdb_movie}")
