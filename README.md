# Django Cinema

> Bootstrapped with [django-startproject](https://github.com/jefftriplett/django-startproject)

## Prequisites
This project relies on [docker][docker], [uv]() and [just]() to properly work.

Here's the suggestion installation process for `uv` and `just` if you don't have them already:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install `just` via cargo
cargo install just
# OR via npm if you don't have cargo
npm install -g just
```


## Quick start

1. Bootstrap the app, will create `.env` file for django configuration env variables
```bash
just bootstrap
```

2. Configure `.env`, needs a valid TMDB token in `TMDB_API_TOKEN` to work properly

3. Start django
```bash
just up --build
```

4. You'll need a superuser to check the admin page
```bash
just manage createsuperuser
```

5. After that you'll need some initial data (movies, authors and maybe links between them). You can use the `seed` command to quickly do that. It will create some authors, movies and spectators data.

```bash
just manage seed
```

5. Run `tmdb` command to start fetching data from TMDB.
```bash
# populate non-populated Movie & Author models
just manage tmdb populate

# expand already populated Movie & Author models, can be run multiple times
# to fetch additionnal data
just manage tmdb expand
```

6. Optionnaly you can run the app in "prod" mode by configuring the `PROFILE` environment variable. Possible values: `dev` (default), `prod`.

## API endpoints

### Movies endpoints
- `GET /api/movies/` - list all movies
  - Can be filtered with `?creation_source=<source>`, source can be `admin` or `tmdb`. 
- `GET /api/movies/<id>/` retrieve a single movie __(requires authentication)__
- `GET /api/movies/by-year/<year>/` list all movies of year set in URL __(requires authentication)__
- `PUT /api/movies/<id>/` update a single movie __(requires authentication)__

### Author
- `GET /api/authors/` list all authors
  - Can be filtered with `?creation_source=<source>`, source can be `admin` or `tmdb`.
- `GET /api/authors/<id>/` retrieve single author __(requires authentication)__
- `PUT /api/authors/<id>/` update a single author __(requires authentication)__
- `DELETE /api/authors/<id>/` delete a single author __(requires authentication)__


### Authentication
#### `POST /api/register` register yourself as a spectator
Request body
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

#### `POST /api/token/` create a JWT token to use the endpoints requiring authentication
Request body
```json
{
  "username": "janedoe",
  "password": "password"
}
```


- `POST /api/token/refresh/` refresh JWT token and obtain a new access token
- `POST /api/token/invalidate/` invalidate a given JWT token and logout


## Improvement points
Those are points not handled I would have added with more time
- Use `nginx` to:
  - serve collected staticfiles
  - configure a reverse proxy to gunicon
- Use caching on some endpoints, especially public ones
- Add tests on all endpoints and core functionnalities

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

# Re-build PIP requirements
$ just lock
```



## `just` Commands

```shell
$ just --list

Available recipes:
    bootstrap *ARGS           # Initialize project with dependencies and environment
    build *ARGS               # Build Docker containers with optional args
    check *ARGS               # Check lint errors with ruff
    console                   # Open interactive bash console in utility container
    down *ARGS                # Stop and remove containers, networks
    lint                      # Run ruff linter on all python code
    lock                      # Compile exports dependencies from pyproject.toml into requirements.txt
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

[docker]: https://www.docker.com/