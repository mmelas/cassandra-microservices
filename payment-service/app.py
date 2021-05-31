import logging
from http import HTTPStatus

from flask import Flask, jsonify
from databases.cassandra import CassandraDatabase
from databases.postgres import PostgresDatabase

LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)
app = Flask("payment-service")


@app.route('/payment/pay/<uuid:user_id>/<uuid:order_id>/<float:amount>', methods=['POST'])
def pay_order(user_id, order_id, amount):
    LOGGER.info("Trying to pay order %s", order_id)
    try:
        success = database.subtract_credit(user_id, amount)
        if success:
            database.add_payment(order_id, 1, amount)
            return HTTPStatus.OK
        else:
            database.add_payment(order_id, 0, amount)
            return jsonify({'message': 'not enough credit'}), HTTPStatus.BAD_REQUEST
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


@app.route('/payment/cancel/<uuid:user_id>/<uuid:order_id>', methods=['POST'])
def cancel_payment(user_id, order_id):
    LOGGER.info("Canceling payment for %s by %s", (order_id, user_id))
    try:
        success_cancel, amount = database.cancel_payment(order_id)
        if success_cancel:
            success_add = database.add_credit(user_id, amount)
            if success_add:
                return HTTPStatus.OK
            else:
                return jsonify({'message': 'User not found'}), HTTPStatus.BAD_REQUEST
        return jsonify({'message': 'Payment not found'}), HTTPStatus.BAD_REQUEST
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


@app.route('/payment/status/<uuid:order_id>', methods=['GET'])
def get_status(order_id):
    LOGGER.info("Getting status of payment for order %s", order_id)
    try:
        success, status = database.get_status(order_id)
        if not success:
            return jsonify({'message': 'Payment not found'}), HTTPStatus.BAD_REQUEST
        else:
            if status == 1:
                return jsonify({'paid': True}), HTTPStatus.OK
            elif status == 0:
                return jsonify({'paid': False}), HTTPStatus.OK
            else:
                return jsonify({'message': 'Invalid status'}), HTTPStatus.BAD_REQUEST
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


@app.route('/payment/add_funds/<uuid:user_id>/<float:amount>', methods=['POST'])
def add_funds(user_id, amount):
    LOGGER.info("Adding %s to credit for user %s", (amount, user_id))
    try:
        success = database.add_credit(user_id, amount)
        if success:
            return jsonify({'done': True}), HTTPStatus.OK
        else:
            return jsonify({'done': False}), HTTPStatus.BAD_REQUEST
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


@app.route('/payment/create_user', methods=['POST'])
def create_user():
    LOGGER.info("Creating new user")
    try:
        user_id = database.create_user()
        return jsonify({'user_id': user_id}), HTTPStatus.OK
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


@app.route('/payment/find_user/<uuid:user_id>', methods=['GET'])
def find_user(user_id):
    LOGGER.info("Trying to find user %s", user_id)
    try:
        success, credit = database.find_user(user_id)
        if success:
            return jsonify({'user_id': user_id, 'credit': credit}), HTTPStatus.OK
        else:
            return jsonify({'message': 'user not found'}), HTTPStatus.BAD_REQUEST
    except RuntimeError:
        return jsonify({'message': 'failure'}), HTTPStatus.BAD_REQUEST


if __name__ == "__main__":
    database = PostgresDatabase()
