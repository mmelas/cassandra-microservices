# cassandra-microservices

## For deploying the microservices

**!THOROUGHLY TEST YOUR CODE, ALL CASES, ALL ERRORS, ALL POSSIBLE ERROR CODES!**

Base your development on the stock service, can mostly copy paste the databases, only change the tables and functions to what is needed for your service.

- Need to start a database container [link](#starting-database-container), run either cassandra or postgres and specify in the app which one
- Run the app as a python application (without docker, since it's quicker for developing)
- For testing use [Postman](https://www.postman.com/) to submit http request with the corresponding links, and check return codes and results


some notes for now..

build the docker image for the respective microservice folder

```bash
# adjust build concurrency in the dockerfile to what your system can handle
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

to unset the minikube deamons (detach them from the docker deamon)

```bash
eval $(minikube docker-env -u)
```


### Temp for stock service

```bash
# adjust build concurrency in the dockerfile to what your system can handle
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:stock ./stock-service
docker run -p 5000:5000 nicktehrany/wdm-cassandra-microservices:stock
```

#### Starting Database container

For starting up cassandra container

```bash
# Do once to pull cassandra from docker hu
docker pull cassandra:3.11.10

# Start the downloaded cassandra image
docker run -d --name microservices-cassandra -p 127.0.0.1:9042:9042 cassandra:3.11.10

# [CAN SKIP] To check docker exec for the db (run queries from cmd line)
docker exec -it microservices-cassandra cqlsh

# Then run the app.py of the stocking service [USE THIS FOR DEVELOPING]
python3 app.py

# [NOT RECOMMENDED FOR DEVELOPING] OR run using docker image of app (this takes longe since also need to build image)
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:stock ./stock-service
docker run --net="host" nicktehrany/wdm-cassandra-microservices:stock
```

For postgres container
**REQUIRES postgres to be installed on OS, linux it's libpq-dev package**

```bash
# Do once to pull postgres from docker hub
docker pull postgres:11.12

# Start the downloaded postgres image
docker run --name microservices-postgres -e POSTGRES_PASSWORD=password -p 127.0.0.1:9042:5432 postgres:11.12 

# To check docker exec for the db (run queries from cmd line, username is "postgres")
docker exec -it microservices-postgres psql -U postgres

# Then run the app.py of the stocking service [USE THIS FOR DEVELOPING]
python3 app.py

# [NOT RECOMMENDED FOR DEVELOPING] OR run using docker image of app (this takes longe since also need to build image)
docker build -f Dockerfile -t nicktehrany/wdm-cassandra-microservices:stock ./stock-service
docker run --net="host" nicktehrany/wdm-cassandra-microservices:stock
```