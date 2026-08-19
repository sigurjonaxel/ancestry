#!/bin/bash
cd "$(dirname "$0")"

if [ -f ".venv/bin/python" ]; then
    echo "🚀 Ræsi Ancestry server með .venv (sýndarumhverfi)..."
    exec .venv/bin/python server.py "$@"
elif command -v python3 &>/dev/null; then
    echo "🚀 Ræsi Ancestry server með python3..."
    exec python3 server.py "$@"
else
    echo "❌ Villa: Fann hvorki .venv né python3 á kerfinu."
    exit 1
fi
