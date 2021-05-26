import uuid

from cassandra.auth import PlainTextAuthProvider
from cassandra.cluster import Cluster, Session
from database.database import Database, DatabaseException


# This file connects to the cassandra database, it should expose the same
# functions as the other database models (db_postgres.py).

class CassandraDB(Database):
    DATABASE = "CASSANDRA"
    connection: Session = None

    def connect(self, config, setup=False):
        connection_config = config['connection']
        auth_provider = PlainTextAuthProvider(username=connection_config['user'],
                                              password=connection_config['password']) \
            if 'user' in connection_config else None
        cluster = Cluster(auth_provider=auth_provider)
        self.connection = cluster.connect()
        # TODO: Add specific connection code, if needed.
        if setup:
            self.__setup_database(connection_config)
        self.connection.set_keyspace(connection_config['database'])

    def __setup_database(self, config):
        # Create the keyspace
        self.connection.execute(f'''
        CREATE KEYSPACE {config['database']} with replication = {{
            'class':'SimpleStrategy','replication_factor':1
        }};
        ''')
        self.connection.set_keyspace(config['database'])
        self.connection.execute(f''''
        CREATE TABLE IF NOT EXISTS order_payment_status (
            order_id uuid PRIMARY KEY,
            status varchar,
            amount int
        );
        CREATE TABLE IF NOT EXISTS user_credit (
            user_id uuid PRIMARY KEY,
            credit int
        );
        ''')

    def get_payment(self, order_id):
        try:
            results = self.connection.execute('''
                SELECT status, amount FROM order_payment_status
                WHERE order_id = %s
                ''', (order_id,))
            row = results.one()
            if row is None:
                return None, None
            else:
                return row.status, row.amount
        except Exception as e:
            raise DatabaseException(e)

    def insert_payment(self, order_id, payment_status, amount):
        try:
            self.connection.execute('''
            INSERT INTO order_payment_status (order_id, status, amount)
            VALUES (%s, %s, %s); 
            ''', (order_id, payment_status, amount))
        except Exception as e:
            raise DatabaseException(e)

    def set_payment_status(self, order_id, payment_status):
        try:
            self.connection.execute('''
            UPDATE order_payment_status
            SET status = %s
            WHERE order_id = %s;
            ''', (payment_status, order_id))
        except Exception as e:
            raise DatabaseException(e)

    def create_user(self):
        try:
            user_id = uuid.uuid4()
            self.connection.execute('''
                INSERT INTO user_credit (user_id, credit)
                VALUES(%s, 0)                
            ''', (user_id,))
            return str(user_id)
        except Exception as e:
            raise DatabaseException(e)

    def subtract_user_credit(self, user_id, amount):
        try:
            user = self.connection.execute("""
                SELECT credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
            if user is None:
                # Credit not found
                return False
            current_credit = user.credit
            if amount > current_credit:
                # Insufficient funds
                return False
            new_credit = current_credit - amount
            self.connection.execute("""
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
            user = self.connection.execute("""
                SELECT credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
            if user is None:
                # Credit not found
                return False
            new_credit = user.credit + order_amount
            self.connection.execute("""
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
            result = self.connection.execute("""
                SELECT user_id, credit FROM user_credit
                WHERE user_id = %s;
                """, (user_id,)).one()
            if result is None:
                # Credit not found
                return None, None
            return result[0], result[1]
        except Exception as e:
            raise DatabaseException(e)
