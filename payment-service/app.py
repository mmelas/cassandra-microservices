from flask import Flask
from cassandra.cluster import Cluster

app = Flask(__name__)

# TODO: Dummy app for now. replace with real microservices
@app.route('/')
def hello_world():
    return 'Hello, World!'


def cassandra_test():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()


if __name__ == "__main__":
    app.run(host='0.0.0.0')
    cassandra_test()
