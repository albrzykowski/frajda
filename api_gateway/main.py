import os
import logging
from threading import Thread
import json

import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import pika

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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

connection_params = pika.URLParameters(rabbitmq_url)

def get_channel():
    conn = pika.BlockingConnection(connection_params)
    ch = conn.channel()
    ch.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    ch.queue_declare(queue=RABBITMQ_RESPONSE_QUEUE, durable=True)
    return conn, ch

@app.route('/action', methods=['POST'])
def handle_action():
    try:
        data = request.json
        if not data or 'player_id' not in data or 'action' not in data:
            logging.error("Invalid input data.")
            return jsonify({"error": "Invalid input data"}), 400

        message = {
            "player_id": data['player_id'],
            "action": data['action']
        }

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

def on_message(ch, method, properties, body):
    logging.info("----------- 3")
    try:
        logging.info("----------- 4")
        response = json.loads(body)
        socketio.emit('notification', response)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Processed and emitted message: {response}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")

def start_listening():
    logging.info("----------- 1")
    try:
        logging.info("----------- 2")
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

eventlet.spawn(start_listening)
logging.info("Background listener task spawned with eventlet.")

if __name__ == '__main__':
    logging.info("This block is for local development only. Gunicorn will ignore it.")
    logging.info("Starting listener thread...")
    listener_thread = Thread(target=start_listening)
    listener_thread.daemon = True
    listener_thread.start()
    logging.info("Starting SocketIO server...")
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
