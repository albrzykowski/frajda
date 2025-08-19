import os
import logging
import json
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, join_room
import pika
import eventlet
from eventlet.queue import Queue

eventlet.monkey_patch()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RABBITMQ_USER = os.environ.get('RABBITMQ_USER')
RABBITMQ_PASS = os.environ.get('RABBITMQ_PASS')
RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_PORT = os.environ.get('RABBITMQ_PORT', '5672')
RABBITMQ_QUEUE = os.environ.get('RABBITMQ_QUEUE', 'actions')
RABBITMQ_RESPONSE_QUEUE = os.environ.get('RABBITMQ_RESPONSE_QUEUE', 'responses')
RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

rabbitmq_url = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:{RABBITMQ_PORT}{RABBITMQ_VHOST}"

app = Flask(__name__)
# This change enables communication between multiple Gunicorn workers
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', message_queue=rabbitmq_url)

message_queue = Queue()
connection_params = pika.URLParameters(rabbitmq_url)

def get_channel():
    conn = pika.BlockingConnection(connection_params)
    ch = conn.channel()
    ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    ch.queue_declare(queue=RABBITMQ_RESPONSE_QUEUE, durable=True)
    return conn, ch

@app.route('/actions', methods=['POST'])
def handle_action():
    try:
        data = request.json
        if not data or 'player_id' not in data or 'action' not in data:
            return jsonify({"error": "Invalid input data"}), 400

        message = {"player_id": data['player_id'], "action": data['action']}
        conn, ch = get_channel()
        ch.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()
        logging.info(f"Published message to queue: {message}")
        return jsonify({"status": "Action accepted for processing"}), 202
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logging.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Client disconnected: {request.sid}")

@socketio.on('identify')
def handle_identify(data):
    player_id = data.get('player_id')
    if player_id:
        join_room(player_id)
        logging.info(f"Client {request.sid} identified as {player_id} and joined room.")

def on_message(ch, method, properties, body):
    try:
        response = json.loads(body)
        player_id = response.get('player_id')
        if player_id:
            message_queue.put((player_id, response))
            logging.info(f"Queued message for room '{player_id}'")
        else:
            logging.warning(f"Received message without player_id: {response}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error(f"Error in on_message callback: {e}")

def start_listening():
    try:
        consumer_conn, consumer_ch = get_channel()
        consumer_ch.basic_consume(
            queue=RABBITMQ_RESPONSE_QUEUE,
            on_message_callback=on_message,
            auto_ack=False
        )
        logging.info("RabbitMQ listener started.")
        consumer_ch.start_consuming()
    except Exception as e:
        logging.error(f"Error in RabbitMQ listener: {e}")

def message_emitter():
    logging.info("Socket.IO emitter started.")
    while True:
        try:
            player_id, response = message_queue.get()
            socketio.emit("notification", response, room=player_id)
            logging.info(f"Successfully emitted message to room '{player_id}'")
        except Exception as e:
            logging.error(f"Error in message_emitter: {e}")

eventlet.spawn(start_listening)
eventlet.spawn(message_emitter)
