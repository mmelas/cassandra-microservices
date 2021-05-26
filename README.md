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

### Temp setup k8 pod

```bash
docker run -d -p 5000:5000 --name registry registry:2
eval $(minikube docker-env)
minikube start

docker build -f Dockerfile -t cassandra-microservices-payment:latest ./payment-service
docker image tag cassandra-microservices-payment:latest localhost:5000/cassandra-microservices-payment:latest
docker push localhost:5000/cassandra-microservices-payment
kubectl create -f payment-service/k8/payment-service.yaml
```