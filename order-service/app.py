from flask import Flask, jsonify
from databases.cassandra import CassandraDatabase
from databases.postgres import PostgresDatabase
import logging
from uuid import uuid4, UUID
import os
import requests


LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)
app = Flask("order-service")


@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'check success'}), 200


@app.route('/orders/create/<uuid:userid>', methods=['POST'])
def create_order(userid: UUID):
    orderid = uuid4()
    LOGGER.info("Creating orderid %s", orderid)
    try:
        database.put(orderid, userid)
        return jsonify({'order_id': str(orderid)}), 201
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/remove/<uuid:orderid>', methods=['DELETE'])
def remove_order(orderid: UUID):
    LOGGER.info("Removing orderid %s", orderid)
    try:
        if database.delete(orderid) != 404:
            return jsonify({'message': 'success'}), 200
        else:
            return jsonify({'message': 'non-existent orderid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/addItem/<uuid:orderid>/<uuid:itemid>', methods=['POST'])
def add_item(orderid: UUID, itemid: UUID):
    LOGGER.info("Adding item %s to orderid %s", itemid, orderid)
    try:
        if database.update(orderid, itemid) != 404:
            return jsonify({'message': 'success'}), 201
        else:
            return jsonify({'message': 'non-existent orderid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/removeItem/<uuid:orderid>/<uuid:itemid>', methods=['DELETE'])
def remove_item(orderid: UUID, itemid: UUID):
    LOGGER.info("Removing item %s from orderid %s", itemid, orderid)
    try:
        if database.remove_item(orderid, itemid) != 404:
            return jsonify({'message': 'success'}), 200
        else:
            return jsonify({'message': 'non-existent orderid/itemid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/find/<uuid:orderid>', methods=['GET'])
def find_order(orderid: UUID):
    LOGGER.info("Finding information for orderid %s", orderid)
    try:
        # improves the performance in benchmarks
        order = database.find_order(orderid)
        if order == 404:
            return jsonify({'message': 'non-existent orderid'}), 404
        total_cost = 0
        items = order['items'][0]
        for item, amount in items.items():
            stock_item = requests.get(f"{STOCK_SERVICE_URL}/stock/find/{item}")
            total_cost += int(amount) * float(stock_item.json()['price'])
        order['total_cost'] = total_cost
        paid = requests.get(
            f"{PAYMENT_SERVICE_URL}/payment/status/{orderid}")
        if paid.status_code == 404:
            order['paid'] = False
        elif paid.status_code == 200:
            order['paid'] = True
        if order != 404:
            return order, 200
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/checkout/<uuid:orderid>', methods=['POST'])
def checkout(orderid: UUID):
    LOGGER.info("Checking out orderid %s", orderid)
    order_result, order_code = find_order(orderid)

    if order_code == 404:
        return jsonify({'message': 'non-existent orderid'}), 404
    if order_code == 500:
        return jsonify({'message': 'failure'}), 400

    if order_code == 200 and not order_result['paid']:
        # make payment
        payment = requests.post(
            f"{PAYMENT_SERVICE_URL}/payment/pay/{order_result['user_id']}/{orderid}/{order_result['total_cost']}")
        LOGGER.info(payment.status_code)
        if payment.status_code == 200:
            stock = requests.post(
                f"{STOCK_SERVICE_URL}/stock/subtract/multiple", json=order_result['items'][0])
            if stock.status_code == 201:
                return jsonify({'message': 'success'}), 200
            else:
                payment = requests.post(
                    f"{PAYMENT_SERVICE_URL}/payment/cancel/{order_result['user_id']}/{orderid}")
                if payment.status_code != 200:
                    LOGGER.error(
                        f'Canceling of payment with order id {orderid} failed')
                return jsonify({'message': 'Stock subtraction failed'}), 400
        else:
            return jsonify({'message': 'Payment failed'}), 400
    else:
        return jsonify({'message': 'Order already paid'}), 400


if __name__ == "__main__":
    DB = os.environ["DB"]
    database = CassandraDatabase() if DB == "cassandra" else PostgresDatabase()

    PAYMENT_SERVICE_URL = os.environ["PAYMENT_SERVICE"]
    STOCK_SERVICE_URL = os.environ["STOCK_SERVICE"]
    app.run(host='0.0.0.0')
