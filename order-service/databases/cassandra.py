import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from uuid import uuid4, UUID
from cassandra.util import OrderedMapSerializedKey

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "microservices"


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = session = None
    orders = {}

    def __init__(self):
        """Constructor connects to cluster and creates tables"""

        # Setup the Cluster on localhost and connect to it (TODO: likely will need to pass ip in k8s later on ...)
        self.cluster = Cluster(['127.0.0.1'], port=9042, protocol_version=3)
        LOGGER.info("Connecting to cluster")
        self.session = self.cluster.connect()
        LOGGER.info("Connected to cluster")

        LOGGER.info("Setting up keyspace: %s" % KEYSPACE)
        self.session.execute("""CREATE KEYSPACE IF NOT EXISTS %s
                                WITH replication = { 'class': 'SimpleStrategy',
                                'replication_factor': '1' }
                                """ % KEYSPACE
                             )

        self.session.set_keyspace(KEYSPACE)

        LOGGER.info("Instantiating table order-service")
        self.session.execute("""CREATE TABLE IF NOT EXISTS orders (
                                orderid uuid,
                                userid uuid,
                                items map<uuid, int>,
                                PRIMARY KEY(orderid)
                                )"""
                             )

    def put(self, orderid: UUID, userid: UUID):
        """Insert an order with an orderid and a userid into the database."""

        # TODO: have to gen order id since we don't provide a way to get table size
        self.session.execute("""INSERT INTO microservices.orders (orderid, userid) 
                                VALUES (%s, %s)
                                """, (orderid, userid)
                             )

    def get(self, orderid: UUID):
        """Retrieve information of an order with orderid from the database"""

        order = self.session.execute("""SELECT * FROM microservices.orders 
                                        WHERE orderid = %s
                                        """ % orderid
                                     )

        return {
            'order_id': order.one()[0],
            'user_id': order.one()[2],
            # ? Maybe have to loop over items to convert map to json? also maybe don't always need the items so might be better to only do this when we need it.
            'items': order.one()[1]
        } if order.one() != None else None

    def update(self, orderid: UUID, itemid: UUID):
        """Add items to an existing order"""

        # TODO: Replace with a dict inside this class to skip this get for performance
        order = self.get(orderid)
        if order is None:
            return 404
        if (order['items'] != None and (itemid in order['items'])):
            self.session.execute("""UPDATE microservices.orders
                                    SET items[%s] = %s
                                    WHERE orderid = %s
                                    """, (itemid, order['items'][itemid] + 1, orderid))
        else:
            self.session.execute("""UPDATE microservices.orders
                                   SET items[%s] = 1
                                   WHERE orderid = %s
                                   """, (itemid, orderid))


    def remove_item(self, orderid: UUID, itemid: UUID):
        """Remove item with itemid from an order with orderid"""

        # if order does not exist or item does not exit 404 error
        order = self.get(orderid)
        print(order)
        if order is None or order['items'] is None or itemid not in order['items']:
            return 404

        # if item amount is 1 remove it
        if order['items'][itemid] == 1:
            query = self.session.execute("""DELETE items[%s] FROM microservices.orders 
                                            WHERE orderid = %s
                                            """, (itemid, orderid)
                                         )
        else:
            # if order and item exists and item amount is > 1 decrement it by 1
            self.session.execute("""UPDATE microservices.orders
                                    SET items[%s] = %s
                                    WHERE orderid = %s
                                    """, (itemid, order['items'][itemid], orderid))


    def find_order(self, orderid: UUID):
        """Retrieve information of order with orderid"""

        order_info = {}
        order_info['items'] = []
        order = self.get(orderid)

        if order is None:
            return 404

        # TODO: add params: paid, total_cost (get from payment service)
        items = order['items']
        order_info['order_id'] = order['order_id']
        order_info['user_id'] = order['user_id']

        if order['items'] is not None:
            for item in items:
                LOGGER.info("log item: " + str(item))
                order_info['items'].append(item)

        return order_info

    def delete(self, orderid: UUID):
        """Delete an order from the database"""

        # TODO: Replace with a dict inside this class to skip this get for performance
        order = self.get(orderid)
        if order is None:
            return 404
        self.session.execute("""DELETE FROM microservices.orders 
                                        WHERE orderid = %s
                                        """ % orderid
                             )
