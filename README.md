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
docker run -p 5000:5000 cassandra-microservices-payment
```


### Temp setup k8 pod

```bash
eval $(minikube docker-env)
minikube start

docker build -f Dockerfile -t cassandra-microservices-payment:latest ./payment-service
docker image tag cassandra-microservices-payment:latest localhost:5000/cassandra-microservices-payment:latest
kubectl create -f payment-service/k8/payment-service.yaml
```