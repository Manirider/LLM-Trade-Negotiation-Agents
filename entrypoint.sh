#!/bin/sh
set -e

# Model to pull (default: llama3.1:8b for local, overridden by CI)
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"

echo "[entrypoint] Starting Ollama server..."
ollama serve &
SERVER_PID=$!

cleanup() {
    echo "[entrypoint] Shutting down Ollama (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[entrypoint] Waiting for Ollama API to be ready on 127.0.0.1:11434..."
for i in $(seq 1 60); do
    if curl -sf http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        echo "[entrypoint] Ollama API is ready"
        break
    fi
    echo "[entrypoint] Attempt $i/60: Ollama API not ready yet, waiting..."
    sleep 2
    if [ $i -eq 60 ]; then
        echo "[entrypoint] ERROR: Ollama API did not become ready after 120 seconds"
        exit 1
    fi
done

echo "[entrypoint] Checking if model '$MODEL' exists..."
# Use ollama list with name-only format for reliable parsing
if ollama list --format "{{.Name}}" 2>/dev/null | grep -qx "$MODEL"; then
    echo "[entrypoint] Model '$MODEL' already exists"
else
    echo "[entrypoint] Pulling model '$MODEL'..."
    ollama pull "$MODEL"
    echo "[entrypoint] Model '$MODEL' pulled successfully"
fi

# Verify model is now available
echo "[entrypoint] Verifying model '$MODEL' is available..."
for i in $(seq 1 10); do
    if ollama list --format "{{.Name}}" 2>/dev/null | grep -qx "$MODEL"; then
        echo "[entrypoint] Model '$MODEL' verified"
        break
    fi
    sleep 1
    if [ $i -eq 10 ]; then
        echo "[entrypoint] ERROR: Model '$MODEL' not found after pull"
        exit 1
    fi
done

echo "[entrypoint] Model provisioning complete. Keeping Ollama server running..."
# Ensure the server process is still alive
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "[entrypoint] ERROR: Ollama server process died unexpectedly"
    exit 1
fi

wait $SERVER_PID