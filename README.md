# cassandra-microservices

some notes for now..

build the docker image for the respective microservice folder

```bash
docker build -f Dockerfile -t cassandra-microservices-payment:latest ./payment-service
```

make sure it built

```bash
docker image ls
```

to run the image

```bash
docker run cassandra-microservices-payment
```