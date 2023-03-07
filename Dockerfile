FROM python:3.11-slim as install-deps

# install dependencies
WORKDIR /app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# The docker compose file is dependent on the correct working directory to
# properly start uvicorn, so set it here.
WORKDIR /app/src

# No CMD or entrypoint. In development, docker compose targets this stage and
# specifies the entrypoint and command. In production, we fall through to next stage.


FROM python:3.11-slim

ENV FASTAPI_ENV=production

# copy dependencies installed in previous stage and then copy source code
WORKDIR /app
COPY --from=install-deps /app ./
COPY ./src ./src

RUN apt-get -y update && apt-get -y install wget
HEALTHCHECK --interval=1m --timeout=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost/healthcheck/ || exit 1

WORKDIR /app/src
ENTRYPOINT ["uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "80"]
