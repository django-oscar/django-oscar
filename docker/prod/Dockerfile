# Production image of the Oscar sandbox, served by gunicorn behind the host nginx
# (see docker-compose.prod.yml). Build from the repository root:
#   docker compose -f docker-compose.prod.yml build

# --- Stage 1: build the django-oscar wheel (setup.py runs npm to build the assets)
FROM python:3.12-slim AS builder

COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:20-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci

COPY pyproject.toml setup.py setup.cfg MANIFEST.in README.rst LICENSE AUTHORS ./
COPY gulpfile.js ./gulpfile.js
COPY src ./src
RUN pip wheel --no-deps --wheel-dir /wheels .

# --- Stage 2: runtime
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=settings_prod

COPY --from=builder /wheels /wheels
RUN pip install /wheels/*.whl \
        "sorl-thumbnail>=12.10.0,<13.0.0" \
        "easy-thumbnails>=2.9,<2.11" \
        "django-environ>=0.4,<0.13" \
        "whitenoise>=6.7.0,<6.12" \
        "psycopg2-binary>=2.8,<2.10" \
        "Whoosh>=2.7,<2.8" \
        pycountry \
        "djangorestframework>=3.15,<4" \
        "django-oscar-api>=3.3,<3.4" \
        "stripe>=12,<17" \
        "gunicorn>=23,<24" \
    && rm -rf /wheels

# Fixed uid so the host media directory can be chowned to it (10001:10001)
RUN groupadd -r -g 10001 django && useradd -r -u 10001 -g django -d /app django

WORKDIR /app/sandbox
COPY --chown=django:django sandbox/ ./
COPY --chown=django:django docker/prod/entrypoint.sh /entrypoint.sh

# Writable locations, mounted as volumes in docker-compose.prod.yml
RUN mkdir -p public/media whoosh_index \
    && chown -R django:django public whoosh_index \
    && chmod +x /entrypoint.sh

USER django

# Static files are baked into the image and served by whitenoise. The settings
# need these variables to import; collectstatic does not touch the database.
RUN SECRET_KEY=build ALLOWED_HOSTS=localhost \
    DATABASE_NAME=build DATABASE_USER=build DATABASE_PASSWORD=build \
    python manage.py collectstatic --noinput

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "30", \
     "--access-logfile", "-"]
