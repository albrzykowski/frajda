import json
import threading
import socket
import socketio

# --- HTTP client using raw socket ---
def send_request(host="localhost", port=8000, path="/action"):
    request_body = json.dumps({
        "player_id": "user_1",
        "action": "action_4_access_archive"
    })
    http_request = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(request_body)}\r\n"
        "Connection: close\r\n"
        "\r\n"
        f"{request_body}"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(http_request.encode("utf-8"))

        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk

    decoded = response.decode("utf-8")
    headers, body = decoded.split("\r\n\r\n", 1)

    print("=== HTTP RESPONSE ===")
    print(headers)
    print("\nBODY:", body)

    try:
        data = json.loads(body)
        print("Parsed JSON:", data)
    except Exception:
        print("Failed to parse JSON.")


# --- WebSocket (Socket.IO) client ---
def start_socketio_client():
    sio = socketio.Client()

    @sio.event
    def connect():
        print("Connected to Socket.IO server.")
        # Send HTTP request once connected
        send_request()

    @sio.on("notification")
    def on_notification(data):
        print("=== ASYNC NOTIFICATION ===")
        print(data)

    @sio.event
    def disconnect():
        print("Disconnected from Socket.IO server.")

    # Keep connection alive
    sio.connect("http://localhost:8000", transports=['websocket'])
    sio.wait()


if __name__ == "__main__":
    # Start WebSocket listener in background thread
    ws_thread = threading.Thread(target=start_socketio_client, daemon=True)
    ws_thread.start()

    # Keep main thread alive
    ws_thread.join()
