from flask import Flask
from databases.cassandra import CassandraDatabase

app = Flask("order-service")

# TODO: Dummy app for now. replace with real microservices
@app.route('/')
def hello_world():
    return 'Hello, World!'


if __name__ == "__main__":
    database = CassandraDatabase()
    app.run(host='0.0.0.0')