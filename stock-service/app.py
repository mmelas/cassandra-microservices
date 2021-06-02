import simplejson
from cassandra.cqlengine.columns import Decimal
from flask import Flask, jsonify
from databases.cassandra import CassandraDatabase
from databases.postgres import PostgresDatabase
import logging
from uuid import uuid4, UUID


LOGGER = logging.getLogger()
LOGGER.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
LOGGER.addHandler(handler)
app = Flask("stock-service")


# http://192.168.3.13:5000/stock/item/create/1.0
@app.route('/stock/item/create/<float:price>', methods=['POST'])
def create_item(price: Decimal):
    itemid = uuid4()
    LOGGER.info("Creating itemid %s", itemid)
    try:
        database.create_item(itemid, price)
        return jsonify({'item_id': str(itemid)}), 201
    except RuntimeError:
        return jsonify({'message': 'failure'}), 400

# http://192.168.3.13:5000/stock/add/c2b08f54-112e-4481-a83f-c6aa01c05efa/1
@app.route('/stock/add/<uuid:itemid>/<int:number>', methods=['POST'])
def add_item(itemid: UUID, number: int):
    LOGGER.info("Adding %s item %s", number, itemid)
    try:
        if database.add_item(itemid, number) != 404:
            return jsonify({'message': 'success'}), 201
        else:
            return jsonify({'message': 'non-existent itemid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 400

# http://192.168.3.13:5000/stock/find/c2b08f54-112e-4481-a83f-c6aa01c05efa
@app.route('/stock/find/<uuid:itemid>', methods=['GET'])
def find_item(itemid: UUID):
    LOGGER.info("Finding information for itemid %s", itemid)
    try:
        item = database.get(itemid)
        if item != 404:
            item['price'] = simplejson.dumps(item['price'])
            return item, 200
        else:
            return jsonify({'message': 'non-existent itemid'}), 404
    except RuntimeError:
        return jsonify({'message': 'failure'}), 400


# http://192.168.3.13:5000/stock/subtract/c2b08f54-112e-4481-a83f-c6aa01c05efa/1
@app.route('/stock/subtract/<uuid:itemid>/<int:number>', methods=['POST'])
def subtract_item(itemid: UUID, number: int):
    LOGGER.info("Adding item %s to stock %s", number, itemid)
    try:
        response = database.subtract_item(itemid, number)
        if response == 404:
            return jsonify({'message': 'non-existent itemid'}), 404
        elif response == 400:
            return jsonify({'message': 'input number is larger than the stock!'}), 400
        else:
            return jsonify({'message': 'success'}), 201
    except RuntimeError:
        return jsonify({'message': 'failure'}), 400

if __name__ == "__main__":
    DB = os.environ["DB"]
    database = CassandraDatabase() if DB == "cassandra" else PostgresDatabase()
    app.run(host='0.0.0.0')
