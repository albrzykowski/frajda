import couchdb
import os
import logging
from dotenv import load_dotenv

class Repository:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        couchdb_user = os.getenv('COUCHDB_USER')
        couchdb_pass = os.getenv('COUCHDB_PASSWORD')
        couchdb_host = os.getenv('COUCHDB_HOST', 'localhost')
        couchdb_port = int(os.getenv('COUCHDB_PORT', 5984))
        db_name = os.getenv('COUCHDB_DB', 'players')

        url = f"http://{couchdb_user}:{couchdb_pass}@{couchdb_host}:{couchdb_port}/"

        try:
            couch = couchdb.Server(url)
            self.db = couch[db_name]
        except couchdb.http.ResourceNotFound:
            logging.error(f"Database '{db_name}' not found. Please create it manually.")
            raise

    def get_player(self, player_id: str):
        try:
            return self.db[player_id]
        except couchdb.http.ResourceNotFound:
            logging.info(f"Player {player_id} not found, creating new document.")
            return {"_id": player_id, "inventory": {}, "titles": [], "completed_quests": [], "currency": 0}

    def save_player(self, player_doc: dict):
        self.db.save(player_doc)
