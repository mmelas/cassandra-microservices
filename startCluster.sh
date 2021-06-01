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

# Setup minikube
minikube start
eval $(minikube docker-env)
minikube addons enable ingress

# docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order ./order-service

# minikube cleaup before start
kubectl delete --all pods --namespace=default &
kubectl delete --all services --namespace=default &
kubectl delete --all deployments --namespace=default &

# Install helm repos for different databases
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm install postgresql --set postgresqlPassword=password bitnami/postgresql
# helm install cassandra --set dbUser.password=password bitnami/cassandra

echo "Waiting for db to startup"
sleep 10

# TODO error with password when reinstalling (after helm uninstall postgresql and restarting this)
# Setting up postgres client
kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" --command -- psql --host postgresql -U postgres -d postgres -p 5432 -c "create database order_service" # can then add -c "create payment-service" etc.

#* NOTES:
# To run a cassandra pod that you can use as a client:
#   kubectl run --namespace default cassandra-client --rm --tty -i --restart='Never' \ --env CASSANDRA_PASSWORD=$CASSANDRA_PASSWORD --image docker.io/bitnami/cassandra:3.11.10-debian-10-r108 -- bash

# To connect to your databse from outside the cluster:
#   kubectl port-forward --namespace default svc/cassandra 9042:9042 & cqlsh -u cassandra -p $CASSANDRA_PASSWORD 127.0.0.1 9042

# kubectl apply -f order-service/k8s/order-service-cassandra.yaml
# TODO: build all containers for all microservices and start minikube with the right configs