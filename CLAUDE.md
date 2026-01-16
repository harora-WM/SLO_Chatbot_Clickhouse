# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a **complete SLO monitoring system** with a clean, organized structure:

```
slo-monitoring/
├── pipeline/          # Data ingestion (Kafka → ClickHouse)
├── chatbot/           # AI-powered monitoring (Claude Sonnet 4.5)
├── docs/              # Shared documentation
├── requirements.txt   # Unified dependencies
└── README.md          # User guide
```

**Architecture:** Pipeline writes to ClickHouse (shared data layer), Chatbot reads from ClickHouse.

## Quick Start Commands

### Data Pipeline

```bash
# From repository root
./pipeline/clickhouse_setup.sh      # Setup ClickHouse (first time only)
python pipeline/kafka_producer.py    # Fetch API → Kafka (~10-30s)
python pipeline/kafka_to_clickhouse.py  # Load Kafka → ClickHouse (~30-60s, Ctrl+C when done)

# Verify
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759
```

### SLO Chatbot

```bash
# From repository root
cd chatbot
cp .env.example .env  # Add AWS credentials
streamlit run app.py  # Access at http://localhost:8501

# Test
python test_clickhouse_comprehensive.py  # Expected: 38/38 passed
```

### Common Commands

```bash
# ClickHouse management
docker start clickhouse-server
docker ps | grep clickhouse
docker exec -it clickhouse-server clickhouse-client
# Web UI: http://localhost:8123/play

# Install dependencies (unified)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Kafka connectivity test
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected:', admin._client.cluster.brokers())"
```

## Architecture

### Project Structure

**pipeline/** - Data ingestion pipeline
- `keycloak_auth.py` - OAuth2 authentication for Platform API
- `kafka_producer.py` - Fetch API data → Kafka (122 messages)
- `kafka_to_clickhouse.py` - Consume Kafka → ClickHouse (8,759 rows)
- `clickhouse_setup.sh` - Docker setup script
- **Runs:** On-demand or scheduled
- **Output:** Populates `transaction_metrics` table

**chatbot/** - SLO monitoring application
- `app.py` - Streamlit web UI
- `agent/` - Claude Sonnet 4.5 integration (AWS Bedrock)
- `analytics/` - 20 analytics functions (SLO, burn rate, degradation, predictions)
- `data/database/clickhouse_manager.py` - Read-only ClickHouse client
- `utils/` - Config, logging
- **Runs:** Continuously (Streamlit server)
- **Input:** Queries ClickHouse

**docs/** - Shared documentation
- `OFFSET_EXPLORER_GUIDE.md` - Kafka topic viewer guide

### Data Flow

```
Platform API (Keycloak OAuth2)
    ↓
pipeline/kafka_producer.py (Parse nested JSON, 122 services)
    ↓
Kafka Topic: services_series_12days (AWS EC2 broker)
    ↓
pipeline/kafka_to_clickhouse.py (Flatten arrays, batch insert)
    ↓
ClickHouse: transaction_metrics (8,759 rows, 80+ columns)
    ↓
chatbot/analytics/ (SQL queries, DataFrames)
    ↓
Claude Sonnet 4.5 (Natural language responses)
    ↓
User (Streamlit UI)
```

### Critical Understanding: Shared ClickHouse

**IMPORTANT:** Both projects use the **same ClickHouse Docker container**.

- Pipeline **writes** to ClickHouse (creates/updates table)
- Chatbot **reads** from ClickHouse (queries only)
- **No direct communication** between projects
- **Data coupling:** Chatbot depends on pipeline having loaded data first
- **Container must be running** for both to work

**Typical workflow:**
1. Run pipeline once to load/refresh data
2. Run chatbot continuously to analyze data
3. Re-run pipeline periodically for fresh data

## Configuration

### Data Pipeline

**Files:** `pipeline/kafka_producer.py`, `pipeline/keycloak_auth.py`

**Hardcoded configuration:**
- Credentials: `keycloak_auth.py:91-92` (username/password for Platform API)
- Time range: `kafka_producer.py:48-49` (Dec 31, 2025 → Jan 12, 2026)
- Kafka broker: `kafka_producer.py:165-166` (AWS EC2 instance)

**To change time range:** Edit `kafka_producer.py` lines 48-49 (START_TIME, END_TIME in milliseconds)

### SLO Chatbot

**File:** `chatbot/.env`

```bash
# Required
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Optional (defaults provided)
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
DEFAULT_SLO_TARGET_PERCENT=98
ASPIRATIONAL_SLO_TARGET_PERCENT=99
```

### ClickHouse (Shared)

- Host: `localhost` (Docker container)
- HTTP Port: `8123`
- Native Port: `9000`
- Username: `default`
- Password: (empty)
- Table: `transaction_metrics`

## Critical Code Patterns

### Pattern 1: ClickHouse GROUP BY (Chatbot Analytics)

**CRITICAL:** With hourly data (8,759 rows for 122 services), always GROUP BY only `transaction_name`:

```python
# ❌ WRONG - Creates duplicates
sql = """
    SELECT transaction_name, eb_health, AVG(error_rate)
    FROM transaction_metrics
    GROUP BY transaction_name, eb_health  -- Multiple fields
"""

# ✅ CORRECT - Returns exactly 122 services
sql = """
    SELECT
        transaction_name as service_name,
        any(eb_health) as eb_health_status,      -- Use any() for status
        AVG(error_rate) as avg_error_rate,       -- Use AVG() for metrics
        SUM(total_count) as total_requests       -- Use SUM() for counts
    FROM transaction_metrics
    GROUP BY transaction_name  -- ONLY transaction_name
"""
```

**Why:** Each service has ~72 hourly rows. Grouping by multiple fields creates one row per unique combination, resulting in 214+ rows instead of 122.

### Pattern 2: Message Flattening (Pipeline)

**How pipeline converts nested JSON to flat rows:**

```python
# In pipeline/kafka_to_clickhouse.py
for msg_data in kafka_messages:
    transaction_name = msg_data['transactionName']
    transaction_series = msg_data.get('transactionSeries', [])

    # Flatten: each hourly record → one ClickHouse row
    for ts_record in transaction_series:
        row = {
            'transaction_name': transaction_name,
            'timestamp': ts_record['timestamp'],
            'total_count': ts_record.get('totalCount', 0),
            # ... 75+ more fields
        }
        batch.append(row)

        if len(batch) >= 5000:
            client.insert('transaction_metrics', batch)
            batch = []
```

### Pattern 3: NaN Handling (Chatbot)

**Always use pd.notna() before type conversions:**

```python
# ❌ WRONG
total_requests = int(row['total_requests'])

# ✅ CORRECT
total_req = row['total_requests']
total_requests = int(total_req) if pd.notna(total_req) else 0
```

### Pattern 4: JSON Serialization for Claude (Chatbot)

**Always use DateTimeEncoder:**

```python
import json
from agent.claude_client import DateTimeEncoder

# ✅ CORRECT - Handles pandas Timestamp, datetime, numpy types
result = {"timestamp": pd.Timestamp.now(), "value": np.int64(42)}
result_json = json.dumps(result, cls=DateTimeEncoder)
```

## Key Data Structures

### Kafka Message Format

Each of 122 messages contains one service with nested time series:

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
      "errorRate": 0.405,
      "avgResponseTime": 123.45,
      "percentile_95": 250.0,
      "shortTargetSlo": 98.0,
      "ebConsumedPercent": 45.2,
      // ... 60+ more fields
    },
    // ... 176-288 hourly records per service
  ]
}
```

### ClickHouse Table Schema

**Table:** `transaction_metrics` (~80 columns, MergeTree engine)

**Key columns:**
- `transaction_name` - Service identifier
- `timestamp` - DateTime64(3)
- `total_count`, `error_count`, `success_count`
- `error_rate`, `success_rate` (0-100)
- `avg_response_time`, `percentile_95`, `percentile_99` (ms)
- `short_target_slo` (98%), `aspirational_slo` (99%)
- `eb_consumed_percent`, `eb_left_percent`
- `eb_health`, `response_health`, `timeliness_health`
- `eb_breached`, `response_breached` (booleans)

**Data characteristics:**
- 8,759 rows (hourly records)
- 122 unique services
- 12-day range (Dec 31, 2025 → Jan 12, 2026)
- ~72 hours per service average (varies: 1-288)

## Testing

### Pipeline Tests

```bash
# Test authentication
python pipeline/keycloak_auth.py
# Output: service_health_response.json

# Test Kafka connectivity
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected')"

# Verify ClickHouse data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"  # Expected: 8759
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(DISTINCT transaction_name) FROM transaction_metrics"  # Expected: 122
```

### Chatbot Tests

```bash
cd chatbot

# Comprehensive test suite (38 tests)
python test_clickhouse_comprehensive.py
# Expected: 38/38 passed

# Test specific function
python3 -c "
from analytics.metrics import MetricsAggregator
from data.database.clickhouse_manager import ClickHouseManager
m = MetricsAggregator(ClickHouseManager())
print(len(m.get_services_by_burn_rate(limit=10)))
"
```

## Common Issues

### Issue: ClickHouse Not Running

```bash
docker ps | grep clickhouse          # Check status
docker start clickhouse-server       # Start if stopped
./pipeline/clickhouse_setup.sh       # Setup if doesn't exist
```

### Issue: No Data in ClickHouse

```bash
# Check table exists
docker exec clickhouse-server clickhouse-client --query "SHOW TABLES"

# Check row count
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# If zero, re-run pipeline
python pipeline/kafka_producer.py
python pipeline/kafka_to_clickhouse.py
```

### Issue: Schema Changes Required

```bash
# Drop table (WARNING: deletes all data)
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"

# Change consumer group in pipeline/kafka_to_clickhouse.py (~line 490)
# KAFKA_GROUP_ID = 'clickhouse_consumer_group_v3'  # Increment version

# Re-run to recreate table
python pipeline/kafka_to_clickhouse.py
```

### Issue: Kafka Consumer Already Processed Messages

**Symptom:** `kafka_to_clickhouse.py` doesn't insert data

**Solution:** Change `KAFKA_GROUP_ID` in `pipeline/kafka_to_clickhouse.py:490`:

```python
KAFKA_GROUP_ID = 'clickhouse_consumer_group_v3'  # Was v2, now v3
```

This forces re-consumption from beginning.

## Development Workflows

### Workflow 1: Refresh Data

```bash
# 1. Re-fetch from Platform API
python pipeline/kafka_producer.py

# 2. Drop existing table
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"

# 3. Change consumer group ID (if needed)
# Edit pipeline/kafka_to_clickhouse.py:490

# 4. Re-load to ClickHouse
python pipeline/kafka_to_clickhouse.py  # Ctrl+C after 122 messages

# 5. Verify
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# 6. Chatbot sees new data immediately (no restart needed)
```

### Workflow 2: Add New Analytics Function (Chatbot)

```bash
cd chatbot

# 1. Add method to analytics module
# Edit: analytics/metrics.py (or slo_calculator.py, etc.)

# 2. Add wrapper in FunctionExecutor
# Edit: agent/function_tools.py
#   - Add method to FunctionExecutor class
#   - Register in function_map dict
#   - Add to TOOLS list with schema

# 3. Test
python3 -c "
from analytics.metrics import MetricsAggregator
from data.database.clickhouse_manager import ClickHouseManager
m = MetricsAggregator(ClickHouseManager())
result = m.your_new_function()
print(result)
"

# 4. Run tests
python test_clickhouse_comprehensive.py

# 5. Restart Streamlit
# Ctrl+C, then: streamlit run app.py
```

### Workflow 3: Query ClickHouse Directly

```bash
# Interactive mode
docker exec -it clickhouse-server clickhouse-client

# Single query
docker exec clickhouse-server clickhouse-client --query "
SELECT transaction_name, AVG(error_rate) as avg_error_rate
FROM transaction_metrics
GROUP BY transaction_name
ORDER BY avg_error_rate DESC
LIMIT 10
"

# Web UI
# Open: http://localhost:8123/play
```

## File Organization

### Where to Find Things

**Pipeline code:** `pipeline/`
- All data ingestion logic
- Kafka producer/consumer
- ClickHouse setup script

**Chatbot code:** `chatbot/`
- Streamlit UI
- Claude integration
- Analytics functions
- Tests

**Documentation:**
- User guide: `README.md` (root)
- Developer guide: `CLAUDE.md` (this file)
- Kafka viewer: `docs/OFFSET_EXPLORER_GUIDE.md`
- Chatbot details: `chatbot/README.md`, `chatbot/QUICKSTART.md`

**Configuration:**
- Dependencies: `requirements.txt` (root, unified)
- Pipeline config: Hardcoded in `pipeline/*.py`
- Chatbot config: `chatbot/.env`

**Data files:** (git-ignored)
- Debug files: `data/` directory
- Temporary files: Filtered by `.gitignore`

## Known Issues

1. **SSL Verification Disabled** - Pipeline uses `verify=False` for sandbox certificates
2. **Hardcoded Credentials** - Platform API credentials in `pipeline/keycloak_auth.py:91-92`
3. **Fixed Time Range** - Hardcoded Dec 31, 2025 → Jan 12, 2026 in `pipeline/kafka_producer.py:48-49`
4. **WSL2 Docker Dependency** - ClickHouse setup assumes WSL2 with Docker Desktop on Windows
5. **Streamlit Cache** - If code changes don't reflect, clear: `find . -type d -name "__pycache__" -exec rm -r {} +`

## Project-Specific Documentation

For detailed documentation:

- **Pipeline:** See inline comments in `pipeline/*.py`
- **Chatbot:** See `chatbot/CLAUDE.md` for detailed patterns and `chatbot/README.md` for user guide
- **Architecture:** See `README.md` for system overview
- **Migration:** See `chatbot/CLICKHOUSE_MIGRATION.md` and `chatbot/MIGRATION_COMPLETE.md`
