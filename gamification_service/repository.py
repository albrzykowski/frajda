import couchdb
import os
import json
import logging

class Repository:
    def __init__(self):
        config = {}
        with open(os.path.join(os.path.dirname(__file__), '../shared_config/config.json')) as f:
            config = json.load(f)

        db_config = config['db_connection']
        url = db_config['url']
        
        try:
            couch = couchdb.Server(url)
            self.db = couch[db_config['db_name']]
        except couchdb.http.ResourceNotFound:
            logging.error(f"Database '{db_config['db_name']}' not found. Please create it manually.")
            raise

    def get_player(self, player_id: str):
        try:
            return self.db[player_id]
        except couchdb.http.ResourceNotFound:
            logging.info(f"Player {player_id} not found, creating new document.")
            return {"_id": player_id, "inventory": {}, "titles": [], "completed_quests": [], "currency": 0}

    def save_player(self, player_doc: dict):
        self.db.save(player_doc)