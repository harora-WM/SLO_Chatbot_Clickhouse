# SLO Chatbot - Complete Setup Guide

This guide walks you through setting up the SLO Chatbot from scratch in **under 10 minutes**.

## Prerequisites

- **Docker Desktop** - For ClickHouse database
- **Python 3.12+** - For running the application
- **AWS Bedrock Access** - For Claude Sonnet 4.5
- **Git** - For cloning the repository

## Step-by-Step Setup

### Step 1: ClickHouse Setup (2 minutes)

ClickHouse is set up from the `kafka_put` project:

```bash
# Navigate to kafka_put directory
cd /path/to/kafka_put

# Run setup script (one-time setup)
./clickhouse_setup.sh

# Expected output:
# ✅ ClickHouse container created
# ✅ ClickHouse is running on ports 8123 (HTTP) and 9000 (Native)
# ✅ Database is ready
```

**Verify ClickHouse is running:**
```bash
docker ps | grep clickhouse

# Expected output:
# clickhouse-server ... Up ... 0.0.0.0:8123->8123/tcp, 0.0.0.0:9000->9000/tcp
```

**If ClickHouse stops after system restart:**
```bash
docker start clickhouse-server
```

### Step 2: Load Data into ClickHouse (3 minutes)

Data is loaded via the kafka_put pipeline:

```bash
# Still in kafka_put directory
cd /path/to/kafka_put

# 1. Activate virtual environment (create if needed)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies (if first time)
pip install -r requirements.txt

# 3. Fetch data from Platform API → Kafka
python kafka_producer.py

# Expected output:
# ✅ Keycloak authentication successful
# ✅ Fetched 122 transaction records
# ✅ Published 122 messages to Kafka

# 4. Load data from Kafka → ClickHouse
python kafka_to_clickhouse.py

# Expected output:
# Processing message 1/122...
# Processing message 2/122...
# ...
# ✅ Inserted 8,759 rows to ClickHouse
#
# Press Ctrl+C to stop (after all messages processed)
```

**Verify data is loaded:**
```bash
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# Expected output: 8759
```

### Step 3: SLO Chatbot Setup (3 minutes)

Now set up the actual chatbot:

```bash
# Navigate to SLO Chatbot directory
cd /path/to/SLO_Chatbot_Latest-v1

# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# Expected output:
# Successfully installed streamlit boto3 pandas clickhouse-connect ...
```

### Step 4: Configure Environment (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your AWS credentials
nano .env  # Or use any text editor

# Required: Add these two lines with your actual AWS credentials
AWS_ACCESS_KEY_ID=your_actual_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_key_here

# Optional: Everything else has sensible defaults
# CLICKHOUSE_HOST=localhost (already set correctly)
# CLICKHOUSE_PORT=8123 (already set correctly)
# AWS_REGION=ap-south-1 (already set correctly)
```

**Getting AWS Credentials:**
1. Log in to AWS Console
2. Go to IAM → Users → Your User
3. Security credentials → Create access key
4. Choose "Application running on AWS compute service"
5. Copy Access Key ID and Secret Access Key

### Step 5: Run the Chatbot (1 minute)

```bash
# Make sure you're in SLO_Chatbot_Latest-v1 directory
# Make sure virtual environment is activated

streamlit run app.py

# Expected output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
# Network URL: http://192.168.x.x:8501
```

Open your browser to: **http://localhost:8501**

### Step 6: Test the Chatbot (1 minute)

Try these sample questions:

```
1. "Which services have high burn rates?"
2. "Show me the slowest services by P99 latency"
3. "Which services are degrading?"
4. "Show composite health scores"
```

You should see Claude analyzing the data and returning insights!

## Verification Checklist

Run this checklist to ensure everything is set up correctly:

```bash
# 1. ClickHouse is running
docker ps | grep clickhouse
# ✅ Should show: clickhouse-server ... Up ...

# 2. Data is loaded
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# ✅ Should show: 8759

# 3. Virtual environment is activated
which python
# ✅ Should show: /path/to/SLO_Chatbot_Latest-v1/venv/bin/python

# 4. Dependencies are installed
python -c "import streamlit, clickhouse_connect, boto3; print('✅ All dependencies installed')"
# ✅ Should show: ✅ All dependencies installed

# 5. Environment variables are set
python -c "from utils.config import AWS_ACCESS_KEY_ID; print('✅ AWS credentials configured' if AWS_ACCESS_KEY_ID else '❌ Missing AWS credentials')"
# ✅ Should show: ✅ AWS credentials configured

# 6. ClickHouse connection works
python -c "from data.database.clickhouse_manager import ClickHouseManager; ClickHouseManager(); print('✅ ClickHouse connected')"
# ✅ Should show: ✅ ClickHouse connected
```

## Running Tests

Verify everything works with the comprehensive test suite:

```bash
# In SLO_Chatbot_Latest-v1 directory with venv activated
python3 test_clickhouse_comprehensive.py

# Expected output:
# ================================================================================
# TEST SUMMARY
# ================================================================================
# Total Tests: 38
# Passed: 38
# Failed: 0
# Warnings: 2
#
# ✅ All tests passed! Migration is successful.
```

## Troubleshooting

### Issue: ClickHouse not running

```bash
# Check if container exists
docker ps -a | grep clickhouse

# If stopped, start it
docker start clickhouse-server

# If doesn't exist, set up again
cd /path/to/kafka_put
./clickhouse_setup.sh
```

### Issue: No data in ClickHouse

```bash
# Check row count
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# If zero, reload data
cd /path/to/kafka_put
python kafka_producer.py
python kafka_to_clickhouse.py
```

### Issue: AWS Bedrock authentication errors

```bash
# Verify credentials are set
cat .env | grep AWS_

# Test AWS connection
python3 -c "import boto3; client = boto3.client('bedrock-runtime', region_name='ap-south-1'); print('✅ AWS connection works')"
```

### Issue: Port 8501 already in use

```bash
# Use different port
streamlit run app.py --server.port 8502

# Or kill existing Streamlit process
pkill -f streamlit
```

### Issue: Module import errors

```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

## Quick Reference Commands

### Start Everything
```bash
# Terminal 1: Start ClickHouse (if not running)
docker start clickhouse-server

# Terminal 2: Run chatbot
cd /path/to/SLO_Chatbot_Latest-v1
source venv/bin/activate
streamlit run app.py
```

### Stop Everything
```bash
# Stop Streamlit (Ctrl+C in terminal)
# Stop ClickHouse
docker stop clickhouse-server
```

### Refresh Data
```bash
# Go to kafka_put
cd /path/to/kafka_put
source venv/bin/activate

# Re-fetch and re-load
python kafka_producer.py
python kafka_to_clickhouse.py
```

### View Logs
```bash
# ClickHouse logs
docker logs clickhouse-server

# Streamlit logs (in terminal where you ran streamlit run app.py)
```

## Environment Variables Reference

### Required
```bash
AWS_ACCESS_KEY_ID=your_key           # AWS access key for Bedrock
AWS_SECRET_ACCESS_KEY=your_secret    # AWS secret key for Bedrock
```

### Optional (defaults work)
```bash
# AWS Configuration
AWS_REGION=ap-south-1                              # Mumbai region
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# ClickHouse Configuration
CLICKHOUSE_HOST=localhost                          # Local Docker
CLICKHOUSE_PORT=8123                              # HTTP port
CLICKHOUSE_USER=default                           # Default user
CLICKHOUSE_PASSWORD=                              # No password

# SLO Thresholds
DEFAULT_ERROR_SLO_THRESHOLD=1.0                   # 1% error rate
DEFAULT_RESPONSE_TIME_SLO=1.0                     # 1 second
DEFAULT_SLO_TARGET_PERCENT=98                     # 98% compliance
ASPIRATIONAL_SLO_TARGET_PERCENT=99                # 99% aspirational

# Degradation Detection
DEGRADATION_WINDOW_DAYS=7                         # 7-day comparison
DEGRADATION_THRESHOLD_PERCENT=20                  # 20% change threshold

# Logging
LOG_LEVEL=INFO                                    # INFO level
```

## Next Steps

Once everything is running:

1. **Try the sample questions** in the chatbot
2. **Read [README.md](README.md)** for full feature documentation
3. **Review [QUICKSTART.md](QUICKSTART.md)** for more examples
4. **Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** if you encounter issues

## Support

If you get stuck:
1. Run the verification checklist above
2. Run `python3 test_clickhouse_comprehensive.py`
3. Check logs: `docker logs clickhouse-server`
4. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Setup complete!** You should now have a fully functional SLO Chatbot running at http://localhost:8501 🎉
