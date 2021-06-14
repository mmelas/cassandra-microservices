import logging
from xmlrpc.client import boolean

from cassandra.cqlengine.columns import Decimal

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import DCAwareRoundRobinPolicy
from uuid import uuid4, UUID

LOGGER = logging.getLogger()
LOGGER.disable('ERROR')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)

KEYSPACE = "payament_service"


class CassandraDatabase():
    """Cassandra database class instance"""
    cluster = connection = None

    def __init__(self):
        """Constructor connects to cluster and creates tables"""

        auth = PlainTextAuthProvider(username="cassandra", password="password")

        # Setup the Cluster on localhost and connect to it
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

        LOGGER.info("Instantiating tables payment-service")
        self.connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                                user_id uuid,
                                credit decimal,
                                PRIMARY KEY (user_id)
                                )""")
        self.connection.execute("""        
                CREATE TABLE IF NOT EXISTS payments (
                                order_id uuid,
                                status boolean,
                                amount decimal,
                                PRIMARY KEY (order_id)
                                )"""
                                )

    def create_user(self):
        """Create a new entry in the users database with 0 credit"""

        user_id = uuid4()
        self.connection.execute("""INSERT INTO payament_service.users (user_id, credit)
                                   VALUES (%s, 0.00)
                                """, (user_id, ))

        return user_id

    def find_user(self, user_id: UUID):
        """Find user by ID in users database"""

        query_result = self.connection.execute("""SELECT credit 
                                                  FROM payament_service.users
                                                  WHERE user_id = %s
                                               """, (user_id,))

        result = query_result.one()

        if result is None:
            return False, None
        else:
            return True, result[0]

    def subtract_credit(self, user_id: UUID, amount: Decimal):
        """Subtract amount from user if credit is high enough"""

        query_result = self.connection.execute("""SELECT credit 
                                                  FROM payament_service.users 
                                                  WHERE user_id = %s
                                               """, (user_id,))

        credit = query_result.one()

        if credit is None:
            return False

        new_credit = credit[0] - amount

        if new_credit < 0:
            return False
        else:
            self.connection.execute("""UPDATE payament_service.users
                                       SET credit = %s 
                                       WHERE user_id = %s 
                                    """, (new_credit, user_id))
            return True

    def add_credit(self, user_id: UUID, amount: Decimal):
        """Add given amount to given users credit"""

        query_result = self.connection.execute("""SELECT credit 
                                                  FROM payament_service.users 
                                                  WHERE user_id = %s
                                               """, (user_id,))

        credit = query_result.one()

        if credit is None:
            return False

        new_credit = credit[0] + amount

        self.connection.execute("""UPDATE payament_service.users
                                   SET credit = %s 
                                   WHERE user_id = %s 
                                """, (new_credit, user_id))
        return True

    def add_payment(self, order_id: UUID, paid: boolean, amount: Decimal):
        """Enter new payment into payments database"""

        self.connection.execute("""INSERT INTO payament_service.payments (order_id, status, amount)
                                   VALUES(%s, %s, %s)
                                """, (order_id, paid, amount))

    def cancel_payment(self, order_id: UUID):
        """Change status of payment to unpaid (0)"""

        query_result = self.connection.execute("""SELECT amount 
                                                  FROM payament_service.payments
                                                  WHERE order_id = %s
                                               """, (order_id,))

        amount = query_result.one()

        if amount is None:
            return False, amount

        self.connection.execute("""UPDATE payament_service.payments
                                   SET status = false
                                   WHERE order_id = %s
                                """, (order_id,))

        return True, amount

    def get_status(self, order_id: UUID):
        """Find payment status (0/1) for specific order ID"""

        query_result = self.connection.execute("""SELECT status FROM payament_service.payments
                                                  WHERE order_id = %s
                                               """, (order_id,))

        status = query_result.one()

        if status is None:
            return False, None
        else:
            return True, status[0]
