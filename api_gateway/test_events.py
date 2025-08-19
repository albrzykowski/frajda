import eventlet
eventlet.monkey_patch()

import json
import socketio
import requests
import sys

notification_received = eventlet.event.Event()
sio = socketio.Client(logger=True, engineio_logger=True)
PLAYER_ID = "user_3487"

@sio.event
def connect():
    print("Connected to Socket.IO server.")
    sio.emit('identify', {'player_id': PLAYER_ID})
    eventlet.spawn(send_http_request)

@sio.on("notification")
def on_notification(data):
    print("\n=== ASYNC NOTIFICATION ===")
    print(data)
    notification_received.send()

@sio.event
def disconnect():
    print("Disconnected from Socket.IO server.")
    if not notification_received.ready():
        notification_received.send()

def send_http_request():
    try:
        url = "http://localhost:8000/actions"
        headers = {"Content-Type": "application/json"}
        request_body = json.dumps({
            "player_id": PLAYER_ID,
            "action": "action_4_access_archive"
        })

        print("\n=== SENDING HTTP REQUEST ===")
        response = requests.post(url, data=request_body, headers=headers)
        
        print(f"HTTP RESPONSE: {response.status_code}")
        print(f"BODY: {response.json()}")
        
    except Exception as e:
        print(f"Error during HTTP request: {e}", file=sys.stderr)
        notification_received.send_exception(e)

if __name__ == "__main__":
    print("Starting Socket.IO client...")
    
    try:
        sio.connect("http://localhost:8000", transports=['websocket'])
        notification_received.wait()

    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
    finally:
        if sio.connected:
            sio.disconnect()
        print("\nClient finished.")