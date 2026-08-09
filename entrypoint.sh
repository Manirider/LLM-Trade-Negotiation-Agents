#!/bin/sh
set -e

# Model to pull (default: llama3.1:8b for local, overridden by CI)
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"

echo "Starting Ollama server..."
ollama serve &
SERVER_PID=$!

cleanup() {
    echo "Shutting down Ollama (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for Ollama API to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama API is ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        echo "ERROR: Ollama API did not become ready after 60 seconds"
        exit 1
    fi
done

echo "Checking if model '$MODEL' exists..."
# Use ollama list with name-only format for reliable parsing
if ollama list --format "{{.Name}}" 2>/dev/null | grep -qx "$MODEL"; then
    echo "Model '$MODEL' already exists"
else
    echo "Pulling model '$MODEL'..."
    ollama pull "$MODEL"
    echo "Model '$MODEL' pulled successfully"
fi

# Verify model is now available
echo "Verifying model '$MODEL' is available..."
for i in $(seq 1 10); do
    if ollama list --format "{{.Name}}" 2>/dev/null | grep -qx "$MODEL"; then
        echo "Model '$MODEL' verified"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "ERROR: Model '$MODEL' not found after pull"
        exit 1
    fi
done

echo "Model provisioning complete. Keeping Ollama server running..."
# Ensure the server process is still alive
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Ollama server process died unexpectedly"
    exit 1
fi

wait $SERVER_PID