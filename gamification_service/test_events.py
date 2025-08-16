import pika
import json
import time
import couchdb
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_config():
    with open(os.path.join(os.path.dirname(__file__), '../shared_config/config.json')) as f:
        return json.load(f)

def send_action_to_queue(player_id, action):
    config = get_config()
    mq_config = config['message_queue']
    
    connection_params = pika.URLParameters(mq_config['url'])
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=mq_config['queue'], durable=True)
    
    message = json.dumps({
        "player_id": player_id,
        "action": action
    })
    channel.basic_publish(exchange='', routing_key=mq_config['queue'], body=message, properties=pika.BasicProperties(delivery_mode=2))
    logging.info(f"Sent action: {action} for player: {player_id}")
    connection.close()

def get_player_state_from_db(player_id):
    config = get_config()
    db_config = config['db_connection']
    
    try:
        url = db_config['url']
        couch = couchdb.Server(url)
        db = couch[db_config['db_name']]
        return db[player_id]
    except (couchdb.http.ResourceNotFound, ConnectionRefusedError) as e:
        logging.error(f"Error connecting to DB or finding player: {e}")
        return None

if __name__ == '__main__':
    player_id = "test_player_1"
    
    logging.info("--- TEST CASE 1: Collect 2 items for quest 'Hunter of Secrets' ---")
    
    send_action_to_queue(player_id, "akcja_2_zapal_swiece")
    time.sleep(2) 
    send_action_to_queue(player_id, "akcja_3_odczytaj_inskrypcje")
    
    time.sleep(5)
    
    player_doc = get_player_state_from_db(player_id)
    if player_doc:
        logging.info("Current player state after actions:")
        logging.info(f"Inventory: {player_doc.get('inventory')}")
        logging.info(f"Titles: {player_doc.get('titles')}")
        logging.info(f"Completed Quests: {player_doc.get('completed_quests')}")
    else:
        logging.error("Failed to retrieve player state.")

    logging.info("\n--- TEST CASE 2: Complete 'Timeless Vortex' (all 3 fragments) ---")
    
    send_action_to_queue(player_id, "akcja_1_odwiedz_komnate")
    time.sleep(5)
    
    player_doc = get_player_state_from_db(player_id)
    if player_doc:
        logging.info("Current player state after action:")
        logging.info(f"Inventory: {player_doc.get('inventory')}")
        logging.info(f"Titles: {player_doc.get('titles')}")
        logging.info(f"Completed Quests: {player_doc.get('completed_quests')}")
    else:
        logging.error("Failed to retrieve player state.")