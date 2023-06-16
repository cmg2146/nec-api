FROM python:3.11-slim as base

ARG POETRY_VERSION=1.5.1

# install production dependencies
WORKDIR /app
COPY ./pyproject.toml ./poetry.lock* ./
ENV POETRY_VIRTUALENVS_CREATE=false
# TODO: subsequent stages do not need poetry installed - potential performance improvement
RUN pip install poetry==$POETRY_VERSION && poetry install --no-dev --no-root --no-directory


FROM base as development

ENV FASTAPI_ENV=development

# install dev dependencies, production dependencies are already installed in base stage
RUN poetry install --no-root --no-directory

# The docker compose file is dependent on the correct working directory to
# properly start uvicorn, so set it here.
WORKDIR /app/src

# No CMD or entrypoint. In development, docker compose targets this stage and
# specifies the entrypoint and command. In production, we fall through to next stage.


FROM base as production

ENV FASTAPI_ENV=production

COPY ./src /app/src

RUN apt-get -y update && apt-get -y install wget
HEALTHCHECK --interval=1m --timeout=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost/healthcheck/ || exit 1

WORKDIR /app/src
ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "80"]
