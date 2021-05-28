from flask import Flask, jsonify
from databases.cassandra import CassandraDatabase
import logging
from uuid import uuid4, UUID


LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)
app = Flask("order-service")


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


@app.route('/orders/add_item/<uuid:orderid>/<uuid:itemid>', methods=['POST'])
def add_item(orderid: UUID, itemid: UUID):
    LOGGER.info("Adding item %s to orderid %s", itemid, orderid)
    try:
        if database.update(orderid, itemid) != 404:
            return jsonify({'message': 'success'}), 201
        else:
            return jsonify({'message': 'non-existent orderid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/remove_item/<uuid:orderid>/<uuid:itemid>', methods=['DELETE'])
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
    LOGGER.info("Finding items from orderid %s", orderid)
    try:
        if database.find_items(orderid) is not 400:
            return jsonify({'message': 'success'}), 200
        else:
            return jsonify({'message': 'non-existent orderid/itemid'}), 400
    except:
        return jsonify({'message': 'failure'}), 500


if __name__ == "__main__":
    # TODO: check for type of db (cassandra or postgres) then use according one
    database = CassandraDatabase()
    app.run(host='0.0.0.0')
