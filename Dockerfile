FROM python:3.5
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN groupadd -r django && useradd -r -g django django
COPY . /app
RUN chown -R django /app

WORKDIR /app


RUN make install
RUN pip3 install psycopg2

USER django

RUN make build_sandbox

RUN cp --remove-destination /app/src/oscar/static/oscar/img/image_not_found.jpg /app/sites/sandbox/public/media/

CMD uwsgi --ini /app/sites/sandbox/deploy/uwsgi.ini
