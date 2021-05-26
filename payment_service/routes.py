from http import HTTPStatus

from flask import Flask, jsonify
from database.database import Database, DatabaseException


# This is the main file of the service, handling with the different routes
# the microservice exposes.


# The db variable here can be either 'db_postgres.py' or 'db_cassandra.py'
# based on the config given to the application.
def create_app(db: Database):
    service = Flask(__name__)

    @service.route('/health')
    def health():
        return jsonify({"status": "ok", "database": db.DATABASE})

    @service.route('/pay/<uuid:user_id>/<uuid:order_id>/<int:amount>', methods=["POST"])
    def execute_payment(user_id, order_id, amount):
        order_status = db.get_payment(order_id)
        if order_status == "paid":
            return HTTPStatus.OK
        else:
            try:
                db.insert_payment(order_id, "paid", amount)
                sub_credit = db.subtract_user_credit(user_id, amount)
                if sub_credit:
                    return HTTPStatus.CREATED
                else:
                    return HTTPStatus.BAD_REQUEST
            except DatabaseException:
                # Paid status could not be stored
                return HTTPStatus.BAD_REQUEST

    @service.route('/cancel/<uuid:user_id>/<uuid:order_id>', methods=["POST"])
    def cancel_payment(user_id, order_id):
        order_status, order_amount = db.get_payment(order_id)
        if not order_status == "paid":
            return HTTPStatus.BAD_REQUEST
        else:
            try:
                db.set_payment_status(order_id, "cancelled")
                db.add_user_credit(user_id, order_amount)
                return HTTPStatus.OK
            except DatabaseException:
                return HTTPStatus.BAD_REQUEST

    @service.route('/status/<uuid:order_id>', methods=["GET"])
    def get_status(order_id):
        try:
            order_status, order_amount = db.get_payment(order_id)
            if order_status == "paid":
                return {"paid": True}, HTTPStatus.OK
            elif order_status is not None:
                return {"paid": False}, HTTPStatus.OK
            else:
                return HTTPStatus.BAD_REQUEST
        except DatabaseException:
            return HTTPStatus.BAD_REQUEST

    @service.route('/add_funds/<uuid:user_id>/<int:amount>', methods=["POST"])
    def add_funds(user_id, amount):
        try:
            amount_added = db.add_user_credit(user_id, amount)
            return {"done": amount_added}, HTTPStatus.OK
        except DatabaseException:
            return HTTPStatus.BAD_REQUEST

    @service.route('/create_user', methods=["POST"])
    def create_user():
        try:
            new_id = db.create_user()
            if new_id is not None:
                return {"user_id": new_id}, HTTPStatus.CREATED
            else:
                return HTTPStatus.BAD_REQUEST
        except DatabaseException:
            return HTTPStatus.BAD_REQUEST

    @service.route('find_user/<uuid:user_id>', methods=["GET"])
    def find_user(user_id):
        try:
            user, credit = db.get_user(user_id)
            if user is None:
                return HTTPStatus.BAD_REQUEST
            else:
                return {"user_id": user, "credit": credit}, HTTPStatus.OK
        except DatabaseException:
            return HTTPStatus.BAD_REQUEST

    return service
