FROM python:2.7
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

RUN groupadd -r django && useradd -r -g django django
COPY . /app
RUN chown -R django /app

WORKDIR /app


RUN make install

USER django

RUN make build_sandbox

RUN cp --remove-destination /app/src/oscar/static/oscar/img/image_not_found.jpg /app/sites/sandbox/public/media/
RUN chmod +x /app/sites/sandbox/deploy/run_uwsgi.sh

CMD /app/sites/sandbox/deploy/run_uwsgi.sh
