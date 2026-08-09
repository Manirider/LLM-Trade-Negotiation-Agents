#!/bin/sh
set -e

# Model to pull (default: llama3.1:8b for local, overridden by CI)
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"

echo "Starting Ollama server..."
ollama serve &
SERVER_PID=$!

cleanup() {
    echo "Shutting down Ollama..."
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
done

echo "Checking if model '$MODEL' exists..."
if ollama list | grep -q "^$MODEL "; then
    echo "Model '$MODEL' already exists"
else
    echo "Pulling model '$MODEL'..."
    ollama pull "$MODEL"
    echo "Model '$MODEL' pulled successfully"
fi

echo "Model provisioning complete. Keeping Ollama server running..."
wait $SERVER_PID