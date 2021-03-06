import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from uuid import uuid4, UUID

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "order_service"


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = connection = None

    def __init__(self):
        """Constructor connects to cluster and creates tables"""

        auth = PlainTextAuthProvider(username="cassandra", password="password")

        self.cluster = Cluster(['cassandra'], port=9042,
                               protocol_version=3, auth_provider=auth)
        LOGGER.info("Connecting to cluster")
        self.connection = self.cluster.connect()
        LOGGER.info("Connected to cluster")

        LOGGER.info("Setting up keyspace: %s" % KEYSPACE)
        self.connection.execute("""CREATE KEYSPACE IF NOT EXISTS %s
                                WITH replication = { 'class': 'SimpleStrategy',
                                'replication_factor': '1' }
                                """ % KEYSPACE
                                )

        self.connection.set_keyspace(KEYSPACE)

        LOGGER.info("Instantiating table order_service")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS orders (
                                orderid uuid,
                                userid uuid,
                                items map<uuid, int>,
                                PRIMARY KEY(orderid)
                                )"""
                                )

    def put(self, orderid: UUID, userid: UUID):
        """Insert an order with an orderid and a userid into the database."""

        self.connection.execute("""INSERT INTO order_service.orders (orderid, userid) 
                                VALUES (%s, %s)
                                """, (orderid, userid)
                                )

    def get(self, orderid: UUID):
        """Retrieve information of an order with orderid from the database"""

        order = self.connection.execute("""SELECT * FROM order_service.orders 
                                        WHERE orderid = %s
                                        """ % orderid
                                        )

        return {
            'order_id': order.one()[0],
            'user_id': order.one()[2],
            'items': order.one()[1]
        } if order.one() != None else None

    def update(self, orderid: UUID, itemid: UUID):
        """Add items to an existing order"""

        order = self.get(orderid)
        if order is None:
            return 404
        if (order['items'] != None and (itemid in order['items'])):
            self.connection.execute("""UPDATE order_service.orders
                                    SET items[%s] = %s
                                    WHERE orderid = %s
                                    """, (itemid, order['items'][itemid] + 1, orderid))
        else:
            self.connection.execute("""UPDATE order_service.orders
                                   SET items[%s] = 1
                                   WHERE orderid = %s
                                   """, (itemid, orderid))

    def remove_item(self, orderid: UUID, itemid: UUID):
        """Remove item with itemid from an order with orderid"""

        # if order does not exist or item does not exit 404 error
        order = self.get(orderid)

        if order is None or order['items'] is None or itemid not in order['items']:
            return 404

        # if item amount is 1 remove it
        if order['items'][itemid] == 1:
            self.connection.execute("""DELETE items[%s] FROM order_service.orders 
                                            WHERE orderid = %s
                                            """, (itemid, orderid)
                                    )
        else:
            # if order and item exists and item amount is > 1 decrement it by 1
            self.connection.execute("""UPDATE order_service.orders
                                    SET items[%s] = %s
                                    WHERE orderid = %s
                                    """, (itemid, order['items'][itemid] - 1, orderid))

    def find_order(self, orderid: UUID):
        """Retrieve information of order with orderid"""

        order_info = {}
        order = self.get(orderid)
        order_info['items'] = [{}]

        if order is None:
            return 404

        order_info['order_id'] = str(order['order_id'])
        order_info['user_id'] = str(order['user_id'])
        items = order['items']

        if order['items'] is not None:
            for item in items:
                LOGGER.info("log item: " + str(item))
                amount = order['items'][item]
                order_info['items'][0][str(item)] = amount

        return order_info

    def delete(self, orderid: UUID):
        """Delete an order from the database"""

        order = self.get(orderid)
        if order is None:
            return 404
        self.connection.execute("""DELETE FROM order_service.orders 
                                        WHERE orderid = %s
                                        """ % orderid
                                )
