# 🚀 START HERE - 30 Second Setup

## Everything is Ready! Just Run:

```bash
./run.sh
```

That's it! ✅

---

## What Happens Next:

1. **Browser opens** → `http://localhost:8501`
2. **Click** → "🔄 Load Data from JSON Files" (in sidebar)
3. **Wait** → 2 seconds
4. **Chat** → Go to Chat tab and ask questions!

---

## First Question to Try:

```
Which services are degrading over the past 30 minutes?
```

---

## To Stop:

Press `Ctrl+C` in the terminal

---

## Need More Help?

📖 **Full Guide**: [SETUP_AND_RUN.md](SETUP_AND_RUN.md)

📖 **Quick Start**: [QUICKSTART.md](QUICKSTART.md)

📖 **Data Limits**: [DATA_LIMITS_GUIDE.md](DATA_LIMITS_GUIDE.md)

---

## Already Running?

**Open in browser:**
```
http://localhost:8501
```

**Or run on different port:**
```bash
venv/bin/streamlit run app.py --server.port 8502
```

---

## Visual Guide:

```
Step 1: Terminal
┌────────────────────────────────┐
│ $ ./run.sh                     │
│                                │
│ ✅ Starting Streamlit...       │
│ Local URL: http://localhost... │
└────────────────────────────────┘

Step 2: Browser Opens
┌────────────────────────────────┐
│  📊 SLO Chatbot                │
├────────────────────────────────┤
│  Sidebar:                      │
│  🔄 Load Data from JSON Files  │ ← CLICK THIS
│                                │
│  Dashboard | Chat              │
└────────────────────────────────┘

Step 3: Data Loaded
┌────────────────────────────────┐
│  ✅ Data loaded successfully!  │
│  63 services found             │
│                                │
│  Click "Chat" tab →            │
└────────────────────────────────┘

Step 4: Start Chatting
┌────────────────────────────────┐
│  💬 SLO Assistant              │
│                                │
│  You: Which services are       │
│       degrading?               │
│                                │
│  Assistant: I found 1 service  │
│  degrading...                  │
└────────────────────────────────┘
```

---

## 🎯 That's All You Need!

**One command to rule them all:**
```bash
./run.sh
```

Happy monitoring! 📊
