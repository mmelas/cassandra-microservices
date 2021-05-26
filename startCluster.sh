#!/bin/bash

if ! command -v minikube &> /dev/null; then
    echo "minikube not installed. Exiting."
    exit 1
elif ! command -v kubectl &> /dev/null; then
    echo "minikube not installed. Exiting."
    exit 1
fi

# Setup minikube
minikube start
eval $(minikube docker-env)

docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:payment ./payment-service

kubectl apply -f payment-service/k8/payment-service.yaml
# TODO: build all containers for all microservices and start minikube with the right configs