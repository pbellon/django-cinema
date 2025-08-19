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



## Usage

```shell
# Bootstrap our project
$ just bootstrap

# Build our Docker Image
$ just build

# Run Migrations
$ just manage migrate

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