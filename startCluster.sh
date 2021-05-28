#!/bin/bash

if ! command -v minikube &> /dev/null; then
    echo "minikube not installed. Exiting."
    exit 1
elif ! command -v kubectl &> /dev/null; then
    echo "minikube not installed. Exiting."
    exit 1
fi

# Disable minikube emojis
export MINIKUBE_IN_STYLE=false

# minikube cleaup before start
kubectl delete --all pods --namespace=default &
kubectl delete --all services --namespace=default &
kubectl delete --all deployments --namespace=default &

# Setup minikube
minikube start
eval $(minikube docker-env)
minikube addons enable ingress

# docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order ./order-service

kubectl apply -f order-service/k8s/order-service-cassandra.yaml
# TODO: build all containers for all microservices and start minikube with the right configs