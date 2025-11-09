# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

WORKDIR /repo
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN pip install -U uv

COPY pyproject.toml uv.lock ./
COPY pkgs/python pkgs/python
COPY srvs/api/pyproject.toml srvs/api/

ENV UV_PROJECT_ENVIRONMENT=/repo/srvs/api/.venv
RUN uv sync --package quizbee --frozen --no-dev

COPY srvs/api srvs/api

EXPOSE 8000
CMD ["uv", "run", "--directory", "/repo/srvs/api", "--", "gunicorn", "-c", "gunicorn.conf.py", "src.bootstrap:app"]
