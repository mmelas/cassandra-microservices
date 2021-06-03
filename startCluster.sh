#!/bin/bash

set -e
BLUE='\033[1;34m'
CLOSE='\033[0m'
RED='\033[1;31m'
GREEN=$'\033[1;32m'

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

check_db_ready() {
    regex="\"$1-*\""
    VALUES="$(kubectl get pods | awk '{if($1 ~ '$regex') print $0}' | awk '{print $2}' | grep -oP '\d+')"
    READY=$(echo $VALUES | cut -f1 -d ' ')
    DEPLOYED=$(echo $VALUES | cut -f2 -d ' ')
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
minikube start --cpus=4
eval $(minikube docker-env)
minikube addons enable ingress

docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:order-service ./order-service
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:payment-service ./payment-service
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:stock-service ./stock-service

# Install helm repos for different databases
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

if [[ "$DB" == "postgres" ]]; then
    helm install postgresql --set postgresqlPassword=password bitnami/postgresql
elif [[ "$DB" == "cassandra" ]]; then
    helm install cassandra --set dbUser.password=password bitnami/cassandra
fi

# Check if databases are ready
check_db_ready $DB

# TODO: deploy apps for all services
# Setting up postgres client to be used as a stepstone to connect app to the db
if [[ "$DB" == "postgres" ]]; then
    while [ $READY -ne $DEPLOYED ]; do
        echo -e ""$BLUE"Waiting for postgres to startup"$CLOSE""
        sleep 5
        check_db_ready $DB
    done
    echo -e ""$GREEN"Cassandrda pod is ready!"$CLOSE""
    kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" --command -- psql --host postgresql -U postgres -d postgres -p 5432 -c "create database order_service" -c "create database payment_service" -c "create database stock_service"
    kubectl apply -f order-service/k8s/deployment-postgres.yaml
    kubectl apply -f payment-service-service/k8s/deployment-postgres.yaml
    kubectl apply -f stock-service/k8s/deployment-postgres.yaml
else
    while [ $READY -ne $DEPLOYED ]; do
        echo -e ""$BLUE"Waiting for cassandra to startup"$CLOSE""
        sleep 5
        check_db_ready $DB
    done
    echo -e ""$GREEN"Postgres pod is ready!"$CLOSE""
    kubectl apply -f order-service/k8s/deployment-cassandra.yaml
    kubectl apply -f payment-service/k8s/deployment-cassandra.yaml
    kubectl apply -f stock-service/k8s/deployment-cassandra.yaml
fi