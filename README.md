# cassandra-microservices

## Deploying on local k8s with minikbue

In order to deploy the services on local k8s setup with minikube, required packages are:

- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [helm](https://helm.sh/)

Then the entire cluster can be started as (**Note:** only run this script **ONCE** in the beginning, as it does not clean up or reset. Can only rerun it if you delete the complete cluster.)

```bash
# With database being cassandra || postgres and -b for building images (takes longer) or pulling images from Dockerhub when flag not specified
./startCluster.sh -d <database> [-b]

# for example for deploying cassandra with pulled images:
./startCluster.sh -d cassandra
```

The script will start minikube with all required extensions enabled, set the minikube deamon to take over the docker deamon, then either pulls images from dockerhub or builds images for the service, depending on the specified `-b` flag. Next it installs helm packages for the databases (cassandra & postgres), and initializes the database. The setting up of the database can take several seconds, therefore the script waits until all deployed pods are ready this, and then starts a database client, which is used by the application to connect to the database. Lastly, the pods for the application and the services exposing it in the cluster are deployed. **Note**, we run locally so there is no need for the ingress for exposing services outside the cluster.

For deploying locally with minikube, make sure that all the pods and services deployed correctly by running

```bash
minikube dashboard

# OR
kubectl get <pods,service,ingress,etc.>
```

### Startup Script Troubleshooting

#### Postgres Client timeout

Sometimes the script fails due to a timeout for the postgres client, in that case the script will exit due to the failure without having deployed the pods.
In order to deploy the pods manually run,

```bash
kubectl apply -f order-service/k8s/deployment-postgres.yaml
kubectl apply -f payment-service/k8s/deployment-postgres.yaml
kubectl apply -f stock-service/k8s/deployment-postgres.yaml
```

### Submitting queries with k8s

In order to submit queries we need to get the endpoint (IP:Port) of the service that exposes the application.
This can be done by running

```bash
minikube service <service>
```

which will open the service in a browser, and the link can be copied (or taken from the terminal). Paste this link into Postman to submit
queries for the microservice. You can stop the service by CTRL-c in the terminal, but by doing that you can no longer have access to the service.

Or if running with an ingress when deployed on cloud (Note local deployment in minikube does not need ingress as it does not expose ports for external
access)

```bash
kubectl get ingress
```

and just copy the IP address with port 80 (which was configured in the .yaml config).

## Deploying on Google Cloud

For deploying on Google Cloud, there first needs to be a cluster. Create a cluster in Standard mode with preferably nodes close to the location of the requests. Next, activate the google cloud shell, initialize the project with, and deploy k8s as follows

```bash
# Set the project config
gcloud config set project wdm-cassandra

gcloud container clusters get-credentials <cluster_name>

# clone the repo
git clone https://github.com/mmelas/cassandra-microservices
cd cassandra-microservices

# Install helm repos for different databases
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install the corresponding database, for cassandra:
helm install cassandra --set dbUser.password=password bitnami/cassandra

# For postgress (it also needs to start the client):
helm install postgresql --set postgresqlPassword=password bitnami/postgresql --set postgresqlExtendedConf.max_files_per_process=100
kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 \
        --env="PGPASSWORD=password" --command -- psql --host postgresql -U postgres -d postgres -p 5432 -c "create database order_service" \
        -c "create database payment_service" -c "create database stock_service"

# start the services, deploy the pods, etc. (Change the <database> to cassandra or postgres)
kubectl apply -f order-service/k8s/deployment-<database>.yaml
kubectl apply -f payment-service/k8s/deployment-<database>.yaml
kubectl apply -f stock-service/k8s/deployment-<database>.yaml

# Setup the kong ingress, proxy, and webhook
kubectl create -f https://bit.ly/k4k8s

# Ensure it has started (can take a couple minutes)
kubectl -n kong get service kong-proxy # wait for the external-IP to show up

# Deploy the service ingress over the kong ingress
kubectl apply -f k8s/order-ingress.yaml
kubectl apply -f k8s/stock-ingress.yaml
kubectl apply -f k8s/payment-ingress.yaml
```

This is using the [kong ingress controller](https://github.com/Kong/kubernetes-ingress-controller) for kubernetes that handles external 
load balancing, provide validation webhooks, and use a proxy for forwarding requests to the correct services. The service ingress are then deployed
separately and connect to the kong ingress to receive their correct requests.

## Developing the microservices (without k8s)

- Need to start a database container [link](#starting-database-container), run either cassandra or postgres and specify in the app which one
- Run the app as a python application (without docker, since it's quicker for developing)
- For testing use [Postman](https://www.postman.com/) to submit http request with the corresponding links, and check return codes and results

build the docker image for the respective microservice folder
(replace service with the service you want to test)

**Note** you need to change the ip addresses of the database connection (in postgres.py and cassandra.py for all respective services) to localhost and run the application (in app.py set `app.run(host=127.0.0.1` and add ports 5000-5002 for the services), also change the urls for the services in the services so they can communicate with each other, and lastly hardcode a database to start in the app.py, or export an env var for the DB.

```bash
# adjust build concurrency in the dockerfile to what your system can handle
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:<service> ./<service>
```

make sure it built

```bash
docker image ls
```

run the image

```bash
docker run -p 5000:5000 nicktehrany/wdm-cassandra-microservices:<service>
```

### Starting database container

#### Cassandra

For starting up cassandra container

```bash
# Do once to pull cassandra from docker hu
docker pull cassandra:3.11.10

# Start the downloaded cassandra image
docker run -d --name microservices-cassandra -p 127.0.0.1:9042:9042 cassandra:3.11.10

# [CAN SKIP] To check docker exec for the db (run queries from cmd line)
docker exec -it microservices-cassandra cqlsh

# Then run the app.py of the ordering service [USE THIS FOR DEVELOPING]
python3 app.py

# [NOT RECOMMENDED FOR DEVELOPING] OR run using docker image of app (this takes longe since also need to build image)
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:<service> ./<service>
docker run --net="host" nicktehrany/wdm-cassandra-microservices:<service>
```

#### Postgres

For postgres container
**REQUIRES postgres to be installed on OS, linux it's libpq-dev package**

```bash
# Do once to pull postgres from docker hub
docker pull postgres:11.12

# Start the downloaded postgres image
docker run --name microservices-postgres -e POSTGRES_PASSWORD=password -p 127.0.0.1:5432:5432 postgres:11.12

# To check docker exec for the db (run queries from cmd line, username is "postgres")
docker exec -it microservices-postgres psql -U postgres

# Then run the app.py of the ordering service [USE THIS FOR DEVELOPING]
python3 app.py

# [NOT RECOMMENDED FOR DEVELOPING] OR run using docker image of app (this takes longe since also need to build image)
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:<service> ./<service>
docker run --net="host" nicktehrany/wdm-cassandra-microservices:<service>
```

### Troubleshooting

#### Exiting due to MK_USAGE: Due to networking limitations of driver docker on darwin, ingress addon is not supported'

This is caused due to network limiting the docker deamon, to fix it just replace the `minikube start` in the `startCluster.sh` script with
`minikube start --vm=true`

#### 'psql: could not connect to server: Connection refused'

The above script (startCluster.sh) may show an error 'psql: could not connect to server: Connection refused'.
You can ignore this, since the postgres-client probably has not finished setting up the pod yet. Just wait for a minute or so and
then manually deploy the postgres client and then deploy the services with

```bash
# deploy the postgres client
kubectl run postgresql-client --rm --tty -i --restart='Never' --namespace default \
    --image docker.io/bitnami/postgresql:11.12.0-debian-10-r13 --env="PGPASSWORD=password" \
    --command -- psql --host postgresql -U postgres -d postgres -p 5432 \
    -c "create database order_service"

# deploy the services for *ALL* corresponding services and provide the db to run (cassandra || postgres)
kubectl apply -f <service>/k8s/deployment-<database>.yaml
```

#### Manually deploying k8s configurations

Since the script can only be used once to bootstrap the k8s setup, to deploy additional configurations on k8s can be done by running

```bash
# Make sure you are in the minikube env
eval $(minikube docker-env)

kubectl apply -f <PATH-TO-CONFIG.yaml>
```

#### Getting logs

##### Getting container logs from docker

For debugging it can be helpful to get logs from the different containers running on k8s. This can be done by running

```bash
# Make sure you are in the minikube env
eval $(minikube docker-env)

# list all running containers
docker ps

# get the logs for a container
docker logs -tf <container-id>
```

##### Getting logs from k8s

Additionally, it can help for debugging to get the k8s logs of running pods/services/etc. by running

```bash
# get the name of the k8s pods (replace with others, e.g. service)
kubectl get pods

kubectl logs -f <pod-name>
```

#### Cassandra Error: 'pod has unbound immediate PersistentVolumeClaims.'

This is caused by the storage for the stateful set not having been deployed yet. Typically you can just wait a couple of
minutes for this to go up and once it is up all other services should restart and be successfully deployed. You can watch
the status of this by checking the cassandra logs, as explained previously, on the cassandra pod.

#### Deleting deployments of k8s

```bash
# Type can be deployment (or pods/service/etc.) and name can be found with 'kubectl get <type>'
kubectl delete -n default <type> <name>
```

#### Complete minikube reset

If all fails for unknown reasons (happens a lot), you can always fully delete the entire cluster and restart everything
(this does take some time, especially restarting)

```bash
minikube delete
```
