#!/usr/bin/env bash

# apply database migrations first
alembic upgrade head

# start the api
uvicorn app.main:app "$@"
