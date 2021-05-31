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

KEYSPACE = "microservices"


# TODO: check if we can use async in some queries


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = connection = None

    def __init__(self):
        """Constructor connects to cluster and creates tables"""

        # Setup the Cluster on localhost and connect to it (TODO: likely will need to pass ip in k8s later on ...)
        self.cluster = Cluster(['127.0.0.1'], port=9042, protocol_version=3)
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

        LOGGER.info("Instantiating tables payment-service")
        self.connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                                user_id uuid,
                                credit decimal
                                PRIMARY KEY(user_id)
                                );
                CREATE TABLE IF NOT EXISTS payments (
                                order_id uuid,
                                status NUMBER(1),
                                amount decimal,
                                CONSTRAINT ck_testbool_ischk CHECK (status IN (1,0))
                                );"""
                                )

    def create_user(self):
        """Create a new entry in the users database with 0 credit"""

        user_id = uuid4()  # TODO?: check whether uuid already in database
        self.connection.execute("""INSERT INTO microservices.users (user_id, credit)
                            VALUES (%s, decimal(0))
                            """, (user_id,))

        return user_id

    def find_user(self, user_id):
        """Find user by ID in users database"""

        query_result = self.connection.execute("""SELECT credit FROM microservices.users
                            WHERE user_id = %s""", (user_id,))

        result = query_result.fetchone()

        if result is None:
            return False, None
        else:
            return True, result[0]

    def subtract_credit(self, user_id, amount):
        """Subtract amount from user if credit is high enough"""

        query_result = self.connection.execute("""SELECT credit FROM microservices.users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        credit = query_result.fetchone

        if credit is None:
            return False

        new_credit = credit - amount

        if new_credit < 0:
            return False
        else:
            self.connection.execute("""UPDATE microservices.users
                        SET credit = %s 
                        WHERE user_id = %s 
                        IF credit = %s
                        """, (new_credit, user_id, credit))
            return True

    def add_credit(self, user_id, amount):
        """Add given amount to given users credit"""

        query_result = self.connection.execute("""SELECT credit FROM microservices.users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        credit = query_result.fetchone

        if credit is None:
            return False

        new_credit = credit + amount

        self.connection.execute("""UPDATE microservices.users
                        SET credit = %s 
                        WHERE user_id = %s 
                        IF credit = %s
                        """, (new_credit, user_id, credit))
        return True

    def add_payment(self, order_id, paid, amount):
        """Enter new payment into payments database"""

        self.connection.execute("""INSERT INTO microservices.payments (order_id, status, amount)
                    VALUES(%s, %s, %s)
                    """, (order_id, paid, amount))

    def cancel_payment(self, order_id):
        """Change status of payment to unpaid (0)"""

        query_result = self.connection.execute("""SELECT amount FROM microservices.payments
                            WHERE order_id = %s
                            """, (order_id,))

        amount = query_result.fetchone()

        if amount is None:
            return False, amount

        self.connection.execute("""UPDATE microservices.payments
                        SET status = 0
                        WHERE order_id = %s
                        IF amount = %s
                        """, (order_id, amount))

        return True, amount

    def get_status(self, order_id):
        """Find payment status (0/1) for specific order ID"""

        query_result = self.connection.execute("""SELECT status FROM microservices.payments
                            WHERE order_id = %s
                            """, (order_id,))

        status = query_result.fetchone()

        if status is None:
            return False, None
        else:
            return True, status
