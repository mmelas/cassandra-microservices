import psycopg2
import psycopg2.extras
import logging
from uuid import uuid4, UUID
import os

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)


class PostgresDatabase():
    """Postgres database class instance"""
    connection = cursor = None

    def __init__(self):
        LOGGER.info("Connecting to postgres")
        self.connection = psycopg2.connect(host="postgresql",
                                           user="postgres",
                                           port=5432,
                                           database="order_service",
                                           password="password")
        self.connection.autocommit = True

        self.cursor = self.connection.cursor()

        # load hstore extension into current database
        self.cursor.execute("""CREATE EXTENSION IF NOT EXISTS hstore;""")

        psycopg2.extras.register_hstore(self.connection)
        psycopg2.extras.register_uuid(self.connection)
        LOGGER.info("Instantiating table order-service")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
                                orderid uuid PRIMARY KEY,
                                userid uuid,
                                items hstore
                                )
                            """
                            )

    def put(self, orderid: UUID, userid: UUID):
        """Insert an order with an orderid and a userid into the database."""

        # TODO: have to gen order id since we don't provide a way to get table size
        self.cursor.execute("""INSERT INTO orders (orderid, userid)
                               VALUES (%s, %s)
                            """, (orderid, userid)
                            )

    def get(self, orderid: UUID):
        """Retrieve information of an order with orderid from the database"""

        self.cursor.execute("""SELECT * FROM orders 
                                WHERE orderid = %s
                                """, (orderid,)
                            )

        order = self.cursor.fetchone()
        return {
            'order_id': order[0],
            'user_id': order[1],
            # ? Maybe have to loop over items to convert map to json? also maybe don't always need the items so might be better to only do this when we need it.
            'items': order[2]
        } if order != None else None

    def update(self, orderid: UUID, itemid: UUID):
        """Add items to an existing order"""

        # TODO: Replace with a dict inside this class to skip this get for performance
        order = self.get(orderid)
        if order is None:
            return 404

        if order['items'] == None:
            self.cursor.execute("""UPDATE orders
                                   SET items = hstore(%s::text, 1::text) 
                                   WHERE orderid = %s
                                   """, (itemid, orderid))
        elif str(itemid) in order['items']:
            self.cursor.execute("""UPDATE orders
                                    SET items = items || hstore(%s::text, %s::text)
                                    WHERE orderid = %s
                                    """, (itemid, int(order['items'][str(itemid)]) + 1, orderid))
        else:
            self.cursor.execute("""UPDATE orders
                                   SET items = items || hstore(%s::text, 1::text) 
                                   WHERE orderid = %s
                                   """, (itemid, orderid))

    def remove_item(self, orderid: UUID, itemid: UUID):
        """Remove item with itemid from an order with orderid"""

        # if order does not exist or item does not exit 404 error
        order = self.get(orderid)
        if order is None or order['items'] is None or str(itemid) not in order['items']:
            return 404

        # if item amount is 1 remove it
        if order['items'][str(itemid)] == '1':
            self.cursor.execute("""UPDATE orders
                                    SET items = delete(items, %s::text)
                                    WHERE orderid = %s
                                    """, (itemid, orderid)
                                )
        else:
            # if order and item exists and item amount is > 1 decrement it by 1
            self.cursor.execute("""UPDATE orders
                                    SET items = items || hstore(%s::text, %s::text)
                                    WHERE orderid = %s
                                    """, (itemid, int(order['items'][str(itemid)]) - 1, orderid))

    def find_order(self, orderid: UUID):
        """Retrieve information of order with orderid"""

        order_info = {}
        order = self.get(orderid)
        order_info['items'] = [{}]

        if order is None:
            return 404

        order_info['order_id'] = order['order_id']
        order_info['user_id'] = order['user_id']
        items = order['items']

        if order['items'] is not None:
            for item in items:
                LOGGER.info("log item: " + item)
                amount = order['items'][item]
                order_info['items'][0][item] = amount

        return order_info

    def delete(self, orderid: UUID):
        """Delete an order from the database"""

        # TODO: Replace with a dict inside this class to skip this get for performance
        order = self.get(orderid)
        if order is None:
            return 404
        self.cursor.execute("""DELETE FROM orders
                                WHERE orderid = %s
                            """, (orderid,)
                            )
