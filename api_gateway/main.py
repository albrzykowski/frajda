import pika
import json
import os
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

config = {}
with open(os.path.join(os.path.dirname(__file__), 'shared_config/config.json')) as f:
    config = json.load(f)

app = Flask(__name__)

connection_params = pika.URLParameters(config['message_queue']['url'])
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue=config['message_queue']['queue'], durable=True)

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
        channel.basic_publish(exchange='', routing_key=config['message_queue']['queue'], body=message, properties=pika.BasicProperties(delivery_mode=2))

        return jsonify({"status": "Action accepted for processing"}), 202
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)