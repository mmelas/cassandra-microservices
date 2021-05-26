# cassandra-microservices

some notes for now..

build the docker image for the respective microservice folder

```bash
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:payment ./payment-service
```

make sure it built

```bash
docker image ls
```

to run the image

```bash
docker run -p 5000:5000 nicktehrany/wdm-cassandra-microservices:payment
```

to push image to dockerhub

```bash
docker push nicktehrany/wdm-cassandra-microservices:payment
```