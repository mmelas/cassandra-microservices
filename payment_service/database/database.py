import abc


class DatabaseException(Exception):
    pass


class Database(object):
    """Generic Database object, every different database connection should
    implement these functions."""
    __metaclass__ = abc.ABCMeta

    DATABASE: str
    connection: any

    @abc.abstractmethod
    def connect(self, config, setup):
        pass

    @abc.abstractmethod
    def retrieve_version(self):
        pass

    @abc.abstractmethod
    def get_payment(self, order_id):
        pass

    @abc.abstractmethod
    def insert_payment(self, order_id, payment_status, amount):
        pass

    @abc.abstractmethod
    def set_payment_status(self, order_id, payment_status):
        pass

    @abc.abstractmethod
    def create_user(self):
        pass

    @abc.abstractmethod
    def subtract_user_credit(self, user_id, amount):
        pass

    @abc.abstractmethod
    def add_user_credit(self, user_id, order_amount):
        pass

    @abc.abstractmethod
    def get_user(self, user_id):
        pass
