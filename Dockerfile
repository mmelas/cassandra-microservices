FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

ENV VIRTUAL_ENV "/venv"
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install pip==21.1.2
RUN apk update && apk add libpq postgresql-dev gcc musl-dev

COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt
RUN CASS_DRIVER_BUILD_CONCURRENCY=4 pip3 install cassandra-driver==3.25.0
COPY . /app/

CMD ["python3", "app.py"]