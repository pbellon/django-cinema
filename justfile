
set dotenv-load := true

profile := env_var_or_default("PROFILE", "dev")

db_user := env_var_or_default('POSTGRES_USER', 'postgres')
db_pass := env_var_or_default('POSTGRES_PASSWORD', 'postgres')
db_name := env_var_or_default('POSTGRES_DB', 'cinema')
db_url := env_var_or_default(
  'DATABASE_URL',
  'postgres://' + db_user + ':' + db_pass + '@db:5432' + '/' + db_name
)

# Show list of available commands
@_default:
    just --list

# Initialize project with dependencies and environment
bootstrap *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail

    if [ ! -f ".env" ]; then
        cp .env.sample .env
        echo ".env created"
    fi

    if [ -n "${VIRTUAL_ENV-}" ]; then
        python -m pip install --upgrade pip uv
    else
        echo "Skipping pip steps as VIRTUAL_ENV is not set"
    fi

    if [ ! -f "requirements.txt" ]; then
        uv export --format requirements-txt > requirements.txt
        echo "requirements.txt created"
    fi

    just upgrade

    if [ -f "compose.yml" ]; then
        just build {{ ARGS }} --pull
    fi

# Run docker compose --profile dev {{ args }}
@compose_dev *ARGS:
    docker compose --profile dev {{ ARGS }}

@compose *ARGS:
    docker compose --profile {{profile}} {{ ARGS }}

# Build Docker containers with optional args
@build *ARGS:
    just compose build {{ ARGS }}

# Open interactive bash console in utility container
@console:
    just compose_dev run \
        --no-deps \
        --rm \
        utility /bin/bash

# Stop and remove containers, networks
@down *ARGS:
    just compose down {{ ARGS }}

# Format justfile with unstable formatter
[private]
@fmt:
    just --fmt --unstable

# Run ruff linter on all python code
@lint:
    uvx ruff format

# Check lint errors with ruff
@check *ARGS:
    uvx ruff check {{ ARGS }}

# Compile and exports dependencies from pyproject.toml into requirements.txt
@lock:
    uv export --format requirements-txt > requirements.txt
    just compose build

# Show logs from containers
@logs *ARGS:
    just compose logs {{ ARGS }}

# Run Django management commands
@manage *ARGS:
    just compose run \
        --no-deps \
        --rm \
        utility \
            python -m manage {{ ARGS }}

# Dump database to file
@pg_dump file='db.dump':
    just compose run \
        --no-deps \
        --rm \
        db pg_dump \
            --dbname "{{db_url}}" \
            --file /src/{{ file }} \
            --format=c \
            --verbose

# Restore database dump from file
@pg_restore file='db.dump':
    just compose run \
        --no-deps \
        --rm \
        db pg_restore \
            --clean \
            --dbname "{{db_url}}" \
            --if-exists \
            --no-owner \
            --verbose \
            /src/{{ file }}

# Restart containers
@restart *ARGS:
    just compose restart {{ ARGS }}

# Run command in utility container
@run *ARGS:
    just compose_dev run \
        --no-deps \
        --rm \
        utility {{ ARGS }}

# Start services in detached mode by default
@start *ARGS="--detach":
    just up {{ ARGS }}

# Stop services (alias for down)
@stop *ARGS:
    just down {{ ARGS }}

# Show and follow logs
@tail:
    just logs --follow

# Run pytest with arguments
@test *ARGS:
    just compose_dev run \
        --no-deps \
        --rm \
        utility python -m pytest {{ ARGS }}

# Start containers
@up *ARGS:
    just compose up {{ ARGS }}

