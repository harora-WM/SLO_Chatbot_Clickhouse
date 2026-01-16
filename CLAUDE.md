# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a **complete SLO monitoring system** with two integrated projects:

1. **Data Pipeline** (root directory) - Kafka/ClickHouse ingestion pipeline
2. **SLO Chatbot** (SLO_Chatbot_Latest-v1/) - AI-powered monitoring application

```
Platform API → Kafka → ClickHouse (shared) → SLO Chatbot (Claude Sonnet 4.5)
  (Pipeline writes)                           (Chatbot reads)
```

**Key Architecture Decision:** ClickHouse is the **shared data layer** between both projects. The pipeline writes once, the chatbot reads continuously.

## Quick Start Commands

### Data Pipeline (Root Directory)

```bash
# First-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./clickhouse_setup.sh

# Run pipeline (fetch and load data)
python kafka_producer.py           # Fetch API → Kafka (~10-30s)
python kafka_to_clickhouse.py      # Load Kafka → ClickHouse (Ctrl+C when done, ~30-60s)

# Verify data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759 rows
```

### SLO Chatbot (SLO_Chatbot_Latest-v1/)

```bash
cd SLO_Chatbot_Latest-v1

# First-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add AWS credentials

# Run chatbot
streamlit run app.py
# Access at: http://localhost:8501

# Run tests
python3 test_clickhouse_comprehensive.py
# Expected: 38/38 passed
```

### Common Development Commands

```bash
# Start/stop ClickHouse
docker start clickhouse-server
docker stop clickhouse-server
docker ps | grep clickhouse

# Query ClickHouse
docker exec -it clickhouse-server clickhouse-client
# Or web UI: http://localhost:8123/play

# Re-load data (if schema changes or need fresh data)
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"
python kafka_to_clickhouse.py  # Re-creates table and loads data

# Test Kafka connectivity
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected:', admin._client.cluster.brokers()); admin.close()"
```

## Architecture

### Two-Project Design

**Project 1: Data Pipeline (Root)**
- `keycloak_auth.py` - OAuth2 authentication for Platform API
- `kafka_producer.py` - Fetch transaction data → Kafka (122 messages)
- `kafka_to_clickhouse.py` - Consume Kafka → ClickHouse (8,759 rows)
- **Role:** Data ingestion and ETL
- **Runs:** On-demand or scheduled (not continuously)
- **Output:** Populates ClickHouse `transaction_metrics` table

**Project 2: SLO Chatbot (SLO_Chatbot_Latest-v1/)**
- `app.py` - Streamlit web UI
- `agent/` - Claude Sonnet 4.5 integration via AWS Bedrock
- `analytics/` - 20 analytics functions for SLO monitoring
- `data/database/clickhouse_manager.py` - Read-only ClickHouse client
- **Role:** User-facing monitoring application
- **Runs:** Continuously (Streamlit server)
- **Input:** Queries ClickHouse `transaction_metrics` table

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE (Root)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Keycloak OAuth2                                                │
│       ↓                                                         │
│  Platform API (Watermelon)                                      │
│  - 122 services (transaction endpoints)                         │
│  - 12 days of hourly metrics                                    │
│       ↓                                                         │
│  kafka_producer.py                                              │
│  - Parse nested JSON                                            │
│  - 1 message per service                                        │
│       ↓                                                         │
│  Kafka Topic: services_series_12days                            │
│  - AWS EC2 broker                                               │
│  - 122 messages                                                 │
│       ↓                                                         │
│  kafka_to_clickhouse.py                                         │
│  - Flatten nested arrays                                        │
│  - Batch inserts (5,000 rows)                                   │
│       ↓                                                         │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│            SHARED DATA LAYER (Docker Container)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ClickHouse (localhost:8123)                                    │
│  - Table: transaction_metrics                                   │
│  - 8,759 rows (hourly granularity)                              │
│  - 122 unique services                                          │
│  - 80+ columns (SLO, error budget, percentiles, health)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                 SLO CHATBOT (SLO_Chatbot_Latest-v1/)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Streamlit UI (app.py)                                          │
│       ↓                                                         │
│  User Query: "Which services have high burn rates?"             │
│       ↓                                                         │
│  Claude Sonnet 4.5 (AWS Bedrock)                                │
│  - Decides which tool to call                                   │
│       ↓                                                         │
│  FunctionExecutor (agent/function_tools.py)                     │
│  - Routes to appropriate analytics module                       │
│       ↓                                                         │
│  Analytics Module (analytics/metrics.py, etc.)                  │
│  - Builds SQL query                                             │
│       ↓                                                         │
│  ClickHouseManager (data/database/clickhouse_manager.py)        │
│  - Executes query → Returns DataFrame                           │
│       ↓                                                         │
│  Pandas DataFrame (in-memory, temporary)                        │
│  - Convert to dict                                              │
│  - Serialize to JSON (with DateTimeEncoder)                     │
│       ↓                                                         │
│  Claude Sonnet 4.5                                              │
│  - Generate natural language response                           │
│       ↓                                                         │
│  User sees insights in chat interface                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Critical Understanding: Shared ClickHouse

**IMPORTANT:** Both projects use the **same ClickHouse Docker container** (`clickhouse-server`).

- **Pipeline writes** to ClickHouse (creates/updates `transaction_metrics` table)
- **Chatbot reads** from ClickHouse (queries `transaction_metrics` table)
- **No direct communication** between pipeline and chatbot
- **Data coupling:** Chatbot depends on pipeline having loaded data first
- **Container must be running** for both projects to work

**Typical workflow:**
1. Run pipeline once to load/refresh data
2. Run chatbot continuously to analyze that data
3. Re-run pipeline periodically (daily/weekly) to get fresh data

## Configuration

### Data Pipeline Configuration

**Hardcoded in source:**
- `keycloak_auth.py:91-92` - Credentials for Platform API authentication
- `kafka_producer.py:48-49` - Time range (Dec 31, 2025 → Jan 12, 2026)
- `kafka_producer.py:165-166` - Kafka broker URL (AWS EC2)

**To change time range:** Edit `kafka_producer.py` lines 48-49 (START_TIME, END_TIME in milliseconds)

### SLO Chatbot Configuration

**File:** `SLO_Chatbot_Latest-v1/.env`

```bash
# Required
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Optional (with defaults)
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
DEFAULT_SLO_TARGET_PERCENT=98
ASPIRATIONAL_SLO_TARGET_PERCENT=99
```

### ClickHouse Configuration

**Shared by both projects:**
- Host: `localhost` (Docker container)
- HTTP Port: `8123`
- Native Port: `9000`
- Username: `default`
- Password: (empty)
- Database: `default`
- Table: `transaction_metrics`

## Key Data Structures

### Kafka Message Format

Each of the 122 Kafka messages contains one transaction/service:

```json
{
  "transactionName": "GET /api/endpoint",
  "transactionId": "...",
  "applicationId": 31854,
  "transactionSeries": [
    {
      "timestampStr": "2025-12-31T08:00:00.000Z",
      "timestamp": 1735632000000,
      "totalCount": 1234,
      "errorCount": 5,
      "errorRate": 0.405,
      "avgResponseTime": 123.45,
      "percentile_95": 250.0,
      "percentile_99": 500.0,
      "shortTargetSlo": 98.0,
      "ebConsumedPercent": 45.2,
      "ebHealth": "HEALTHY",
      "aspirationalSlo": 99.0,
      // ... 60+ more fields
    },
    // ... 176-288 hourly records per transaction
  ]
}
```

### ClickHouse Table Schema

**Table:** `transaction_metrics` (~80 columns, MergeTree engine, partitioned by month)

**Critical columns for SLO monitoring:**
- `transaction_name` - Service identifier (e.g., "GET /api/users")
- `timestamp` - DateTime64(3) with millisecond precision
- `total_count`, `error_count`, `success_count` - Request counts
- `error_rate`, `success_rate` - Percentages (0-100)
- `avg_response_time`, `percentile_95`, `percentile_99` - Latency metrics (ms)
- `short_target_slo` - Standard SLO target (98%)
- `aspirational_slo` - Aspirational SLO target (99%)
- `eb_consumed_percent`, `eb_left_percent` - Error budget consumption
- `eb_health`, `response_health`, `timeliness_health` - Health statuses
- `eb_breached`, `response_breached` - Boolean violation flags

**Data characteristics:**
- 8,759 rows (hourly records)
- 122 unique services (transaction_name)
- 12-day range (Dec 31, 2025 → Jan 12, 2026)
- ~72 hours per service on average (varies: 1-288 hours)

## Critical Code Patterns

### Pattern 1: ClickHouse GROUP BY (SLO Chatbot)

**CRITICAL for chatbot analytics:** With hourly data (8,759 rows for 122 services), always GROUP BY only `transaction_name` to avoid duplicates:

```python
# ❌ WRONG - Creates 214+ duplicate services
sql = """
    SELECT transaction_name, eb_health, AVG(error_rate)
    FROM transaction_metrics
    GROUP BY transaction_name, eb_health  -- Multiple fields cause duplicates
"""

# ✅ CORRECT - Returns exactly 122 unique services
sql = """
    SELECT
        transaction_name as service_name,
        any(eb_health) as eb_health_status,        -- Use any() for status fields
        AVG(error_rate) as avg_error_rate,         -- Use AVG() for metrics
        SUM(total_count) as total_requests         -- Use SUM() for counts
    FROM transaction_metrics
    GROUP BY transaction_name  -- ONLY transaction_name
    ORDER BY avg_error_rate DESC
"""
```

### Pattern 2: Message Flattening (Data Pipeline)

**How pipeline flattens nested JSON:**

```python
# In kafka_to_clickhouse.py
for msg_data in kafka_messages:
    transaction_name = msg_data['transactionName']
    transaction_series = msg_data.get('transactionSeries', [])

    # Flatten: each hourly record becomes one ClickHouse row
    for ts_record in transaction_series:
        row = {
            'transaction_name': transaction_name,
            'timestamp': ts_record['timestamp'],
            'total_count': ts_record.get('totalCount', 0),
            'error_rate': ts_record.get('errorRate', 0.0),
            # ... 75+ more fields
        }
        batch.append(row)

        # Batch insert every 5,000 rows
        if len(batch) >= 5000:
            client.insert('transaction_metrics', batch)
            batch = []
```

### Pattern 3: NaN Handling (SLO Chatbot)

**Always use pd.notna() checks before converting to integers:**

```python
# ❌ WRONG - Will crash on NaN
total_requests = int(row['total_requests'])

# ✅ CORRECT - Handles NaN safely
total_req = row['total_requests']
total_requests = int(total_req) if pd.notna(total_req) else 0
```

### Pattern 4: JSON Serialization for Claude (SLO Chatbot)

**Always use DateTimeEncoder when sending results to Claude:**

```python
import json
from agent.claude_client import DateTimeEncoder

# ✅ CORRECT - Handles pandas Timestamp, datetime, numpy types
result = {"timestamp": pd.Timestamp.now(), "value": np.int64(42)}
result_json = json.dumps(result, cls=DateTimeEncoder)

# ❌ WRONG - Will crash with "Object of type Timestamp is not JSON serializable"
result_json = json.dumps(result)
```

## Testing

### Data Pipeline Tests

```bash
# Test authentication
python keycloak_auth.py
# Should save: service_health_response.json

# Test Kafka connectivity
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected:', admin._client.cluster.brokers()); admin.close()"

# Verify ClickHouse data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759

docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(DISTINCT transaction_name) FROM transaction_metrics"
# Expected: 122
```

### SLO Chatbot Tests

```bash
cd SLO_Chatbot_Latest-v1

# Run comprehensive test suite (38 tests)
python3 test_clickhouse_comprehensive.py
# Expected: 38/38 passed

# Test specific component
python3 -c "
from analytics.metrics import MetricsAggregator
from data.database.clickhouse_manager import ClickHouseManager
m = MetricsAggregator(ClickHouseManager())
print('Burn rate results:', len(m.get_services_by_burn_rate(limit=10)))
"
```

## Common Issues

### Issue: ClickHouse Not Running

```bash
# Check status
docker ps | grep clickhouse

# Start if stopped
docker start clickhouse-server

# If doesn't exist, run setup
./clickhouse_setup.sh
```

### Issue: No Data in ClickHouse

```bash
# Verify table exists
docker exec clickhouse-server clickhouse-client --query "SHOW TABLES"

# Check row count
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# If zero, re-run pipeline
python kafka_producer.py
python kafka_to_clickhouse.py
```

### Issue: Schema Changes Required

```bash
# Drop table (WARNING: deletes all data)
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"

# Change KAFKA_GROUP_ID in kafka_to_clickhouse.py (e.g., _v2 → _v3)
# This forces Kafka to re-consume all messages from beginning

# Re-run consumer to recreate table and load data
python kafka_to_clickhouse.py
```

### Issue: Chatbot Returns No Data

**Cause:** ClickHouse not running or empty table

```bash
# 1. Verify ClickHouse is running
docker ps | grep clickhouse

# 2. Check data exists
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# 3. Check time range
docker exec clickhouse-server clickhouse-client --query "SELECT MIN(timestamp), MAX(timestamp) FROM transaction_metrics"
```

### Issue: Kafka Consumer Group Already Processed Messages

**Symptom:** Running `kafka_to_clickhouse.py` doesn't insert any data

**Solution:** Change `KAFKA_GROUP_ID` in kafka_to_clickhouse.py:

```python
# Line ~490 in kafka_to_clickhouse.py
KAFKA_GROUP_ID = 'clickhouse_consumer_group_v3'  # Changed from v2 to v3
```

This forces the consumer to re-read all messages from the beginning.

## Development Workflows

### Workflow 1: Refresh Data

When you need to update the dataset with fresh API data:

```bash
# 1. Re-fetch from Platform API (updates Kafka)
python kafka_producer.py

# 2. Drop existing ClickHouse table
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"

# 3. Change consumer group ID in kafka_to_clickhouse.py
# Edit line ~490: KAFKA_GROUP_ID = 'clickhouse_consumer_group_v3'

# 4. Re-load to ClickHouse (creates new table)
python kafka_to_clickhouse.py
# Press Ctrl+C after all 122 messages processed

# 5. Verify data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# 6. Chatbot will see new data immediately (no restart needed)
```

### Workflow 2: Add New Analytics Function (Chatbot)

```bash
cd SLO_Chatbot_Latest-v1

# 1. Add method to analytics module
# Edit: analytics/metrics.py (or slo_calculator.py, trend_analyzer.py, etc.)

# 2. Add wrapper in FunctionExecutor
# Edit: agent/function_tools.py
#   - Add method to FunctionExecutor class
#   - Register in function_map dict

# 3. Add tool definition
# Edit: agent/function_tools.py
#   - Add to TOOLS list with schema

# 4. Test the function
python3 -c "
from analytics.metrics import MetricsAggregator
from data.database.clickhouse_manager import ClickHouseManager
m = MetricsAggregator(ClickHouseManager())
result = m.your_new_function()
print('Result:', result)
"

# 5. Run comprehensive tests
python3 test_clickhouse_comprehensive.py

# 6. Restart Streamlit to pick up changes
# Ctrl+C, then: streamlit run app.py
```

### Workflow 3: Query ClickHouse Directly

```bash
# Interactive mode
docker exec -it clickhouse-server clickhouse-client

# Single query
docker exec clickhouse-server clickhouse-client --query "
SELECT
    transaction_name,
    AVG(error_rate) as avg_error_rate
FROM transaction_metrics
GROUP BY transaction_name
ORDER BY avg_error_rate DESC
LIMIT 10
"

# Web UI
# Open: http://localhost:8123/play
```

## Project-Specific Documentation

For detailed documentation on each project:

- **Data Pipeline:** See this file (you're reading it)
- **SLO Chatbot:** See `SLO_Chatbot_Latest-v1/CLAUDE.md`
- **Kafka Viewer:** See `OFFSET_EXPLORER_GUIDE.md`
- **Chatbot User Guide:** See `SLO_Chatbot_Latest-v1/README.md`
- **Quick Examples:** See `SLO_Chatbot_Latest-v1/QUICKSTART.md`

## Known Issues

1. **SSL Verification Disabled** - Pipeline uses `verify=False` for HTTPS requests to work with sandbox certificates. Enable for production.

2. **Hardcoded Credentials** - Platform API credentials embedded in `keycloak_auth.py`. Consider environment variables for production.

3. **Fixed Time Range** - Pipeline hardcodes Dec 31, 2025 → Jan 12, 2026. Update `kafka_producer.py:48-49` for different ranges.

4. **WSL2 Docker Dependency** - ClickHouse setup assumes WSL2 with Docker Desktop integration on Windows.

5. **Streamlit Cache Issues** - If chatbot doesn't reflect code changes, clear Python cache: `find . -type d -name "__pycache__" -exec rm -r {} +`
