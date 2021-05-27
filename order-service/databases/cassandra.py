import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "microservices"

# TODO:
#   - implement startup of cassandra db
#   - connect to the cassandra db instance (not sure if it requires some user/password? we'll see)
#   - create a table for the order service
#   - provide basic functions to query the database (get, put, and update)

# ? Possible performance improvmenent: add a total price to the order id so we don't have to recalculate everytime we access it

# Cassandra database instance with constructor to setup the cluster, connection, and tables


class CassandraDatabase():
    cluster = session = None

    def __init__(self):

        # Setup the Cluster on localhost and connect to it (TODO: likely will need to pass ip in k8s later on ...)
        self.cluster = Cluster(['127.0.0.1'], port=9042, protocol_version=3)
        LOGGER.info("Connecting to cluster")
        self.session = self.cluster.connect()
        LOGGER.info("Connected to cluster")

        LOGGER.info("Setting up keyspace: %s" % KEYSPACE)
        self.session.execute("""CREATE KEYSPACE IF NOT EXISTS %s
                           WITH replication = { 'class': 'SimpleStrategy',
                           'replication_factor': '1' }
                        """ % KEYSPACE)

        self.session.set_keyspace(KEYSPACE)

        LOGGER.info("Instantiating table order-service")
        self.session.execute("""CREATE TABLE IF NOT EXISTS orders (
                           orderID uuid,
                           userID uuid,
                           items map<uuid, int>,
                           PRIMARY KEY(orderID)
                           )
                        """)

# create another terminal and try to rerun app? (cqlsh seems to work so the node is running)cros

    # def put(self, order_id, user_id, item_id):
    #     self.session.execute()

    # TODO: def put(): put an item into the db

    # TODO: def get(): get an item

    # TODO: def update(): update an existing item

    # TODO: def delete(): delete an item

    # Table design:

    # what we need: order-id, user-id, (item, number),

    # # TODO: Maybe add TotalPrice for each item? (possible payment performance improvement)
    #     pk         pk
    # | order id | user id     | Map{(Item, amount)...}    |
    # | oid_1    | uid_1       | {(banana, 2), (apple, 4)} |
    # | ...      | ...         | ...                       |
