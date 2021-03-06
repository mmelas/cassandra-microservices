import psycopg2
import psycopg2.extras
import logging
from uuid import uuid4, UUID

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)


class PostgresDatabase():
    """Postgres database class instance"""
    connection = None

    def __init__(self):

        # Setup the Cluster on localhost and connect to it
        LOGGER.info("Connecting to postgres")
        self.connection = psycopg2.connect(host="postgresql",
                                           user="postgres",
                                           port=5432,
                                           database="stock_service",
                                           password="password")
        self.connection.autocommit = True

        psycopg2.extras.register_uuid(self.connection)
        LOGGER.info("Instantiating table stock-service")

        with self.connection, self.__cursor__() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS stock (
                                    itemid uuid,
                                    price NUMERIC(10,2) NOT NULL,
                                    quantity int DEFAULT 0 CHECK (quantity>=0),
                                    PRIMARY KEY (itemid)   
                                    )"""
                           )

    def __cursor__(self):
        """Get a new database cursor"""

        return self.connection.cursor()

    def create_item(self, itemid: UUID, price: float):
        """Create an item with price"""

        with self.connection, self.__cursor__() as cursor:
            cursor.execute("""INSERT INTO stock (itemid,price,quantity)
                                    VALUES (%s,%s,1)
                                    """, (itemid, price)
                           )

    def get(self, itemid: UUID):
        """Retrieve information of the number of a specific item with itemid from the database"""

        with self.connection, self.__cursor__() as cursor:
            cursor.execute("""SELECT price,quantity FROM stock
                                            WHERE itemid = %s
                                            """, (itemid,)
                           )
            item = cursor.fetchone()

        return {
            'stock': item[1],
            'price': item[0],
        } if item != None else None

    def add_item(self, itemid: UUID, number: int):
        """Add items to the stock"""
        item = self.get(itemid)
        if item is None:
            return 404
        else:
            with self.connection, self.__cursor__() as cursor:
                cursor.execute("""UPDATE stock
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
                with self.connection, self.__cursor__() as cursor:
                    cursor.execute("""UPDATE stock
                                            SET quantity = quantity - %s
                                            WHERE itemid = %s
                                            """, (number, itemid))

    def subtract_multiple(self, items: dict):
        try:
            tuples = list(map(lambda x: (items[x], x), items.keys()))
            query = "UPDATE stock SET quantity = quantity - %s WHERE itemid = %s"
            with self.connection, self.__cursor__() as cursor:
                psycopg2.extras.execute_batch(cursor, query, tuples)
            return 201
        except Exception:
            return 404

    def get_all(self):
        with self.connection, self.__cursor__() as cursor:
            cursor.execute("""SELECT * FROM stock""")
            result = cursor.fetchall()
        return list(map(lambda x: [x[0], float(x[1]), x[2]], result))
