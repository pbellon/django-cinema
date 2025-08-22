# ------------------------------------------------------------
# Base/builder layer
# ------------------------------------------------------------
FROM python:3.13-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=pip \
    python -m pip install --upgrade pip uv just-bin
RUN --mount=type=cache,target=/root/.cache,sharing=locked,id=pip \
    python -m uv pip install --system --requirement /tmp/requirements.txt

# Dev layer (autoreload / bind-mount)
FROM builder AS dev
WORKDIR /src
COPY . /src/
CMD ["python", "-m", "manage", "runserver", "0.0.0.0:8000"]

# Release/prod layer
FROM builder AS release
WORKDIR /src
COPY . /src/

RUN python -m manage collectstatic --noinput || true

RUN addgroup --system app && adduser --system --ingroup app app

USER app

EXPOSE 8000
CMD ["gunicorn","--bind","0.0.0.0:8000","config.wsgi:application","--workers","3","--threads","4","--timeout","60"]
