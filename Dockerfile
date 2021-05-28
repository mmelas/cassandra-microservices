FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

ENV VIRTUAL_ENV "/venv"
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"
RUN pip3 install pip==21.1.2
RUN apt-get install libpq-dev

COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app/

EXPOSE 5000
CMD ["python3", "app.py"]