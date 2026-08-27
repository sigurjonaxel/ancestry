#!/bin/bash
cd "$(dirname "$0")"

echo "========================================================"
echo "🚀 Ræsi Saga Web App & Cloudflare Tunnel (Persistent Mode)"
echo "========================================================"

# Trap exits
trap 'pkill -P $$; exit' SIGINT SIGTERM

# 1. Start Server Loop
start_server() {
    while true; do
        if [ -f ".venv/bin/python" ]; then
            .venv/bin/python server.py
        else
            python3 server.py
        fi
        echo "⚠️ server.py stöðvaðist! Endurræsi eftir 2 sekúndur..."
        sleep 2
    done
}

# 2. Start Cloudflare Tunnel Loop
start_tunnel() {
    while true; do
        if [ ! -f "/tmp/cloudflared" ]; then
            curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /tmp/cloudflared
            chmod +x /tmp/cloudflared
        fi
        /tmp/cloudflared tunnel --url http://localhost:8000
        echo "⚠️ Cloudflare tunnel stöðvaðist! Endurræsi eftir 3 sekúndur..."
        sleep 3
    done
}

start_server &
start_tunnel &

wait
