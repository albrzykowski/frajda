import pika
import json
import logging
import os
from repository import Repository
from service import GameService
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def main():
    repo = Repository()
    game_service = GameService(
        game_rules_path=os.path.join(os.path.dirname(__file__), '../shared_config/game_rules.yml'),
        repo=repo
    )

    # RabbitMQ connection parameters from environment
    rabbitmq_user = os.getenv('RABBITMQ_USER')
    rabbitmq_pass = os.getenv('RABBITMQ_PASS')
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    queue_name = os.getenv('RABBITMQ_QUEUE', 'actions')
    response_queue_name = os.getenv('RABBITMQ_RESPONSE_QUEUE', 'responses')

    connection_url = f'amqp://{rabbitmq_user}:{rabbitmq_pass}@{rabbitmq_host}:{rabbitmq_port}/%2F'
    connection_params = pika.URLParameters(connection_url)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def callback(ch, method, properties, body):
        try:
            event = json.loads(body)
            logging.info(f"Received event: {event}")
            
            # Process the action
            result = game_service.process_action(event['player_id'], event['action'])

            # Publish response to response_queue
            response_channel = connection.channel()
            response_channel.queue_declare(queue=response_queue_name, durable=True)
            response_message = json.dumps({
                "player_id": event['player_id'],
                "result": result,
            })
            response_channel.basic_publish(
                exchange='',
                routing_key=response_queue_name,
                body=response_message,
                properties=pika.BasicProperties(delivery_mode=2)
            )

            logging.info(f"Published response message to queue '{response_queue_name}': {response_message}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error(f"Error processing event: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    logging.info("Starting to consume messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()
