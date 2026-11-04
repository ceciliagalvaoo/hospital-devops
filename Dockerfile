# syntax=docker/dockerfile:1

# Base image pinned to a patch version; docs/docker-build.md records its digest.
ARG PYTHON_IMAGE=python:3.13.18-slim

############ Stage 1: build ############
FROM ${PYTHON_IMAGE} AS build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build

# Isolated virtual environment without its own pip; only this directory reaches the runtime stage.
RUN python -m venv --without-pip /opt/venv

# Dependency definition first: rebuilt only when requirements.txt changes.
# The base image's pip installs into the virtual environment, so pip itself is not copied.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip --python /opt/venv/bin/python install -r requirements.txt

############ Stage 2: runtime ############
FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Unprivileged runtime user; application files stay owned by root (read-only for it).
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=build /opt/venv /opt/venv
COPY alembic.ini .
COPY migrations ./migrations
COPY app ./app

USER 10001:10001
EXPOSE 8000

# Declared last: a new version or commit changes only the metadata, not the cached layers.
ARG APP_VERSION=0.0.0
ARG VCS_REF=unknown
LABEL org.opencontainers.image.title="hospital-devops" \
      org.opencontainers.image.description="Hospital management web application (FastAPI and PostgreSQL)" \
      org.opencontainers.image.source="https://github.com/ceciliagalvaoo/hospital-devops" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
