#!/bin/bash
# OnSpect AI Demo Launcher
# Start de Streamlit web interface

set -e

# Ga naar project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=================================="
echo "OnSpect AI - Demo Launcher"
echo "=================================="

# Check of Ollama draait
if ! pgrep -x "ollama" > /dev/null; then
    echo "WAARSCHUWING: Ollama lijkt niet te draaien."
    echo "Start Ollama met: ollama serve"
    echo ""
fi

# Check of het model beschikbaar is
MODEL=${ONSPECT_MODEL:-"gemma3:27b"}
echo "Gebruikt model: $MODEL"

# Start Streamlit
echo ""
echo "Start de web interface..."
echo "Open http://localhost:8501 in je browser"
echo ""

streamlit run app/streamlit_app.py
