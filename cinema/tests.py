# Create your tests here.
import pytest
from rest_framework.test import APIClient
from model_bakery import baker

from cinema.models import Spectator, Movie


def obtain_access_token(
    client: APIClient, username="tester", password="testing1234"
) -> str:
    # SimpleJWT obtain token endpoint per project README
    resp = client.post(
        "/api/token/",
        {"username": username, "password": password},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    access_token = resp.data["access"]
    return access_token


@pytest.fixture
def spectator(db) -> Spectator:
    spectator = Spectator(
        username="tester",
        email="tester@example.com",
    )
    spectator.set_password("testing1234")
    spectator.save()
    return spectator


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_api_client(
    spectator: Spectator, api_client: APIClient
) -> APIClient:
    token = obtain_access_token(api_client)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.mark.django_db
def test_list_movies_is_public(api_client: APIClient):
    baker.make(Movie, title="One")
    baker.make(Movie, title="Two")
    baker.make(Movie, title="Three")

    resp = api_client.get("/api/movies/")
    assert resp.status_code == 200
    assert isinstance(resp.data["results"], list)
    assert len(resp.data) >= 3


@pytest.mark.django_db
def test_retrieve_movie_requires_auth(api_client: APIClient):
    movie = baker.make(Movie, title="Secured")
    resp = api_client.get(f"/api/movies/{movie.id}/")
    # Unauthenticated should be blocked
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_retrieve_movie_with_auth(authenticated_api_client: APIClient):
    movie = baker.make(Movie, title="Allowed")
    resp = authenticated_api_client.get(f"/api/movies/{movie.id}/")
    assert resp.status_code == 200
    assert resp.data["id"] == movie.id
    assert resp.data["title"] == "Allowed"
