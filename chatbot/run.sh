#!/bin/bash

echo "=================================================="
echo "   SLO Chatbot - Starting..."
echo "=================================================="
echo ""

# Activate virtual environment (check both chatbot and root directories)
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment (chatbot/venv)..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "✅ Activating virtual environment (root venv)..."
    source ../venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run from repository root:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "✅ Starting Streamlit app..."
echo ""
echo "📊 The chatbot will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
