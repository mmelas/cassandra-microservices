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
        # Setup the Cluster on localhost and connect to it
        LOGGER.info("Connecting to postgres")

        self.connection = psycopg2.connect(host="postgresql",
                                           user="postgres",
                                           port=5432,
                                           database="order_service",
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
                                status BOOLEAN,
                                amount NUMERIC(10,2)
                                );
                            """
                            )

    def create_user(self):
        """Create a new entry in the users database with 0 credit"""

        user_id = uuid4()
        self.cursor.execute("""INSERT INTO users (user_id, credit)
                            VALUES (%s, %s)
                            """, (user_id, float(0))
                            )

        return user_id

    def find_user(self, user_id):
        """Find user by ID in users database"""

        self.cursor.execute("""SELECT credit FROM users
                            WHERE user_id = %s""", (user_id,))

        result = self.cursor.fetchone()

        if result is None:
            return False, None
        else:
            return True, result[0]

    def subtract_credit(self, user_id, amount):
        """Subtract amount from user if credit is high enough"""

        self.cursor.execute("""SELECT credit FROM users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        result = self.cursor.fetchone()

        if result is None:
            return False

        credit = result[0]

        new_credit = credit - amount

        if new_credit < 0:
            return False
        else:
            self.cursor.execute("""UPDATE users
                        SET credit = %s 
                        WHERE user_id = %s 
                        """, (new_credit, user_id))
            return True

    def add_credit(self, user_id, amount):
        """Add given amount to given users credit"""

        self.cursor.execute("""SELECT credit FROM users 
                                    WHERE user_id = %s
                                    """, (user_id,))

        result = self.cursor.fetchone()

        if result is None:
            return False

        credit = result[0]
        new_credit = credit + amount

        self.cursor.execute("""UPDATE users
                        SET credit = %s 
                        WHERE user_id = %s 
                        """, (new_credit, user_id))
        return True

    def add_payment(self, order_id, paid, amount):
        """Enter new payment into payments database"""

        self.cursor.execute("""INSERT INTO payments (order_id, status, amount)
                    VALUES(%s, %s, %s)
                    """, (order_id, paid, amount))

    def cancel_payment(self, order_id):
        """Change status of payment to unpaid"""

        self.cursor.execute("""SELECT amount FROM payments
                            WHERE order_id = %s
                            """, (order_id,))

        amount = self.cursor.fetchone()

        if amount is not None:
            self.cursor.execute("""UPDATE payments
                        SET status = false
                        WHERE order_id = %s
                        """, (order_id,))

            return True, amount
        else:
            return False, amount

    def get_status(self, order_id):
        """Find payment status for specific order ID"""

        self.cursor.execute("""SELECT status FROM payments
                            WHERE order_id = %s
                            """, (order_id,))

        status = self.cursor.fetchone()

        if status is None:
            return False, None
        else:
            return True, status