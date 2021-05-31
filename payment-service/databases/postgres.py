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

        psycopg2.extras.register_uuid(self.connection)
        LOGGER.info("Instantiating table payment-service")

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                                user_id uuid PRIMARY KEY,
                                credit NUMERIC(10,2)
                                );
                CREATE TABLE IF NOT EXISTS payments (
                                order_id uuid,
                                status NUMBER(1),
                                amount NUMERIC(10,2),
                                CONSTRAINT ck_testbool_ischk CHECK (status IN (1,0))
                                );
                            """
                            )

    def create_user(self):
        """Create a new entry in the users database with 0 credit"""

        user_id = uuid4()  # TODO?: check whether user_id already exists in database
        self.cursor.execute("""INSERT INTO users (user_id, credit)
                            VALUES (%s, float(0))
                            """, (user_id,)
                            )

        return user_id

    def find_user(self, user_id):
        """Find user by ID in users database"""

        query_result = self.cursor.execute("""SELECT credit FROM users
                            WHERE user_id = %s""", (user_id,))

        result = query_result.fetchone()

        if result is None:
            return False, None
        else:
            return True, result[0]

    def subtract_credit(self, user_id, amount):
        """Subtract amount from user if credit is high enough"""

        query_result = self.cursor.execute("""SELECT credit FROM users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        credit = query_result.fetchone

        if credit is None:
            return False

        new_credit = credit - amount

        if new_credit < 0:
            return False
        else:
            self.cursor.execute("""UPDATE users
                        SET credit = %s 
                        WHERE user_id = %s 
                        IF credit = %s
                        """, (new_credit, user_id, credit))
            return True

    def add_credit(self, user_id, amount):
        """Add given amount to given users credit"""

        query_result = self.cursor.execute("""SELECT credit FROM users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        credit = query_result.fetchone

        if credit is None:
            return False

        new_credit = credit + amount

        self.cursor.execute("""UPDATE users
                        SET credit = %s 
                        WHERE user_id = %s 
                        IF credit = %s
                        """, (new_credit, user_id, credit))
        return True

    def add_payment(self, order_id, paid, amount):
        """Enter new payment into payments database"""

        self.cursor.execute("""INSERT INTO payments (order_id, status, amount)
                    VALUES(%s, %s, %s)
                    """, (order_id, paid, amount))

    def cancel_payment(self, order_id):
        """Change status of payment to unpaid (0)"""

        query_result = self.cursor.execute("""SELECT amount FROM payments
                            WHERE order_id = %s
                            """, (order_id,))

        amount = query_result.fetchone()

        if amount is None:
            return False, amount

        self.cursor.execute("""UPDATE payments
                        SET status = 0
                        WHERE order_id = %s
                        IF amount = %s
                        """, (order_id, amount))

        return True, amount

    def get_status(self, order_id):
        """Find payment status (0/1) for specific order ID"""

        query_result = self.cursor.execute("""SELECT status FROM payments
                            WHERE order_id = %s
                            """, (order_id,))

        status = query_result.fetchone()

        if status is None:
            return False, None
        else:
            return True, status
