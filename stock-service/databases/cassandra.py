import logging
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine.columns import Decimal
from cassandra.query import BatchStatement, SimpleStatement, BatchType
from cassandra.cqltypes import CounterColumnType
from cassandra.query import dict_factory
from uuid import uuid4, UUID

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "stock_service"


# TODO: check if we can use async in some queries


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = connection = None

    def __init__(self):
        """Constructor connects to cluster and creates tables"""

        auth = PlainTextAuthProvider(username="cassandra", password="password")

        self.cluster = Cluster(['127.0.0.1'], port=9042,
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
        self.connection.execute("""INSERT INTO stock_service.stock (itemid,price)
                                   VALUES (%s,%s)
                                """, (itemid, price)
                                )
        self.connection.execute("""UPDATE stock_service.stock_counts 
                                   SET quantity = quantity + 1
                                   WHERE itemid = %s
                                """ % itemid
                                )

    def get(self, itemid: UUID):
        """Retrieve information of the number of a specific item with itemid from the database"""

        item = self.connection.execute("""SELECT price FROM stock_service.stock
                                          WHERE itemid = %s;
                                       """ % itemid
                                       )

        item_counts = self.connection.execute("""SELECT quantity FROM stock_service.stock_counts
                                                 WHERE itemid = %s;
                                              """ % itemid
                                              )
        return {
            'stock': item_counts.one()[0],
            'price': item.one()[0],
        } if item.one() != None else None

    def get_all(self):
        item_counts = self.connection.execute(SimpleStatement("SELECT itemid FROM stock_service.stock"))
        return item_counts.all()

    def get_ids(self, ids):
        query = '''
        SELECT * 
        FROM stock_service.stock_counts
        WHERE itemid IN ({}) 
        ALLOW FILTERING'''.format(','.join('%s' for _ in ids))
        uuids = tuple(map(lambda x: UUID(x), ids))
        results = self.connection.execute(query, uuids).all()
        resultsDict = {}
        for result in results:
            resultsDict[str(result[0])] = result[1]
        return resultsDict

    def add_item(self, itemid: UUID, number: int):
        """Add items to the stock"""
        item = self.get(itemid)
        if item is None:
            return 404
        else:
            self.connection.execute("""UPDATE stock_service.stock_counts
                                       SET quantity = quantity + %s
                                       WHERE itemid = %s
                                    """, (number, itemid))

    def subtract_item(self, itemid: UUID, number: int):
        """Subtract items from the stock"""
        item = self.get(itemid)

        if item is None:
            return 404
        else:
            if (item['stock'] < number):
                LOGGER.info("input number is larger than the stock!")
                return 400
            else:
                self.connection.execute("""UPDATE stock_service.stock_counts
                                           SET quantity = quantity - %s
                                           WHERE itemid = %s
                                        """, (number, itemid))

    def subtract_multiple(self, items: dict):
        update_statement = "UPDATE stock_service.stock_counts SET quantity = quantity - %s  WHERE itemid = %s"
        idWithQuanties = self.get_ids(list(items.keys()))

        batch = BatchStatement(retry_policy=0, consistency_level=9, serial_consistency_level=1,
                               batch_type=BatchType.COUNTER)
        for item in items.keys():
            if item not in idWithQuanties or idWithQuanties[item] - int(items[item]) < 0:
                return 400
            uuid = UUID(item)
            batch.add(SimpleStatement(update_statement), (int(items[item]), uuid))

        try:
            self.connection.execute(batch)
            return 201
        except Exception as e:
            return 400
