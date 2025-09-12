#!/bin/sh

mkdir media
mkdir media/news_uploads

export DB_HOST=rsapa_database

poetry run alembic upgrade head
poetry run uvicorn app.main:app --host 0.0.0.0
