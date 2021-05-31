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
    connection = cursor = None

    def __init__(self):

        # Setup the Cluster on localhost and connect to it (TODO: likely will need to pass ip in k8s later on ...)
        LOGGER.info("Connecting to postgres")
        # * Weird but specifying different port did not work, so changed docker port, but have to fix this!
        self.connection = psycopg2.connect(host="localhost",
                                           user="postgres",
                                           port=9042,
                                           password="password")
        self.connection.autocommit = True

        self.cursor = self.connection.cursor()

        # load hstore extension into current database
        self.cursor.execute("""CREATE EXTENSION IF NOT EXISTS hstore;""")

        psycopg2.extras.register_hstore(self.connection)
        psycopg2.extras.register_uuid(self.connection)
        LOGGER.info("Instantiating table stock-service")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS stock (
                                itemid uuid,
                                price NUMERIC(10,2) NOT NULL,
                                quantity int DEFAULT 0 CHECK (quantity>=0),
                                PRIMARY KEY (itemid)   
                                )"""
                            )

    def create_item(self, itemid: UUID, price: float):
        """Create an item with price"""

        self.cursor.execute("""INSERT INTO stock (itemid,price,quantity)
                                VALUES (%s,%s,1)
                                """, (itemid, price)
                                )


    def get(self, itemid: UUID):
        """Retrieve information of the number of a specific item with itemid from the database"""

        self.cursor.execute("""SELECT price,quantity FROM stock
                                        WHERE itemid = %s
                                        """, (itemid,)
                                        )
        item = self.cursor.fetchone()
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
            self.cursor.execute("""UPDATE stock
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
                self.cursor.execute("""UPDATE stock
                                        SET quantity = quantity - %s
                                        WHERE itemid = %s
                                        """, ( number, itemid))


