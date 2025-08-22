from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set

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
    created_movies: int = 0
    updated_movies: int = 0

    created_authors: int = 0
    updated_authors: int = 0


# Basic working:
# 1. Collect existing movies & author not yet populated via TMDB
# 2. Extract movie titles & authors' full names
# 3. Use TMDB API to find authors and related films. Note that this will work
#    both ways. If a matching author (aka director) is found on TMDB, then we'll
#    look for related films. Same for given movie titles, if we find a matching
#    movie in TMDB, we'll look for related directors/authors.
class Command(BaseCommand):
    help = "Populate DB by querying TMDB"

    def add_arguments(self, parser):
        parser.add_argument("stage", choices=["populate", "expand"])

    def handle(self, stage, **opts):
        self.client = client.TMDBClient(stdout=self.stdout, style=self.style)
        if stage == "populate":
            self.seed()
        else:
            self.expand()

    def expand(
        self,
        authors_to_expand: List[client.AuthorFromTMDB] = list(),
        movies_to_expand: List[client.MovieFromTMDB] = list(),
        stats=CommandStats(),
    ):
        """
        Expand will lookup already stored Movie & Authors that have been
        populated. By expansion we mean to try look associated resources:
            - Movie -> List[Authors]
            - Author -> List[Movie]

        If `authors_to_expand` or `movies_to_expand` are set, will
        skip a fetching step and directly use those objects. This assumes those
        TMDB objects are already reflected in DB.

        Then we'll ensure the existing Author & Movie are properly linked by
        looking at received data from TMDB. This phase won't try to update
        existing Movie and Author row.
        """

        all_stored_authors_tmdb_id = set(
            Author.objects.filter(tmdb_id__isnull=False).values_list(
                "tmdb_id", flat=True
            )
        )

        all_stored_movies_tmdb_id = set(
            Movie.objects.filter(tmdb_id__isnull=False).values_list(
                "tmdb_id", flat=True
            )
        )

        if not authors_to_expand:
            authors_to_expand = self.client.get_authors(
                all_stored_authors_tmdb_id
            )

        if not movies_to_expand:
            movies_to_expand = self.client.get_movies(all_stored_movies_tmdb_id)

        # Dict for linking movies & authors once fetching from TMDB done
        # It's based on tmdb's id and will need to be mapped to primary keys
        authors_mapping_to_authors: Dict[Set[int]] = defaultdict(set)

        detected_authors_tmdb_ids: Set[int] = set()
        detected_movies_tmdb_ids: Set[int] = set()

        for tmdb_movie in movies_to_expand:
            detected_authors_tmdb_ids.update(tmdb_movie.directors_ids)
            # Add detected directors IDs for later linking
            authors_mapping_to_authors[tmdb_movie.tmdb_id].update(
                tmdb_movie.directors_ids
            )

        for tmdb_author in authors_to_expand:
            detected_movies_tmdb_ids.update(tmdb_author.directing_movies_ids)
            # Add to mapping for later linking
            for tmdb_movie_id in tmdb_author.directing_movies_ids:
                authors_mapping_to_authors[tmdb_movie_id].add(
                    tmdb_author.tmdb_id
                )

        # then we'll fetch TMDB data on authors & movies only on data that are
        # not currently in DB (tmdb ID not present)
        newly_detected_authors_tmdb_id = (
            detected_authors_tmdb_ids - all_stored_authors_tmdb_id
        )

        newly_detected_movie_ids_tmdb_id = (
            detected_movies_tmdb_ids - all_stored_movies_tmdb_id
        )

        self.stdout.write(
            f"Detected {len(newly_detected_authors_tmdb_id)} new authors TMDB ids"
        )

        self.stdout.write(
            f"Detected {len(newly_detected_movie_ids_tmdb_id)} new movies TMDB ids"
        )

        for tmdb_author in self.client.get_authors(
            newly_detected_authors_tmdb_id
        ):
            try:
                Author.objects.create(
                    biography=tmdb_author.biography,
                    birth_day=tmdb_author.birthday,
                    creation_source=CreationSource.TMDB,
                    death_day=tmdb_author.deathday,
                    first_name=tmdb_author.first_name,
                    username=f"{tmdb_author.first_name}_{tmdb_author.last_name}",
                    imdb_id=tmdb_author.imdb_id,
                    last_name=tmdb_author.last_name,
                    tmdb_id=tmdb_author.tmdb_id,
                    tmdb_population_date=tmdb_author.fetch_datetime,
                )
                stats.created_authors += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not save newly fetched author in DB: {e}\n\t{tmdb_author}"
                    )
                )
                continue  # skip this author

            # Add to mapping newly detected links
            for tmdb_movie_id in tmdb_author.directing_movies_ids:
                authors_mapping_to_authors[tmdb_movie_id].add(
                    tmdb_author.tmdb_id
                )

        for tmdb_movie in self.client.get_movies(
            newly_detected_movie_ids_tmdb_id
        ):
            try:
                Movie.objects.create(
                    description=tmdb_movie.overview,
                    evaluation=MovieEvaluation.from_vote(tmdb_movie.vote),
                    imdb_id=tmdb_movie.imdb_id,
                    release_date=tmdb_movie.release_date,
                    status=MovieStatus.from_status(tmdb_movie.status),
                    title=tmdb_movie.title,
                    tmdb_id=tmdb_movie.tmdb_id,
                    tmdb_population_date=tmdb_movie.fetch_datetime,
                    creation_source=CreationSource.TMDB,
                )
                stats.created_movies += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Could not save newly fetched movie in DB: {e}\n\t{tmdb_movie}"
                    )
                )
                continue  # skip this author

            authors_mapping_to_authors[tmdb_movie.tmdb_id].update(
                tmdb_movie.directors_ids
            )

        # Finalize process with linking
        self.link_movies_to_authors_by_tmdb_id(authors_mapping_to_authors)

        self.print_success(stats)

    def seed(self):
        """
        In this phase we'll lookup in database which Movie & Author have not
        been populated yet and try to find them in TMDB to populate their data.
        Once populated we'll run an expand on them. See `expand` method for
        more details on expansion.
        """
        stats = CommandStats(
            created_authors=0,
            updated_authors=0,
            created_movies=0,
            updated_movies=0,
        )

        all_movies_titles_and_ids = list(
            Movie.objects.filter(tmdb_id__isnull=True)
            .all()
            .values_list("title", "id")
        )

        all_authors_names_and_ids = list(
            Author.objects.filter(tmdb_id__isnull=True)
            .all()
            .annotate(full_name=Concat("first_name", Value(" "), "last_name"))
            .values_list("full_name", "id")
        )

        print(f"Movies not populated: {all_movies_titles_and_ids}")
        print(f"Authors not populated: {all_authors_names_and_ids}")

        authors_to_expand: List[client.AuthorFromTMDB] = list()
        movies_to_expand: List[client.MovieFromTMDB] = list()

        for tmdb_movie in self.client.find_movies_by_titles(
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
            movies_to_expand.append(tmdb_movie)
            stats.updated_movies += 1

        for tmdb_author in self.client.find_authors_by_name(
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
            authors_to_expand.append(tmdb_author)

        if authors_to_expand or movies_to_expand:
            # Run an expand phase on newly fetched items
            self.expand(
                authors_to_expand=authors_to_expand,
                movies_to_expand=movies_to_expand,
                stats=stats,
            )
        else:
            self.print_success(stats)

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

    def print_success(self, stats: CommandStats):
        self.stdout.write(
            self.style.SUCCESS(f"""Successfully populated DB with TMDB data:
    {stats.created_movies} new movies created - {stats.updated_movies} updated movies
    {stats.created_authors} new authors created - {stats.updated_authors} updated authors""")
        )
