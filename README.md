# NEC (Not-Esri Collector) API
NOTE: This repo is a work in progress.

This repo contains a web API which can be used as a backend to create a generic, geographical survey/data collection
application. This web API could be used by a desktop application, a mobile app, or a frontend web app.

This web API is implemented with FastAPI and SQLAlchemy/GeoAlchemy2. Geographical data is stored in a PostgreSQL
database with the PostGIS extension.

## Build
In development, the app can be run using Linux Docker containers by executing the following command at the repo root:

```docker-compose up```

After starting the app, the API docs can be viewed at http://localhost:10000/docs or http://localhost:10000/redoc.

### Configuration
The following environment variables must be configured, at run time, for proper operation:

* FASTAPI_ENV
  * "development" or "production"
* DATABASE_URL
  * The URL to the PostgreSQL database
* ALLOWED_ORIGINS
  * Comma separated list of CORS allowed origins

For development, all environment variables have already been set in the docker compose file and can
be tweaked as needed. Some other environment variables, not listed above, are required for development and
have also been set in the docker-compose file.

## Database Migrations
Migrations must be added whenever making schema changes to the database. To add a migration, with the app running,
run the following command in a terminal to connect to api container:

```docker-compose exec api bash```

And then run the following command in the "database" directory:

```alembic revision --autogenerate -m "Name of Migration"```

The app has been configured to update the database automatically (apply all pending migrations) at startup.

## Notes
The following documentation was helpful to setup this project:

[FastAPI](https://fastapi.tiangolo.com/)
[FastAPI with PostgreSQL Starter](https://github.com/tiangolo/full-stack-fastapi-postgresql)
