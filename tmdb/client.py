from dataclasses import dataclass
from datetime import date, datetime
from typing import Generator, List, Optional, Tuple, Iterator

import requests
from django.conf import settings
from django.core.management.base import OutputWrapper
from django.core.management.color import Style


@dataclass
class MovieFromTMDB:
    db_id: Optional[int]
    title: str
    original_title: str
    imdb_id: str
    tmdb_id: int
    release_date: date
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
                    "[TMDB Client] An error occured during request: {req.reason}"
                )
            )
            return ({}, False)

        result = req.json()

        if result.get("success") == False:  # noqa: E712
            error_msg = result["status_message"]
            self.stdout.write(
                self.style.ERROR(f"[TMDB Client] query failed: {error_msg}")
            )
            return (result, False)

        return (result, True)

    def get_author(
        self, id: int, db_id: Optional[int] = None
    ) -> Optional[AuthorFromTMDB]:
        result, success = self.get(
            f"/person/{id}", params={"append_to_response": "movie_credits"}
        )

        if not success:
            return None

        deathday = None
        birthday = None

        if result["deathday"] is not None:
            deathday = parse_date(result["deathday"])

        if result["birthday"] is not None:
            birthday = parse_date(result["birthday"])

        # Poor's man first / last names parsing, not a big deal since we'll
        # almost always show `cinema.models.User.full_name`
        name = result["name"]
        name_splitted = name.split(" ")

        first_name = name_splitted[0]
        last_name = " ".join(name_splitted[1:])

        directing_movie_ids = map(
            lambda role: role["id"],
            filter(
                lambda role: role.get("job") == "Director",
                result["movie_credits"]["cast"],
            ),
        )

        if result["birthday"] is None:
            print(f"Found undefined birthday for author {id}")

        return AuthorFromTMDB(
            db_id=db_id,
            birthday=birthday,
            biography=result["biography"],
            deathday=deathday,
            first_name=first_name,
            last_name=last_name,
            tmdb_id=result["id"],
            imdb_id=result["imdb_id"],
            directing_movies_ids=list(directing_movie_ids),
            fetch_datetime=datetime.now(),
        )

    def get_movie(
        self, id: int, db_id: Optional[int] = None
    ) -> Optional[MovieFromTMDB]:
        result, success = self.get(
            f"/movie/{id}", params={"append_to_response": "credits"}
        )

        if not success:
            return None

        title = result["title"]
        original_title = result["original_title"]
        release_date_str = result["release_date"]
        tmdb_id = result["id"]
        imdb_id = result["imdb_id"]

        director_ids = map(
            lambda cast: cast["id"],
            filter(
                lambda cast: cast.get("job") == "Director",
                result["credits"]["crew"],
            ),
        )

        return MovieFromTMDB(
            db_id=db_id,
            title=title,
            original_title=original_title,
            release_date=parse_date(release_date_str),
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            vote=result["vote_average"],
            status=result["status"],
            overview=result["overview"],
            fetch_datetime=datetime.now(),
            directors_ids=list(director_ids),
        )

    def find_movies_by_titles(
        self, titles: List[Tuple[str, int]]
    ) -> Generator[MovieFromTMDB]:
        for title, id in titles:
            json, success = self.get(
                "/search/movie",
                params={"page": 1, "language": "en-US", "query": title},
            )

            if not success:
                # skip this title because of issue with request
                continue

            if len(json["results"]) == 0:
                self.stdout(
                    self.style.ERROR(
                        f"[TDMB Client] No movie found on TMDB with {title} title"
                    )
                )
                continue

            first_res = json["results"][0]

            maybe_movie = self.get_movie(first_res["id"], db_id=id)

            if maybe_movie:
                yield maybe_movie

    def find_authors_by_name(
        self, names: List[Tuple[str, int]]
    ) -> Generator[AuthorFromTMDB]:
        for name, id in names:
            json, success = self.get(
                "/search/movie",
                params={"page": 1, "language": "en-US", "query": name},
            )

            if not success:
                # skip this title because of issue with request
                continue

            if len(json["results"]) == 0:
                self.stdout(
                    self.style.ERROR(
                        f"[TDMB Client] No author found on TMDB with {name} name"
                    )
                )
                continue

            first_res = json["results"][0]
            maybe_author = self.get_author(first_res["id"], db_id=id)

            if maybe_author:
                yield maybe_author
