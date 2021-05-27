from flask import Flask, jsonify
from databases.cassandra import CassandraDatabase
import logging

# TEMP
from uuid import uuid4, UUID


LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)
app = Flask("order-service")

# TODO: Check if actually should use uuid (check in thier client what they provide)
@app.route('/orders/create/<uuid:userid>', methods=['POST'])
def create_order(userid: UUID):
    orderid = uuid4()
    LOGGER.info("Creating orderid %s", orderid)
    try:
        database.put(orderid, userid)
        return jsonify({'order_id': str(orderid)}), 201
    except:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/remove/<uuid:orderid>', methods=['DELETE'])
def remove_order(orderid: UUID):
    LOGGER.info("Removing orderid %s", orderid)
    try:
        if database.delete(orderid, itemid) is not 400:
            return jsonify({'message': 'success'}), 200
        else:
            return jsonify({'message': 'non-existent orderid'}), 400
    except:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/add_item/<uuid:orderid>/<uuid:itemid>', methods=['POST'])
def add_item(orderid: UUID, itemid: UUID):
    LOGGER.info("Adding item %s to orderid %s", itemid, orderid)
    try:
        if database.update(orderid, itemid) is not 400:
            return jsonify({'message': 'success'}), 201
        else:
            return jsonify({'message': 'non-existent orderid'}), 400
    except:
        return jsonify({'message': 'failure'}), 500


@app.route('/orders/remove_item/<uuid:orderid>/<uuid:itemid>', methods=['DELETE'])
def remove_item(orderid: UUID, itemid: UUID):
    LOGGER.info("Removing item %s from orderid %s", itemid, orderid)
    try:
        if database.remove_item(orderid, itemid) is not 400:
            return jsonify({'message': 'success'}), 200
        else:
            return jsonify({'message': 'non-existent orderid/itemid'}), 400
    except:
        return jsonify({'message': 'failure'}), 500


if __name__ == "__main__":
    database = CassandraDatabase()
    orderID = uuid4()
    userID = uuid4()
    database.put(orderID, userID)
    print("should have added empty order ", database.get(orderID))
    itemid = uuid4()
    database.update(orderID, itemid)
    print("should be 1 item ", database.get(orderID))
    itemid = uuid4()
    database.update(orderID, itemid)
    print("Should be two items ", database.get(orderID))
    database.update(orderID, itemid)
    print("Should be two items with second one amount = 2 ", database.get(orderID))
    database.delete(orderID)
    print("Should be gone lol ", database.get(orderID))
    app.run(host='0.0.0.0')
