import json
import threading
import socketio
import time

# --- WebSocket (Socket.IO) client ---
sio = socketio.Client()
connected = threading.Event()

@sio.event
def connect():
    print("Connected to Socket.IO server.")
    connected.set()

@sio.on("notification")
def on_notification(data):
    print("=== ASYNC NOTIFICATION ===")
    print(data)
    # Odłącz po otrzymaniu powiadomienia
    # sio.disconnect()

@sio.event
def disconnect():
    print("Disconnected from Socket.IO server.")

def send_request():
    request_body = json.dumps({
        "player_id": "user_1",
        "action": "action_4_access_archive"
    })
    
    try:
        # Użyj biblioteki 'requests' do prostszego wysyłania żądań HTTP
        import requests
        
        url = "http://localhost:8000/actions"
        headers = {"Content-Type": "application/json"}
        
        print("\n=== SENDING HTTP REQUEST ===")
        response = requests.post(url, data=request_body, headers=headers)
        
        print(f"HTTP RESPONSE: {response.status_code}")
        print(f"BODY: {response.json()}")
        
    except ImportError:
        print("Błąd: Biblioteka 'requests' nie jest zainstalowana. Użyj 'pip install requests'.")
    except Exception as e:
        print(f"Błąd podczas wysyłania żądania HTTP: {e}")

if __name__ == "__main__":
    print("Starting Socket.IO client...")
    
    # Uruchom klienta Socket.IO w tle
    sio.connect("http://localhost:8000", transports=['websocket'])
    
    # Poczekaj na nawiązanie połączenia
    connected.wait(timeout=5)
    
    if connected.is_set():
        # Uruchom wysyłanie żądania HTTP w osobnym wątku, aby nie blokować pętli nasłuchującej Socket.IO
        http_thread = threading.Thread(target=send_request)
        http_thread.start()
    else:
        print("Nie udało się połączyć z serwerem Socket.IO.")
    
    # Utrzymaj główny wątek, aby klient Socket.IO mógł działać
    sio.wait()