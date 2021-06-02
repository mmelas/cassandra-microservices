import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine.columns import Decimal
from cassandra.policies import DCAwareRoundRobinPolicy
from uuid import uuid4, UUID

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "microservices"

# TODO: check if we can use async in some queries


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = connection = None

    def __init__(self):
        """Constructor connects to cluster and creates tables"""
        
        auth = PlainTextAuthProvider(username="cassandra", password="password")
        
        self.cluster = Cluster(['cassandra'], port=9042, protocol_version=3, auth_provider=auth)
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

        LOGGER.info("Instantiating table stock-service")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS stock (
                                   itemid uuid,
                                   price decimal,
                                   PRIMARY KEY (itemid))
                                """
                                )
        self.connection.execute("""CREATE TABLE IF NOT EXISTS stock_counts (
                                itemid uuid,
                                quantity counter,
                                PRIMARY KEY (itemid))
                                """
                                )



    def create_item(self, itemid: UUID, price: Decimal):
        """Create an item with price"""
        self.connection.execute("""INSERT INTO microservices.stock (itemid,price)
                                   VALUES (%s,%s)
                                """, (itemid, price)
                                )
        self.connection.execute("""UPDATE microservices.stock_counts 
                                   SET quantity = quantity + 1
                                   WHERE itemid = %s
                                """ % itemid
                                )


    def get(self, itemid: UUID):
        """Retrieve information of the number of a specific item with itemid from the database"""

        item = self.connection.execute("""SELECT price FROM microservices.stock
                                          WHERE itemid = %s;
                                       """ % itemid
                                       )

        item_counts = self.connection.execute("""SELECT quantity FROM microservices.stock_counts
                                                 WHERE itemid = %s;
                                              """ % itemid
                                              )
        return {
            'stock': item_counts.one()[0],
            'price': item.one()[0],
        } if item.one() != None else None



    def add_item(self, itemid: UUID, number: int):
        """Add items to the stock"""
        item = self.get(itemid)
        if item is None:
            return 404
        else:
            self.connection.execute("""UPDATE microservices.stock_counts
                                       SET quantity = quantity + %s
                                       WHERE itemid = %s
                                    """, ( number, itemid))


    def subtract_item(self, itemid: UUID, number: int):
        """Subtract items from the stock"""
        item = self.get(itemid)

        if item is None:
            return 404
        else:
            if(item['stock'] < number):
                LOGGER.info("input number is larger than the stock!")
                return 400
            else:
                self.connection.execute("""UPDATE microservices.stock_counts
                                           SET quantity = quantity - %s
                                           WHERE itemid = %s
                                        """, ( number, itemid))


