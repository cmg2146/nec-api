# NEC (Not-Esri Collector) API
This repo contains a web API which can be used as a backend to create a generic, geographical survey/data collection
application. This web API could be used by a desktop application, a mobile app, or a frontend web app.

This web API is implemented with FastAPI and SQLAlchemy/GeoAlchemy2. Geographical data is stored in a PostgreSQL
database with the PostGIS extension.

This app is not production ready and lacks features like:
* Authentication
* API versioning
* logging
* auditing database changes
* tests
* Proper storage for user uploads

## Build
In development, the app can be run using Linux Docker containers by executing the following command at the repo root:

```docker-compose up```

After starting the app, the API docs can be viewed at http://localhost:10000/docs or http://localhost:10000/redoc.

### Configuration
The following run-time environment variables must be configured for proper operation:

* FASTAPI_ENV
  * "development" or "production"
* DATABASE_URL
  * The URL to the PostgreSQL database
* FILE_UPLOAD_DIR
  * The directory where user file uploads will be stored. For production, a storage service should
  be used, but a file system will do for now.

The following run-time environment variables are optional:

* ALLOWED_ORIGINS
  * Comma separated list of CORS allowed origins. If not provided, CORS will not be enabled.

For development, required environment variables have already been set in the docker compose file and can
be tweaked as needed. Some other environment variables, not listed above, may be required for development
only and should be set in the docker-compose file.

## Database Migrations
Migrations must be added whenever making schema changes to the database. To add a migration, with the app running,
run the following command in a terminal to connect to api container:

```docker-compose exec api bash```

And then run the following command in the "src" directory (the directory containing "alembic.ini"):

```alembic revision --autogenerate -m "Name of Migration"```

This will add a new migration to the code on your host, not in the container. This only works because the
source is bind mounted in development.

For development, the database is created automatically and pending migrations are automatically applied on app startup.

## Notes
The following documentation was helpful to setup this project:

[FastAPI](https://fastapi.tiangolo.com/)

[FastAPI with PostgreSQL Starter](https://github.com/tiangolo/full-stack-fastapi-postgresql)

TODO:
* add spatial queries
* get rid of db parameter to all crud functions
* Figure out how to use shapely types in pydantic model
* verify/add logic for related entities.
* Go through TODOs in code
* handle cascades/ deletions on related entities
* replace filesystem for uploads with azurite
