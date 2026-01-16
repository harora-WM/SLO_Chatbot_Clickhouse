# 🚀 Setup and Run Guide

## Quick Start (2 Minutes)

### Step 1: Verify Setup
Everything is already installed! Just verify:

```bash
# Check virtual environment exists
ls venv/

# Check if dependencies are installed
venv/bin/pip list | grep streamlit
```

✅ If you see packages listed, you're ready to go!

---

### Step 2: Run the Chatbot

**Option A: Using the Quick Start Script** (Recommended)
```bash
./run.sh
```

**Option B: Manual Start**
```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit
streamlit run app.py
```

**Option C: Direct Run (without activating venv)**
```bash
venv/bin/streamlit run app.py
```

---

### Step 3: Open in Browser

The app will automatically open at:
```
http://localhost:8501
```

If it doesn't open automatically, just copy-paste that URL into your browser.

---

### Step 4: Load Data

In the Streamlit UI sidebar:

1. **Click**: "🔄 Refresh from OpenSearch"
2. **Wait**: ~2-5 seconds for data to load from OpenSearch
3. **See**: "✅ Loaded X service logs and Y error logs" message

✅ Data will be loaded from your OpenSearch instance (max 4-hour window)!

---

### Step 5: Start Chatting!

Go to the **💬 Chat** tab and ask:

```
Which services are degrading over the past 30 minutes?
```

🎉 **You're done!**

---

## Detailed Setup (If Starting Fresh)

### Prerequisites

- Python 3.8+ (You have 3.12 ✅)
- 2GB RAM minimum
- Internet connection (for AWS Bedrock)

---

### Complete Setup from Scratch

If you need to set up everything from scratch:

```bash
# 1. Navigate to project
cd /home/hardik121/slo_chatbot

# 2. Create virtual environment (already done)
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies (already done)
pip install -r requirements.txt

# 5. Verify .env file exists
cat .env

# 6. Run tests (optional)
python test_system.py

# 7. Start the app
streamlit run app.py
```

---

## Environment Variables

Your `.env` file should be configured with your credentials:

```env
AWS_ACCESS_KEY_ID=<your_aws_access_key>
AWS_SECRET_ACCESS_KEY=<your_aws_secret_key>
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
```

**Setup:** Copy `.env.example` to `.env` and fill in your AWS and OpenSearch credentials.

---

## What Happens When You Start

```
$ ./run.sh

==================================================
   SLO Chatbot - Starting...
==================================================

✅ Activating virtual environment...
✅ Starting Streamlit app...

📊 The chatbot will open in your browser at http://localhost:8501

Press Ctrl+C to stop the server

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

## First Time User Guide

### 1. **Dashboard Tab** (Default View)

When you first open the app, you'll see:
- Service Health Dashboard
- Metrics cards (Total Services, Healthy, Degraded, Violated)
- Top Services by Volume chart
- Current SLO Violations

**First Action**: Click "🔄 Refresh from OpenSearch" in sidebar to load data

---

### 2. **Sidebar Controls**

```
🔧 Configuration
├── Data Management
│   ├── 📊 Data is loaded from OpenSearch only
│   │
│   ├── OpenSearch Options
│   │   ├── Time Range: [Last 4 hours ▼] (or Custom - max 4 hours)
│   │   ├── Max Results: 1000 (100-10,000)
│   │   └── 🔄 Refresh from OpenSearch ← START HERE
│   │
│   ├── 📅 Data Time Range
│   │   └── Shows loaded data range
│   │
│   ├── 📊 Total Services Loaded
│   │
│   ├── 🗑️ Clear Chat History
│   │
│   └── 💡 Sample Questions
```

---

### 3. **Chat Tab**

Switch to the Chat tab and try these questions:

**Beginner Questions:**
```
What's the overall health of services?
Show me the top services by request volume
What are the most common errors?
```

**Intermediate Questions:**
```
Which services are degrading over the past 30 minutes?
Show me services violating their SLO
What's the error rate for the grant-token service?
```

**Advanced Questions:**
```
Which services are expected to have issues today?
Calculate error budget for the grant-token service
Show historical patterns for the onboarding service
Compare error rates across all degrading services
```

---

## Fetching Data from OpenSearch

### Using Default Settings (Quick)

1. In sidebar, click **"🔄 Refresh from OpenSearch"**
2. Wait 2-5 seconds
3. Data refreshes automatically (last 4 hours)

### Using Custom Time Range

1. Select time range: **"Custom"** from dropdown
2. Pick **Start Date** and **Start Time**
3. Pick **End Date** and **End Time** (max 4 hours from start)
4. Adjust **Max Results** if needed (100-10,000)
5. Click **"🔄 Refresh from OpenSearch"**
6. Wait for completion

**Important Limits:**
- Maximum time window: **4 hours** (enforced by the app)
- Maximum results: **10,000** per query
- Scroll API: **Not used** (data stays within limits)

---

## Stopping the Chatbot

Press `Ctrl+C` in the terminal where Streamlit is running:

```
Stopping...
^C
  Stopping...
```

---

## Troubleshooting

### Issue: Port 8501 already in use

```bash
# Find and kill the process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run app.py --server.port 8502
```

---

### Issue: Module not found

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

---

### Issue: AWS Bedrock authentication error

```bash
# Verify .env file
cat .env

# Check AWS credentials are correct
# Make sure no extra spaces in .env file
```

---

### Issue: OpenSearch connection failed

```bash
# Test OpenSearch connection
python3 -c "
from data.ingestion.opensearch_client import OpenSearchClient
client = OpenSearchClient()
print('✅ Connected!' if client.test_connection() else '❌ Failed')
"
```

---

### Issue: Database locked or error

```bash
# Clear the database and reload
rm -rf data/database/slo_analytics.duckdb*

# Restart the app
./run.sh

# Reload data in UI
```

---

## Running Tests

### Full Test Suite

```bash
venv/bin/python test_system.py
```

Expected output:
```
============================================================
SLO CHATBOT SYSTEM TEST
============================================================

TEST 1: Data Loading                ✅ PASSED
TEST 2: SLO Calculator              ✅ PASSED
TEST 3: Degradation Detector        ✅ PASSED
TEST 4: Trend Analyzer              ✅ PASSED
TEST 5: Metrics Aggregator          ✅ PASSED

Total: 5/5 tests passed

🎉 All tests passed! System is ready to use.
```

---

## Performance Tips

### For Faster Queries
- Use "Last 4 hours" default option (fastest)
- Keep max results at 1,000 for quick checks
- Custom time ranges take slightly longer

### For Maximum Data
- Set Max Results to 10,000
- Use the full 4-hour window
- Note: Data beyond 4 hours requires multiple manual refreshes

---

## File Locations

```
/home/hardik121/SLO_Chatbot_Our/
├── app.py                          ← Main application
├── run.sh                          ← Quick start script
├── test_system.py                  ← Test suite (uses local JSON for testing)
├── .env                            ← AWS & OpenSearch credentials
└── data/database/
    └── slo_analytics.duckdb        ← Local database (auto-created)
```

---

## Next Steps After Setup

1. ✅ **Load data** - Click "🔄 Refresh from OpenSearch"
2. ✅ **Explore dashboard** - View service health metrics
3. ✅ **Try chat** - Ask sample questions
4. ✅ **Monitor continuously** - Refresh data periodically
5. ✅ **Customize** - Adjust SLO thresholds in `utils/config.py`

---

## Quick Command Reference

| Task | Command |
|------|---------|
| **Start chatbot** | `./run.sh` |
| **Run tests** | `venv/bin/python test_system.py` |
| **Activate venv** | `source venv/bin/activate` |
| **Install deps** | `venv/bin/pip install -r requirements.txt` |
| **Clear database** | `rm -rf data/database/*.duckdb*` |
| **Stop chatbot** | `Ctrl+C` |

---

## 🎉 You're All Set!

Just run:
```bash
./run.sh
```

And start chatting! 💬
