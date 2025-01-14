FROM python:3.12
ENV PYTHONUNBUFFERED 1

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get update && apt-get install -y \
    nodejs \
    python3-distutils \
    build-essential \
    python3-dev \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV VIRTUAL_ENV=/app/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY . /app

RUN pip install poetry uwsgi
RUN pip install -e .[test]

RUN make install
RUN make build_sandbox
RUN cp --remove-destination /app/src/oscar/static/oscar/img/image_not_found.jpg /app/sandbox/public/media/

WORKDIR /app/sandbox/
CMD uwsgi --ini uwsgi.ini
