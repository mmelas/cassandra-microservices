#!/bin/bash

set -e
BLUE='\033[1;34m'
CLOSE='\033[0m'
RED='\033[1;31m'

if ! command -v minikube &> /dev/null; then
    echo -e ""$RED"minikube not installed. Exiting."$CLOSE""
    exit 1
elif ! command -v kubectl &> /dev/null; then
    echo -e ""$RED"kubectl not installed. Exiting."$CLOSE""
    exit 1a
elif ! command -v helm &> /dev/null; then
    echo -e ""$RED"helm not installed. Exiting."$CLOSE""
    exit 1
fi

usage(){
    printf "$0 Flags:\n\t-d: Type of database to use (cassandra | postgres)\n" 
    exit 0
}

[ $# -ne 2 ] && usage
DB="None"
while getopts "d:h" opt; do
    case ${opt} in
        d)
            DB=${OPTARG}
            ;; 
        h | *)
            usage
            exit 0
            ;;
    esac
done

case "$DB" in
    "cassandra"|"postgres")
        ;;
    *)
        usage
        ;;
esac

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

if [[ "$DB" == "postgres" ]]; then
    helm install postgresql --set postgresqlPassword=password bitnami/postgresql
elif [[ "$DB" == "cassandra" ]]; then
    helm install cassandra --set dbUser.password=password bitnami/cassandra
fi

echo -e ""$BLUE"Waiting for db to startup"$CLOSE""
# Sleep long enough for db to start, typically between 20-30s but we use 40 to be sure
sleep 40

# TODO: deploy apps for all services
# Setting up postgres client to be used as a stepstone to connect app to the db
if [[ "$DB" == "postgres" ]]; then
    kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" --command -- psql --host postgresql -U postgres -d postgres -p 5432 -c "create database order_service"
    kubectl apply -f order-service/k8s/deployment-postgres.yaml
else
    kubectl apply -f order-service/k8s/deployment-cassandra.yaml
fi