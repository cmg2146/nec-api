# NEC (Not-Esri Collector) API
This repo contains a web API which can be used as a backend to create a generic, geospatial data collection
application. This web API could be used by a desktop application, a mobile app, or a frontend web app.

This web API is implemented with FastAPI and SQLAlchemy/GeoAlchemy2. Geographical data is stored in a PostgreSQL
database with the PostGIS extension.

This app is not production ready and currently lacks features like:
* Authentication
* Proper storage for file uploads
* API versioning
* logging
* auditing database changes
* tests

## Design/Data Model
This app is targeted towards collecting data which happens to have a geographical component rather than collecting
purely geographical data. This is an important distinction to note when understanding the design/data model, which
is described below:

* Sites - A surveyed physical location/facility. A site is denoted by a 2-dimensional, geographic point in the database.
A Site can also have any number of sub-Sites, accomplished with a self-referencing foreign key, which can be useful
for large Sites.
* Surveys - A Survey contains the actual surveyed data (Assets, Panos, Photos, etc.) at a Site. A Site can have
multiple Surveys, which is useful for repeat Surveys.
* Assets - An important item which occupies a 2-dimensional, geographic point.
* Asset Properties - Used for storing custom, key/value properties of an Asset.
* Asset Types - Useful for categorizing Assets into custom types.
* Panos - A 360 degree, spherical photo. A Pano also occupies a 2-dimensional, geographic point in the database.
* Photos - A typical photo. A Photo also occupies a 2-dimensional, geographic point in the database.
* Overlays - A 2-dimensional image which is overlayed on a map. An Overlay's placement is described by a simple,
rectangualar boundary. Overlays can be useful for displaying floor plans or other imagery in the survey.

Note: This model may not work in an inventory or change-tracking system because assets may be duplicated across
multiple surveys at the same site. Although, there is a column in the survey table to denote whether it is the latest
survey for its associated site and the database only allows one latest survey per site.

## Build
In development, the app can be run using Linux Docker containers by executing the following command at the repo root:

```docker-compose up```

After starting the app, the Open API docs can be viewed at http://localhost:10000/docs. Alternative API docs are
available at http://localhost:10000/redoc.

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
