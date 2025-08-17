import socket
import json
import threading
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
        pass


# --- WebSocket (Socket.IO) client ---
def start_socketio_client():
    sio = socketio.Client()

    @sio.on("connect")
    def on_connect():
        print("Connected to Socket.IO server.")
        send_request()  # <- wyślij żądanie dopiero po połączeniu

    @sio.on("notification")
    def on_notification(data):
        print("=== ASYNC NOTIFICATION ===")
        print(data)

    @sio.on("disconnect")
    def on_disconnect():
        print("Disconnected from Socket.IO server.")

    sio.connect("http://localhost:8000", transports=['websocket'])
    sio.wait()


if __name__ == "__main__":
    # Start WebSocket listener in background thread
    t = threading.Thread(target=start_socketio_client, daemon=True)
    t.start()

    # Send HTTP request
    send_request()

    # Keep main thread alive so WebSocket can receive notifications
    t.join()
