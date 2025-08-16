# Frajda

Frajda is a high-performance **gamification engine** and library for your applications. Designed for simplicity and flexibility, it allows you to quickly enrich your projects with engaging game elements like achievements, leaderboards, and rewards.

## Key Features

- **Performance**: Built on a message-based architecture and leveraging RabbitMQ, the engine processes events asynchronously, minimizing the load on your main application.

- **Declarative Configuration**: All game rules, rewards, and challenges are defined in simple, readable **YAML files**. This allows you to easily modify and test new mechanics without changing a single line of code.

- **Modular Architecture**: Frajda operates as a standalone service that can be scaled and developed independently of the rest of your project.

- **Data Persistence**: Integration with CouchDB ensures that player progress is securely stored and easily accessible.

## How It Works

1.  **Client (Your Script)**: Sends events (e.g., 'action_1') to a RabbitMQ queue.
2.  **Engine (Frajda)**: Listens for messages, processes them, and updates the player's state in the CouchDB database.
3.  **Application**: Can read the player's current state from CouchDB at any time.

## Getting Started

1.  Make sure you have Docker and Docker Compose installed.
2.  Start the RabbitMQ and CouchDB services with Docker Compose:
    ```sh
    docker-compose up -d
    ```
3.  Run the gamification engine server:
    ```sh
    # In a new terminal
    python -m gamification_service.main
    ```
4.  Run your test script to send events and see the engine in action:
    ```sh
    # In another terminal
    python -m gamification_service.test_events
    ```