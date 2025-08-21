from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Value
from django.db.models.functions import Concat
from cinema.models import (
    CreationSource,
    Movie,
    MovieEvaluation,
    MovieStatus,
    Author,
)

from tmdb import client


@dataclass
class CommandStats:
    created_movies: int
    updated_movies: int

    created_authors: int
    updated_authors: int


def success_msg(stats: CommandStats) -> str:
    return f"""Successfully populated DB with TMDB data:
    {stats.created_movies} new movies created - {stats.updated_movies} updated movies
    {stats.created_authors} new authors created - {stats.updated_authors} updated authors"""


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
        stats = CommandStats(
            created_authors=0,
            updated_authors=0,
            created_movies=0,
            updated_movies=0,
        )

        tmdb_client = client.TMDBClient(stdout=self.stdout, style=self.style)

        # Will be more costful but would be safer to remove filter()
        all_movies_titles_and_ids = list(
            Movie.objects.all().values_list("title", "id")
        )

        all_authors_names_and_ids = list(
            Author.objects.all()
            .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .values_list("full_name", "id")
        )

        # Dict for linking movies & authors once fetching from TMDB done
        # It's based on tmdb's id and will need to be mapped to primary keys
        authors_mapping_to_authors: Dict[Set[int]] = defaultdict(set)

        # Sets keeping track of authors & movie already populated from TMDB
        # via their "tmdb_id".
        already_populated_movies: Set[int] = set()
        already_populated_authors: Set[int] = set()

        detected_authors_ids: Set[int] = set()
        detected_movie_ids: Set[int] = set()

        for tmdb_movie in tmdb_client.find_movies_by_titles(
            all_movies_titles_and_ids
        ):
            # Typing safety, not strictly needed
            if tmdb_movie.db_id is None:
                raise CommandError("Unexpected undefined db_id attribute")

            # Early populate
            Movie.objects.filter(pk=tmdb_movie.db_id).update(
                description=tmdb_movie.overview,
                evaluation=MovieEvaluation.from_vote(tmdb_movie.vote),
                imdb_id=tmdb_movie.imdb_id,
                release_date=tmdb_movie.release_date,
                status=MovieStatus.from_status(tmdb_movie.status),
                title=tmdb_movie.title,
                tmdb_id=tmdb_movie.tmdb_id,
                tmdb_population_date=tmdb_movie.fetch_datetime,
            )

            stats.updated_movies += 1

            already_populated_movies.add(tmdb_movie.tmdb_id)

            # add detected authors in mapping
            authors_mapping_to_authors[tmdb_movie.tmdb_id].update(
                tmdb_movie.directors_ids
            )

            # will fetch those if not already fetched in later stage
            detected_authors_ids.update(tmdb_movie.directors_ids)

        for tmdb_author in tmdb_client.find_authors_by_name(
            all_authors_names_and_ids
        ):
            # Typing safety, not strictly needed
            if tmdb_author.db_id is None:
                raise CommandError("Unexpected undefined db_id attribute")

            Author.objects.filter(pk=tmdb_author.db_id).update(
                first_name=tmdb_author.first_name,
                last_name=tmdb_author.last_name,
                biography=tmdb_author.biography,
                birth_day=tmdb_author.birthday,
                death_day=tmdb_author.deathday,
                imdb_id=tmdb_author.imdb_id,
                tmdb_id=tmdb_author.tmdb_id,
                tmdb_population_date=tmdb_author.fetch_datetime,
            )

            stats.updated_authors += 1

            already_populated_authors.add(tmdb_author.tmdb_id)

            detected_movie_ids.update(tmdb_author.directing_movies_ids)

            # Add this author mapping
            for tmdb_movie_id in tmdb_author.directing_movies_ids:
                authors_mapping_to_authors[tmdb_movie_id].add(
                    tmdb_author.tmdb_id
                )

        # Determine new authors & movies we need to fetch from TMDB
        new_authors_detected = detected_authors_ids.difference(
            already_populated_authors
        )

        new_movies_detected = detected_movie_ids.difference(
            already_populated_movies
        )

        self.stdout.write(
            f"Detected {len(new_authors_detected)} authors and {len(new_movies_detected)} movies to additionnaly fetch from TMDB "
        )

        # Fetch newly detected movies
        for tmdb_movie_id in new_movies_detected:
            tmdb_movie = tmdb_client.get_movie(tmdb_movie_id)
            if tmdb_movie is None:
                continue

            movie, created_movie = Movie.objects.update_or_create(
                tmdb_id=tmdb_movie.tmdb_id,
                defaults=dict(
                    description=tmdb_movie.overview,
                    evaluation=MovieEvaluation.from_vote(tmdb_movie.vote),
                    imdb_id=tmdb_movie.imdb_id,
                    release_date=tmdb_movie.release_date,
                    status=MovieStatus.from_status(tmdb_movie.status),
                    title=tmdb_movie.title,
                    tmdb_population_date=tmdb_movie.fetch_datetime,
                ),
            )

            if created_movie:
                movie.creation_source = CreationSource.TMDB
                movie.save(update_fields=["creation_source"])

                stats.created_movies += 1
            else:
                stats.updated_movies += 1

            # Add detected directors IDs for later linking
            authors_mapping_to_authors[tmdb_movie_id].update(
                tmdb_movie.directors_ids
            )

        # Fetch newly detected authors
        for tmdb_author_id in new_authors_detected:
            try:
                tmdb_author = tmdb_client.get_author(tmdb_author_id)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"An unexpected error occured while fetching author with {tmdb_author_id} ID: {e}"
                    )
                )
                continue

            if tmdb_author is None:
                continue

            author, created_author = Author.objects.update_or_create(
                tmdb_id=tmdb_author.tmdb_id,
                defaults=dict(
                    username=f"{tmdb_author.first_name}_{tmdb_author.last_name}",
                    first_name=tmdb_author.first_name,
                    last_name=tmdb_author.last_name,
                    biography=tmdb_author.biography,
                    birth_day=tmdb_author.birthday,
                    death_day=tmdb_author.deathday,
                    imdb_id=tmdb_author.imdb_id,
                    tmdb_population_date=tmdb_author.fetch_datetime,
                ),
            )

            if created_author:
                author.creation_source = CreationSource.TMDB
                author.save(update_fields=["creation_source"])
                stats.created_authors += 1
            else:
                stats.updated_authors += 1

            # Add to mapping for later linking
            for tmdb_movie_id in tmdb_author.directing_movies_ids:
                authors_mapping_to_authors[tmdb_movie_id].add(
                    tmdb_author.tmdb_id
                )

        # Finalize process with linking
        self.link_movies_to_authors_by_tmdb_id(authors_mapping_to_authors)

        self.stdout.write(self.style.SUCCESS(success_msg(stats)))

    @transaction.atomic
    def link_movies_to_authors_by_tmdb_id(self, mapping: Dict[int, Set[int]]):
        """
        Link Movie to Author using their tmdb_id as natural keys.
        """
        if not mapping:
            return

        movie_tmdb_ids = list(mapping.keys())
        author_tmdb_ids = sorted({a for s in mapping.values() for a in s})

        movie_id_map = dict(
            Movie.objects.filter(tmdb_id__in=movie_tmdb_ids).values_list(
                "tmdb_id", "id"
            )
        )

        author_id_map = dict(
            Author.objects.filter(tmdb_id__in=author_tmdb_ids).values_list(
                "tmdb_id", "id"
            )
        )

        # Optional strict check
        missing_movies = [m for m in movie_tmdb_ids if m not in movie_id_map]
        missing_authors = [a for a in author_tmdb_ids if a not in author_id_map]

        if missing_movies:
            self.stdout.write(
                self.style.WARNING(
                    f"Unresolved movies primary keys from TMDB ids: {missing_movies}"
                )
            )

        if missing_authors:
            self.stdout.write(
                self.style.WARNING(
                    f"Unresolved authors primary keys with TMDB ids: {missing_authors}"
                )
            )

        Through = Movie.authors.through

        pairs = set()

        # Construct movie pk to author pk pairs set
        for movie_tmdb_id, author_tmdb_id_set in mapping.items():
            movie_id = movie_id_map.get(movie_tmdb_id)

            if movie_id is None:
                continue

            for author_tmdb in author_tmdb_id_set:
                author_id = author_id_map.get(author_tmdb)

                if author_id is None:
                    continue

                pairs.add((movie_id, author_id))

        rows = [
            Through(movie_id=movie_id, author_id=author_id)
            for (movie_id, author_id) in pairs
        ]

        Through.objects.bulk_create(rows, ignore_conflicts=True)
