import pika
import json
import logging
import os
from repository import Repository
from service import GameService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    config = {}
    with open(os.path.join(os.path.dirname(__file__), '../shared_config/config.json')) as f:
        config = json.load(f)

    repo = Repository()
    game_service = GameService(
        game_rules_path=os.path.join(os.path.dirname(__file__), '../shared_config/game_rules.yml'),
        repo=repo
    )

    connection_params = pika.URLParameters(config['message_queue']['url'])
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=config['message_queue']['queue'], durable=True)
    
    def callback(ch, method, properties, body):
        try:
            event = json.loads(body)
            logging.info(f"Received event: {event}")
            game_service.process_action(event['player_id'], event['action'])
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error(f"Error processing event: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=config['message_queue']['queue'], on_message_callback=callback)

    logging.info("Starting to consume messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()