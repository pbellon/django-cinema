from dataclasses import dataclass
from datetime import date, datetime
from typing import Generator, List, Optional, Tuple

import requests
from django.conf import settings
from django.core.management.base import OutputWrapper
from django.core.management.color import Style


@dataclass
class MovieFromTMDB:
    title: str
    original_title: str
    imdb_id: str
    tmdb_id: int
    release_date: date
    fetch_datetime: datetime


@dataclass
class AuthorFromTMDB:
    first_name: str
    last_name: str
    imdb_id: str
    biography: str
    birthday: date
    deathday: Optional[date]
    fetch_datetime: datetime


def parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


class TMDBClient:
    def __init__(self, stdout: OutputWrapper, style: Style):
        self.stdout = stdout
        self.style = style

        print(f"API TOKEN FROM SETTINGS => {settings.TMDB_API_TOKEN}")

        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.TMDB_API_TOKEN}",
        }

        print(self.headers)

    def get(self, path: str, url_params: dict = {}) -> Tuple[dict, bool]:
        BASE_TMDB_API_URL = "https://api.themoviedb.org/3"
        req = requests.get(
            f"{BASE_TMDB_API_URL}{path}",
            params=url_params,
            headers=self.headers,
        )
        print(f"URL to querry: {req.url}")
        if req.status_code != 200:
            self.stdout.write(
                self.style.ERROR(
                    "[TMDB Client] An error occured during request: {req.reason}"
                )
            )
            return ({}, False)

        json = req.json()

        if json.get("success") == False:
            error_msg = json["status_message"]
            self.stdout.write(
                self.style.ERROR(f"[TMDB Client] query failed: {error_msg}")
            )
            return (json, False)

        return (json, True)

    def get_author(self, id: int) -> Optional[AuthorFromTMDB]:
        json, success = self.get(f"/person/{id}")

        if not success:
            return None

        deathday = None
        if json["deathday"] is not None:
            deathday = parse_date(json["deathday"])

        # Poor's man first / last names parsing, not a big deal since we'll
        # almost always show `cinema.models.User.full_name`
        name = json["name"]
        name_splitted = name.split(" ")

        first_name = name_splitted[0]
        last_name = " ".join(name_splitted[1:])

        return AuthorFromTMDB(
            birthday=parse_date(json["birthday"]),
            deathday=deathday,
            first_name=first_name,
            last_name=last_name,
            tmdb_id=json["id"],
            imdb_id=json["imdb_id"],
        )

    def get_movie(self, id: int) -> Optional[MovieFromTMDB]:
        json, success = self.get(f"/movie/{id}")

        if not success:
            return None

        title = json["title"]
        original_title = json["original_title"]
        release_date_str = json["release_date"]
        tmdb_id = json["id"]
        imdb_id = json["imdb_id"]

        return MovieFromTMDB(
            title=title,
            original_title=original_title,
            release_date=parse_date(release_date_str),
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            fetch_datetime=datetime.now(),
        )

    def find_movie_authors(
        self, tmdb_movie: MovieFromTMDB
    ) -> Generator[AuthorFromTMDB]:
        json, success = self.get(
            "/movie/{tmdb_movie.id}/credits", url_params={"language": "en-US"}
        )

        if not success:
            return

        for cast in json["cast"]:
            if cast["job"] == "Director":
                person_maybe = self.get_author(cast["id"])
                if person_maybe:
                    yield person_maybe

    def find_movies_by_titles(
        self, titles: List[str]
    ) -> Generator[MovieFromTMDB]:
        for title in titles:
            json, success = self.get(
                "/search/movie",
                url_params={"page": 1, "language": "en-US", "query": title},
            )

            if not success:
                # skip this title because of issue with request
                continue

            if len(json["results"]) == 0:
                print(
                    f"[TDMB Client] No movie found on TMDB with {title} title"
                )
                continue

            first_res = json["results"][0]

            maybe_movie = self.get_movie(first_res["id"])

            if maybe_movie:
                yield maybe_movie
