# Django Cinema

> Bootstrapped with [django-startproject](https://github.com/jefftriplett/django-startproject)


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

# Lint the project / run pre-commit by hand
$ just lint

# Re-build PIP requirements
$ just lock
```

## `just` Commands

```shell
$ just --list
```
<!-- [[[cog
import subprocess
import cog

list = subprocess.run(['just', '--list'], stdout=subprocess.PIPE)
cog.out(
    f"```\n{list.stdout.decode('utf-8')}```"
)
]]] -->
```
Available recipes:
    bootstrap *ARGS           # Initialize project with dependencies and environment
    build *ARGS               # Build Docker containers with optional args
    console                   # Open interactive bash console in utility container
    down *ARGS                # Stop and remove containers, networks
    lint *ARGS                # Run pre-commit hooks on all files
    lock *ARGS                # Compile requirements.in to requirements.txt
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
    upgrade                   # Upgrade dependencies and lock
```
<!-- [[[end]]] -->
