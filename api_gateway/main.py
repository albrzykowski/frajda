import json
import os
import logging
from threading import Thread

import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import pika

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), '../shared_config/config.json')
with open(config_path) as f:
    config = json.load(f)

# Flask app with SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# RabbitMQ connection parameters
connection_params = pika.URLParameters(config['message_queue']['url'])

# --- Utility to create a new RabbitMQ connection and channel ---
def get_channel():
    conn = pika.BlockingConnection(connection_params)
    ch = conn.channel()
    ch.queue_declare(queue=config['message_queue']['queue'], durable=True)
    ch.queue_declare(queue=config['message_queue']['response_queue'], durable=True)
    return conn, ch

# HTTP endpoint to publish action
@app.route('/action', methods=['POST'])
def handle_action():
    try:
        data = request.json
        if not data or 'player_id' not in data or 'action' not in data:
            logging.error("Invalid input data.")
            return jsonify({"error": "Invalid input data"}), 400

        message = json.dumps({
            "player_id": data['player_id'],
            "action": data['action']
        })

        # Create a new connection and channel for this request
        conn, ch = get_channel()
        ch.basic_publish(
            exchange='',
            routing_key=config['message_queue']['queue'],
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        conn.close()

        logging.info(f"Published message to queue: {message}")
        return jsonify({"status": "Action accepted for processing"}), 202

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

# RabbitMQ consumer callback
def on_message(ch, method, properties, body):
    try:
        response = json.loads(body)
        socketio.emit('notification', response)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Processed and emitted message: {response}")
    except Exception as e:
        logging.error(f"Error handling message: {e}")

# RabbitMQ listener in a separate thread
def start_listening():
    try:
        consumer_conn, consumer_ch = get_channel()
        consumer_ch.basic_consume(
            queue=config['message_queue']['response_queue'],
            on_message_callback=on_message,
            auto_ack=False
        )
        logging.info("RabbitMQ listener started.")
        consumer_ch.start_consuming()
    except Exception as e:
        logging.error(f"Error in RabbitMQ listener: {e}")

# Start listener and run SocketIO server
if __name__ == '__main__':
    listener_thread = Thread(target=start_listening)
    listener_thread.daemon = True
    listener_thread.start()
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
