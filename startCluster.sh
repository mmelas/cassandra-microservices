#!/bin/bash

if ! command -v minikube &> /dev/null; then
    echo "minikube not installed. Exiting."
    exit 1
elif ! command -v kubectl &> /dev/null; then
    echo "kubectl not installed. Exiting."
    exit 1
elif ! command -v helm &> /dev/null; then
    echo "helm not installed. Exiting."
    exit 1
fi

# Disable minikube emojis
export MINIKUBE_IN_STYLE=false

# Setup minikube
minikube start
eval $(minikube docker-env)
minikube addons enable ingress

# TODO: build all containers for all microservices and start minikube with the right configs
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order-service ./order-service

# Install helm repos for different databases
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install postgresql --set postgresqlPassword=password bitnami/postgresql
# helm install cassandra --set dbUser.password=password bitnami/cassandra

echo "Waiting for db to startup"
sleep 20

# Setting up postgres client                                                                                                                        
kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" --command -- psql --host postgresql -U postgres -d postgres -p 5432 -c "create database order_service"