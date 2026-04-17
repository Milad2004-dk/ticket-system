from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flasgger import Swagger
import mysql.connector

app = Flask(__name__)
CORS(app)
app.config["SWAGGER"] = {"title": "Ticket API", "uiversion": 3}
swagger = Swagger(app)

DB_CONFIG = {
    "host": "turbine-db.mysql.database.azure.com",
    "user": "turbineadmin",
    "password": "Turbine123!",
    "database": "turbinedb",
    "ssl_disabled": False
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route("/tickets", methods=["GET"])
def get_tickets():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(result)

@app.route("/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
    ticket = cursor.fetchone()
    cursor.close()
    conn.close()
    if ticket is None:
        abort(404)
    return jsonify(ticket)

@app.route("/tickets", methods=["POST"])
def create_ticket():
    if not request.json or "subject" not in request.json:
        abort(400)
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "INSERT INTO tickets (customer_id, subject, message, priority) VALUES (%s, %s, %s, %s)",
        (request.json.get("customer_id", "anonymous"), request.json["subject"],
         request.json.get("message", ""), request.json.get("priority", "medium"))
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
    ticket = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify(ticket), 201

@app.route("/tickets/<int:ticket_id>/close", methods=["PUT"])
def close_ticket(ticket_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("UPDATE tickets SET status = 'closed' WHERE id = %s", (ticket_id,))
    conn.commit()
    cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
    ticket = cursor.fetchone()
    cursor.close()
    conn.close()
    if ticket is None:
        abort(404)
    return jsonify(ticket)

@app.route("/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"result": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
