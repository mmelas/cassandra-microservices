#!/bin/bash

BLUE=$'\033[1;34m'
RED=$'\033[1;31m'

if ! command -v minikube &> /dev/null; then
    echo "{RED}minikube not installed. Exiting."
    exit 1
elif ! command -v kubectl &> /dev/null; then
    echo "{RED}kubectl not installed. Exiting."
    exit 1
elif ! command -v helm &> /dev/null; then
    echo "{RED}helm not installed. Exiting."
    exit 1
fi

# Disable minikube emojis
export MINIKUBE_IN_STYLE=false

# Setup minikube
minikube start --memory 8192 --cpus=4
eval $(minikube docker-env)
minikube addons enable ingress

# TODO: build all containers for all microservices and start minikube with the right configs
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order-service ./order-service

# Install helm repos for different databases
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
# helm install postgresql --set postgresqlPassword=password bitnami/postgresql
helm install cassandra --set dbUser.password=password bitnami/cassandra

echo "{BLUE}Waiting for db to startup"
# Sleep long enough for db to start, typically between 20-30s but we use 40 to be sure
sleep 40
                                                                                                                  
# Setting up postgres client to be used as a stepstone to connect app to the db
# kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default \
#     --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" \
#     --command -- psql --host postgresql -U postgres -d postgres -p 5432 \
#     -c "create database order_service"

# TODO: deploy apps for all services, rename file since all deployments use the same config
kubectl apply -f order-service/k8s/deployment.yaml