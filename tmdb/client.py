from dataclasses import dataclass
from datetime import date, datetime
from typing import Generator, List, Optional, Set, Tuple

import requests
from django.conf import settings
from django.core.management.base import OutputWrapper
from django.core.management.color import Style
from django.utils import timezone


@dataclass
class MovieFromTMDB:
    db_id: Optional[int]
    title: str
    original_title: str
    imdb_id: str
    tmdb_id: int
    release_date: Optional[date]
    fetch_datetime: datetime
    status: str
    vote: float
    overview: str
    directors_ids: List[int]


@dataclass
class AuthorFromTMDB:
    db_id: Optional[int]
    first_name: str
    last_name: str
    imdb_id: str
    tmdb_id: int
    biography: str
    birthday: date
    deathday: Optional[date]
    fetch_datetime: datetime
    directing_movies_ids: List[int]


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class TMDBClient:
    def __init__(self, stdout: OutputWrapper, style: Style):
        self.stdout = stdout
        self.style = style

        session = requests.Session()
        session.headers.update(
            {
                "accept": "application/json",
                "Authorization": f"Bearer {settings.TMDB_API_TOKEN}",
            }
        )
        self.session = session

    def get(self, path: str, params: dict = {}) -> Tuple[dict, bool]:
        BASE_TMDB_API_URL = "https://api.themoviedb.org/3"
        req = self.session.get(
            f"{BASE_TMDB_API_URL}{path}",
            params=params,
        )
        if req.status_code != 200:
            self.stdout.write(
                self.style.ERROR(
                    f"[TMDB Client] An error occured during request: {req.reason}\n{req.url}"
                )
            )
            return ({}, False)

        result = req.json()

        if not result.get("success", True):
            error_msg = result["status_message"]
            self.stdout.write(
                self.style.ERROR(f"[TMDB Client] query failed: {error_msg}")
            )
            return (result, False)

        return (result, True)

    def get_author(
        self, tmdb_author_id: int, db_id: Optional[int] = None
    ) -> Optional[AuthorFromTMDB]:
        result, success = self.get(
            f"/person/{tmdb_author_id}",
            params={"append_to_response": "movie_credits"},
        )

        if not success:
            return None

        name = result.get("name") or ""
        biography = result.get("biography") or ""
        deathday_str = result.get("deathday") or ""
        birthday_str = result.get("birthday") or ""
        imdb_id = result.get("imdb_id") or ""

        deathday = None
        birthday = None

        if deathday_str:
            deathday = parse_date(deathday_str)

        if birthday_str:
            birthday = parse_date(birthday_str)

        # Fail if no name is detected, will break further features
        if not name:
            raise Exception("Missing `name` attribute in fetched author")

        # Poor's man first / last names parsing, not a big deal since we'll
        # almost always show `cinema.models.User.full_name`
        name_splitted = name.split(" ")
        first_name = name_splitted[0]
        last_name = ""

        if len(name_splitted) > 1:
            last_name = " ".join(name_splitted[1:])

        directing_movie_ids = map(
            lambda role: role["id"],
            filter(
                lambda role: role.get("job") == "Director",
                result["movie_credits"]["crew"],
            ),
        )

        return AuthorFromTMDB(
            db_id=db_id,
            birthday=birthday,
            biography=biography,
            deathday=deathday,
            first_name=first_name,
            last_name=last_name,
            tmdb_id=tmdb_author_id,
            imdb_id=imdb_id,
            directing_movies_ids=list(directing_movie_ids),
            fetch_datetime=timezone.now(),
        )

    def get_authors(self, tmdb_ids: Set[int]) -> Generator[AuthorFromTMDB]:
        for tmdb_id in tmdb_ids:
            try:
                tmdb_author = self.get_author(tmdb_id)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"[TMDBClient] An unexpected error occured while fetching author with {tmdb_id} ID: {e}"
                    )
                )

            if tmdb_author:
                yield tmdb_author

    def get_movie(
        self, tmdb_movie_id: int, db_id: Optional[int] = None
    ) -> Optional[MovieFromTMDB]:
        result, success = self.get(
            f"/movie/{tmdb_movie_id}", params={"append_to_response": "credits"}
        )

        if not success:
            return None

        title = result["title"]
        original_title = result.get("original_title") or ""
        release_date_str = result.get("release_date") or ""
        imdb_id = result["imdb_id"] or ""

        director_ids = map(
            lambda cast: cast["id"],
            filter(
                lambda cast: cast.get("job") == "Director",
                result["credits"]["crew"],
            ),
        )

        release_date = None

        if release_date_str:
            release_date = parse_date(release_date_str)

        return MovieFromTMDB(
            db_id=db_id,
            title=title,
            original_title=original_title,
            release_date=release_date,
            imdb_id=imdb_id,
            tmdb_id=tmdb_movie_id,
            vote=result["vote_average"],
            status=result["status"],
            overview=result["overview"],
            fetch_datetime=timezone.now(),
            directors_ids=list(director_ids),
        )

    def get_movies(self, tmdb_ids: Set[int]) -> Generator[MovieFromTMDB]:
        for tmdb_id in tmdb_ids:
            movie_maybe = self.get_movie(tmdb_id)
            if movie_maybe:
                yield movie_maybe

    def find_movies_by_titles(
        self, titles: List[Tuple[str, int]]
    ) -> Generator[MovieFromTMDB]:
        for title, id in titles:
            search_results, success = self.get(
                "/search/movie",
                params={"page": 1, "language": "en-US", "query": title},
            )

            if not success:
                # skip this title because of issue with request
                continue

            if not search_results["results"]:
                self.stdout(
                    self.style.ERROR(
                        f"[TDMB Client] No movie found on TMDB with {title} title"
                    )
                )
                continue

            first_res = search_results["results"][0]
            maybe_movie = self.get_movie(first_res["id"], db_id=id)

            if maybe_movie:
                yield maybe_movie

    def find_authors_by_name(
        self, names: List[Tuple[str, int]]
    ) -> Generator[AuthorFromTMDB]:
        for name, id in names:
            # ipdb.set_trace()

            search_results, success = self.get(
                "/search/person",
                params={"page": 1, "language": "en-US", "query": name},
            )

            if not success:
                # skip this title because of issue with request
                continue

            if not search_results["results"]:
                self.stdout(
                    self.style.ERROR(
                        f"[TDMB Client] No author found on TMDB with {name} name"
                    )
                )
                continue

            first_res = search_results["results"][0]
            try:
                maybe_author = self.get_author(first_res["id"], db_id=id)

                if maybe_author:
                    yield maybe_author

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"An unexpected error occured while fetching author {name}: {e}"
                    )
                )
