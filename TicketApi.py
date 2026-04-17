from flask import Flask, jsonify, request, abort, send_file
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
    "ssl_ca": "/etc/ssl/certs/ca-certificates.crt"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/tickets', methods=['GET'])
def get_tickets():
    """
    Hent alle tickets
    ---
    tags:
      - Tickets
    responses:
      200:
        description: Liste af alle tickets
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    tickets = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(tickets)

@app.route('/tickets', methods=['POST'])
def create_ticket():
    """
    Opret en ny ticket
    ---
    tags:
      - Tickets
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - customer_id
            - subject
            - message
          properties:
            customer_id:
              type: string
              example: "Milad"
            subject:
              type: string
              example: "IT problem"
            message:
              type: string
              example: "Min computer virker ikke"
            priority:
              type: string
              example: "high"
    responses:
      201:
        description: Ticket oprettet
      400:
        description: Manglende felter
    """
    data = request.json
    if not data or not all(k in data for k in ['customer_id', 'subject', 'message']):
        abort(400)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tickets (customer_id, subject, message, priority) VALUES (%s, %s, %s, %s)",
        (data['customer_id'], data['subject'], data['message'], data.get('priority', 'medium'))
    )
    db.commit()
    ticket_id = cursor.lastrowid
    cursor.close()
    db.close()
    return jsonify({'id': ticket_id, 'status': 'open'}), 201

@app.route('/tickets/<int:ticket_id>/close', methods=['PUT'])
def close_ticket(ticket_id):
    """
    Luk en ticket
    ---
    tags:
      - Tickets
    parameters:
      - name: ticket_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Ticket lukket
      404:
        description: Ticket ikke fundet
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE tickets SET status='closed' WHERE id=%s", (ticket_id,))
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()
    if affected == 0:
        abort(404)
    return jsonify({'result': True})

@app.route('/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """
    Slet en ticket
    ---
    tags:
      - Tickets
    parameters:
      - name: ticket_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Ticket slettet
      404:
        description: Ticket ikke fundet
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM tickets WHERE id=%s", (ticket_id,))
    db.commit()
    affected = cursor.rowcount
    cursor.close()
    db.close()
    if affected == 0:
        abort(404)
    return jsonify({'result': True})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
