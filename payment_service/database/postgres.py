import psycopg2
import uuid
from database.database import Database, DatabaseException


# This file connects to the postgres database, it should expose the same
# functions as the other database models (db_cassandra.py).

class PostgresDB(Database):
    DATABASE = "POSTGRES"
    connection = None

    def connect(self, config, setup):
        connection_config = config['connection']
        self.connection = psycopg2.connect(host=connection_config["host"],
                                           user=connection_config["user"],
                                           database=connection_config["database"],
                                           password=connection_config["password"])
        # TODO: Add specific connection code, if needed.
        self.connection.autocommit = True
        if setup:
            self.__setup_database(config)

    def __get_cursor(self):
        """Retrieve a new cursor for the connection."""
        return self.connection.cursor()

    def __setup_database(self, config):
        cur = self.__get_cursor()
        cur.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typename = 'payment_status') THEN
                CREATE TYPE payment_status AS ENUM ('paid', 'failed', 'cancelled', 'refunded');
                CREATE TABLE IF NOT EXISTS order_payment_status (
                    order_id uuid,
                    status payment_status, 
                    amount integer
                );
                CREATE TABLE IF NOT EXISTS user_credit (
                    user_id uuid
                    credit integer
                );
            END IF;
        END$$
        """)

    def get_payment(self, order_id):
        """Retrieve the payment status of an order"""

        try:
            with self.__get_cursor() as cur:
                cur.execute("""SELECT status, amount FROM order_payment_status
                WHERE orderid = %s""", (order_id,))
                if cur.rowcount == 0:
                    return None, None
                result = cur.fetchone()
                return result[0], result[1]
        except Exception as e:
            raise DatabaseException(e)

    def insert_payment(self, order_id, payment_status, amount):
        try:
            with self.__get_cursor() as cur:
                cur.execute("""
                    INSERT INTO order_payment_status (order_id, status, amount) 
                    VALUES (%s, %s, %s);
                    """, (order_id, payment_status, amount))
        except Exception as e:
            raise DatabaseException(e)

    def set_payment_status(self, order_id, payment_status):
        try:
            with self.__get_cursor() as cur:
                cur.execute("""
                    UPDATE order_payment_status 
                    SET status = %s
                    WHERE order_id = %s
                """, (payment_status, order_id))
        except Exception as e:
            raise DatabaseException(e)

    def create_user(self):
        try:
            user_id = uuid.uuid4()
            with self.__get_cursor() as cur:
                cur.execute("""
                INSERT INTO user_credit (user_id, credit)
                VALUES(%s, 0)                
                """, (user_id, ))
                return str(user_id)
        except Exception as e:
            raise DatabaseException(e)

    def subtract_user_credit(self, user_id, amount):
        try:
            with self.__get_cursor() as cur:
                user = cur.execute("""
                SELECT credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
                if user is None:
                    #User not found
                    return False
                current_credit = user.credit
                if amount > current_credit:
                    #Insufficient funds
                    return False
                new_credit = current_credit - amount
                cur.execute("""
                UPDATE user_credit
                SET credit = %s
                WHERE user_id = %s
                IF credit = %s
                """, (new_credit, user_id, current_credit))
                return True
        except Exception as e:
            raise DatabaseException(e)

    def add_user_credit(self, user_id, order_amount):
        try:
            with self.__get_cursor() as cur:
                user = cur.execute("""
                SELECT credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
                if user is None:
                    #User not found
                    return False
                new_credit = user.credit + order_amount
                cur.execute("""
                UPDATE user_credit
                SET credit = %s
                WHERE user_id = %s
                IF credit = %s
                """, (new_credit, user_id, user.credit))
                return True
        except Exception as e:
            raise DatabaseException(e)

    def get_user(self, user_id):
        try:
            with self.__get_cursor() as cur:
                result = cur.execute("""
                SELECT user_id, credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
                if user is None:
                    #User not found
                    return None, None
                return result[0], result[1]
        except Exception as e:
            raise DatabaseException(e)
