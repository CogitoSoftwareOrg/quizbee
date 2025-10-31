FROM python:3.13-slim

WORKDIR /repo
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN pip install -U uv

COPY pyproject.toml uv.lock ./
COPY pkgs/python pkgs/python
COPY apps/api/pyproject.toml apps/api/

ENV UV_PROJECT_ENVIRONMENT=/repo/apps/api/.venv
RUN uv sync --package quizbee --frozen --no-dev

COPY apps/api apps/api

EXPOSE 8000
CMD ["uv", "run", "--directory", "/repo/apps/api", "--", "gunicorn", "-c", "gunicorn.conf.py", "src.bootstrap:app"]
