#!/bin/bash
# Start the API server in one terminal
echo "Starting API server..."
python -m src.api.server --debug &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run the client in the same terminal
echo "Starting API client..."
python -m src.client.api_client

# Clean up server process when client exits
kill $SERVER_PID
