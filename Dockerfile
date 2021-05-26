FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

ENV VIRTUAL_ENV "/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install -r requirements.txt
COPY . /app/

EXPOSE 5000
CMD ["python3", "app.py"]