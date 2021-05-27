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

to unset the minikube deamons (detach them from the docker deamon)

```bash
eval $(minikube docker-env -u)
```


### Temp for order service

```bash
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order ./order-service
docker run -p 5000:5000 nicktehrany/wdm-cassandra-microservices:order
```

For starting up cassandra container

```bash
docker pull cassandra:3.11.10
docker run -d --name microservices-database -p 127.0.0.1:9042:9042 cassandra:3.11.10

# Then run the app.py of the ordering service
python3 app.py
```
