#!/bin/sh
set -e

# Allow overriding model via environment; default to llama3.1:8b for local, tiny for CI
MODEL="${OLLAMA_MODEL:-llama3.1:8b}"
CI_MODE="${CI:-false}"

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

# In CI mode, skip heavy model pull - use tiny model or rely on fallback
if [ "$CI_MODE" = "true" ]; then
    echo "CI mode: skipping heavy model pull (using fallback responses)"
    # Optionally pull a tiny model if needed for integration tests
    # ollama pull qwen2:0.5b  # ~400MB, fast
else
    echo "Checking if model '$MODEL' exists..."
    if ollama list | grep -q "^$MODEL "; then
        echo "Model '$MODEL' already exists"
    else
        echo "Pulling model '$MODEL'..."
        ollama pull "$MODEL"
        echo "Model '$MODEL' pulled successfully"
    fi
fi

echo "Stopping background server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo "Starting Ollama server (foreground)..."
exec ollama serve