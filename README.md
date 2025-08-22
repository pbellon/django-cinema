
[docker]: https://www.docker.com/
[just]: https://just.systems/man/en/packages.html
[uv]: https://docs.astral.sh/uv/getting-started/installation/

# Django Cinema

> Bootstrapped with [django-startproject](https://github.com/jefftriplett/django-startproject)

## Prerequisites
This project relies on [docker][docker], [uv][uv] and [just][just].

Here's the suggested installation process for `uv` and `just` if you don't have them already:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install `just` via cargo
cargo install just
# OR via npm if you don't have cargo
npm install -g just
```

Or you can check the linked documentation pages to see how to install them on your machine.


## Quick start

1. Bootstrap the app; this will create an `.env` file to configure the application's environment variables
```bash
just bootstrap
```

2. Configure the `.env` file: you need a valid TMDB token in `TMDB_API_TOKEN` and set a secure `DJANGO_SECRET_KEY` variable

3. Start Django
```bash
just up --build
```

4. You'll need a superuser to check the admin page
```bash
just manage createsuperuser
```

5. After that you'll need some initial data (movies, authors and maybe links between them). You can use the `seed` command to quickly do that. It will create authors, movies and spectators data.

```bash
just manage seed
```

6. Run `tmdb` command to start fetching data from TMDB.
```bash
# populate non-populated Movie & Author models (i.e: models created by the admin)
just manage tmdb populate

# expand already populated Movie & Author models, can be run multiple times
# to fetch additional data
just manage tmdb expand
```

7. Optionally you can run the app in a "prod" profile by configuring the `PROFILE` environment variable. Possible values: `dev` (default), `prod`.
  - But be careful to remove `DJANGO_DEBUG=True` from your `.env` if it's set
  - And to run `just manage migrate` after launching Django (`just up --build`) if this is the first time the database is created (i.e., if you never launched in the dev profile before)


At this point you should have access to the admin & API URLs
- http://localhost:8000/admin
- http://localhost:8000/api

## API endpoints
All endpoints marked with __(AUTH)__ require authentication. See `/api/token`
below for more details on how to authenticate.

### Movies

#### `GET /api/movies/`
List all movies. 

> Can be filtered with `?creation_source=<source>`, source can be `admin` or `tmdb`. 

##### Response

```json
{
    "count": 826,
    "next": "http://localhost:8000/api/movies/?page=2",
    "previous": null,
    "results": [
        {
            "id": 663,
            "title": "1-100",
            "details": "http://localhost:8000/api/movies/663/",
            "release_date": "1976-07-26"
        },
        {
            "id": 815,
            "title": "14 Up in America",
            "details": "http://localhost:8000/api/movies/815/",
            "release_date": "1998-01-01"
        },
        {
            "id": 655,
            "title": "1492: Conquest of Paradise",
            "details": "http://localhost:8000/api/movies/655/",
            "release_date": "1992-10-09"
        },
        ...
    ]
}
```

#### __(AUTH)__ `GET /api/movies/<id>/`
Retrieve a single movie
##### Response
```json
{
    "id": 663,
    "title": "1-100",
    "description": "A short film by Peter Greenaway.",
    "release_date": "1976-07-26",
    "status": "Released",
    "evaluation": 0,
    "imdb_page": "https://www.imdb.com/title/tt0077112/",
    "authors": [
        {
            "id": 72,
            "full_name": "Peter Greenaway",
            "details": "http://localhost:8000/api/authors/72/"
        }
    ]
}
```

#### __(AUTH)__ `GET /api/movies/by-year/<year>/` 
List all movies released in the year set in the URL via their `release_date`.

##### Response
```json
[
    {
        "id": 7,
        "title": "Lincoln",
        "details": "http://localhost:8000/api/movies/7/",
        "release_date": "2012-11-09"
    },
    {
        "id": 49,
        "title": "The Dark Knight Rises",
        "details": "http://localhost:8000/api/movies/49/",
        "release_date": "2012-07-17"
    },
    ...
]
```

#### __(AUTH)__  `PUT /api/movies/<id>/` or `PATCH /api/movies/<id>/`

Update a single movie. Available fields:
- `title`: `String`, must not exceed 300 characters
- `description`: `String`
- `release_date`: `String` (must be a valid date, can be null)
- `imdb_id`: `String` IMDb id of this movie
- `evaluation`: `Number`, integer between 0 and 5
  - 0 => Not Rated
  - 1 => Very Bad
  - 2 => Bad
  - 3 => Medium
  - 4 => Good
  - 5 => Very Good
- `status`: `String`, possible values:
  - `Unknown`
  - `Rumored`
  - `In Production`
  - `Post Production`
  - `Released`
  - `Canceled`
  

##### Request
```json
{
  "title": "Lincoln (updated)",
  "release_date": "2022-11-02"
}
```

##### Response
```json
{
    "id": 7,
    "title": "Lincoln (updated)",
    "description": "The revealing story of the 16th US President's tumultuous final months in office. In a nation divided by war and the strong winds of change, Lincoln pursues a course of action designed to end the war, unite the country and abolish slavery. With the moral courage and fierce determination to succeed, his choices during this critical moment will change the fate of generations to come.",
    "release_date": "2022-11-02",
    "status": "Released",
    "evaluation": 4,
    "imdb_page": "https://www.imdb.com/title/tt0443272/",
    "authors": [
        {
            "id": 35,
            "full_name": "Steven Spielberg",
            "details": "http://localhost:8000/api/authors/35/"
        }
    ]
}
```

#### __(AUTH)__ `POST /api/movies/<id>/evaluate/`
Create an evaluation on a movie. 

Fields:
- `score`: `Number`, number between 0 and 100 representing your evaluation of the movie
- `comment`: `String`, optional comment

##### Request
```json
{
    "score": 20,
    "comment": "Not really good"
}
```

### Authors

#### `GET /api/authors/`

List all authors
> Can be filtered with `?creation_source=<source>`, source can be `admin` or `tmdb`.

##### Response
```json
{
    "count": 44,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 70,
            "full_name": "Roy Andersson",
            "details": "http://localhost:8000/api/authors/70/"
        },
        {
            "id": 51,
            "full_name": "Andrea Arnold",
            "details": "http://localhost:8000/api/authors/51/"
        },
        ...
    ]
}
```

#### __(AUTH)__ `GET /api/authors/<id>/` 

Retrieve a single author

##### Response
```json
{
    "id": 70,
    "full_name": "Roy Andersson",
    "biography": "Roy Arne Lennart Andersson is ...",
    "imdb_page": "https://www.imdb.com/name/nm0027815/",
    "first_name": "Roy",
    "last_name": "Andersson",
    "imdb_id": "nm0027815",
    "birth_day": "1943-03-31",
    "death_day": null,
    "movies": [
        {
            "id": 73,
            "title": "Cinema 16: European Short Films (U.S. Edition)",
            "details": "http://localhost:8000/api/movies/73/",
            "release_date": "2007-09-25"
        },
        ...
    ]
}
```

#### __(AUTH)__ `PUT /api/authors/<id>/` or `PATCH /api/authors/<id>/`
Update a single author

Available fields:
- `biography`: `String`
- `imdb_id`: `String`, IMDb id of this author
- `first_name`: `String`
- `last_name`: `String`
- `birth_day`: `String`, must be a valid date string, can be null
- `death_day`: `String`, must be a valid date string, can be null


##### __(AUTH)__  `DELETE /api/authors/<id>/`

Delete a single author. Must have no associated movies otherwise will return an
HTTP 409 (Conflict) error.

#### __(AUTH)__  `POST /api/authors/<id>/evaluate/`
Create an evaluation on an author

##### Request
```json
{
    "score": 90,
    "comment": "The best"
}
```

##### Response
```json
{
    "id": 2,
    "author": 70,
    "spectator": 80,
    "score": 90,
    "comment": "The best"
}
```


### Favorites

#### __(AUTH)__ `GET /api/favorites/authors/`

List your favorite authors

##### Response
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 70,
            "full_name": "Roy Andersson",
            "details": "http://localhost:8000/api/authors/70/"
        }
    ]
}
```

#### __(AUTH)__ `POST /api/favorites/authors/`

Add an author to your favorites

##### Request
```json
{
  "author_id": 70
}
```

#### __(AUTH)__ `DELETE /api/favorites/authors/<author_id>/`

Remove an author from your favorites via its ID.


#### __(AUTH)__  `GET /api/favorites/movies/`

List your favorite movies

##### Response

```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 8,
            "title": "There Will Be No Leave Today",
            "details": "http://localhost:8000/api/movies/8/",
            "release_date": "1959-05-09"
        }
    ]
}
```

#### __(AUTH)__ `POST /api/favorites/movies/`

Add a movie to your favorites

##### Request
```json
{
  "movie_id": 8
}
```

#### __(AUTH)__ `DELETE /api/favorites/movies/<id>/`

Remove a movie from your favorites


### Authentication
#### `POST /api/register`
Register yourself as a spectator. Required in order to access endpoints protected by authentication.
Use `/api/token/` endpoints below to generate a token.

##### Request
```json
{
  "username": "janedoe",
  "password": "password",
  "email": "janedoe@doe-corporation.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "biography": "Some biography"
}
```

#### `POST /api/token/`
Create a JWT token to use the endpoints requiring authentication

##### Request
```json
{
  "username": "janedoe",
  "password": "password"
}
```

##### Response
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NTk0ODU3OSwiaWF0IjoxNzU1ODYyMTc5LCJqdGkiOiJmOGU5YTYyZGNiMmI0YzViYWMyOGEzY2EwNmMzMjdhNyIsInVzZXJfaWQiOiI0OCJ9.4dUq4-_rMDB7LjH6B7jbpWXV9k3-bqe7S_NTlWGyJ4U",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU1ODYyNDc5LCJpYXQiOjE3NTU4NjIxNzksImp0aSI6IjdiMjBmYmFjNWJkZDQwN2I4ZGI0YTkwM2ZmZmExZDIyIiwidXNlcl9pZCI6IjQ4In0.0EyuSdgzpA8esA6NLNRsetQ-7-Kx89-ReHQopO_qH9I"
}
```

Once you have your `access` token, use it in __(AUTH)__ endpoints by setting an `Authorization: Bearer {access}` HTTP header.

#### `POST /api/token/refresh/` 
Refresh JWT token and obtain a new access token

##### Request
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NTk1NzY1MywiaWF0IjoxNzU1ODcxMjUzLCJqdGkiOiJjYWQ2ODExMzk2ZDY0NTM4OGE0OWE3NmZhMzE2ZjZjZiIsInVzZXJfaWQiOiI4MCJ9.c_IjuSA4X7CL11upNj742NEgMLlRwn5q1d4Go6OAxXw"
}
```

##### Response
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU1ODcxNTczLCJpYXQiOjE3NTU4NzEyNzMsImp0aSI6IjU1NGFhMWZkMjRkYzRhY2FhYTBkNTAwMDg2MzE2ZTJlIiwidXNlcl9pZCI6IjgwIn0.C0e1K0QazsCd0NfCbb2TcvkAYsbELZ7YwOhkXVT9vjE"
}
```


##### `POST /api/token/invalidate/` 
Invalidate a given JWT token and effectively "logout"

```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NTk1NzY1MywiaWF0IjoxNzU1ODcxMjUzLCJqdGkiOiJjYWQ2ODExMzk2ZDY0NTM4OGE0OWE3NmZhMzE2ZjZjZiIsInVzZXJfaWQiOiI4MCJ9.c_IjuSA4X7CL11upNj742NEgMLlRwn5q1d4Go6OAxXw"
}
```



## Improvement points
Those are points not handled I would have added with more time
- Use `nginx` to:
  - serve collected static files
  - configure a reverse proxy to gunicorn
- Use caching (probably using Redis) on some endpoints, especially public ones
- Add tests on all endpoints and core functionalities
- Add GitHub Actions to check proper linting and run tests
- Improve API discoverability with additional links and automatic OpenAPI
  schema generation with `drf-spectacular`
- Automate API endpoint documentation generation inside repository

## Usage

```shell
# Bootstrap our project
$ just bootstrap

# Build our Docker Image
$ just build

# Create a Superuser in Django
$ just manage createsuperuser

# Run Django on http://localhost:8000/
$ just up

# Run Django in background mode
$ just start

# Stop all running containers
$ just down

# Open a bash shell/console
$ just console

# Run Tests
$ just test

# Lint the project
$ just lint

# Check lint errors
$ just check

# Rebuild PIP requirements
$ just lock

```



## `just` Commands

```shell
$ just --list
Available recipes:
    bootstrap *ARGS           # Initialize project with dependencies and environment
    build *ARGS               # Build Docker containers with optional args
    check *ARGS               # Check lint errors with ruff
    compose *ARGS             # Run docker compose with --profile depending on PROFILE environement variable
    compose_dev *ARGS         # Run docker compose --profile dev {{ args }}
    console                   # Open interactive bash console in utility container
    down *ARGS                # Stop and remove containers, networks
    lint                      # Run ruff linter on all python code
    lock                      # Compile and export dependencies from pyproject.toml into requirements.txt
    logs *ARGS                # Show logs from containers
    manage *ARGS              # Run Django management commands
    pg_dump file='db.dump'    # Dump database to file
    pg_restore file='db.dump' # Restore database dump from file
    restart *ARGS             # Restart containers
    run *ARGS                 # Run command in utility container
    start *ARGS="--detach"    # Start services in detached mode by default
    stop *ARGS                # Stop services (alias for down)
    tail                      # Show and follow logs
    test *ARGS                # Run pytest with arguments
    up *ARGS                  # Start containers
```
