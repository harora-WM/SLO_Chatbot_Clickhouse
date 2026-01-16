#!/bin/bash

echo "=================================================="
echo "   SLO Chatbot - Starting..."
echo "=================================================="
echo ""

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "✅ Starting Streamlit app..."
echo ""
echo "📊 The chatbot will open in your browser at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run app.py
