# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data ingestion and analytics pipeline that fetches transaction summary data from a Watermelon monitoring API, publishes it to Kafka, and loads it into ClickHouse for analysis. The pipeline authenticates via Keycloak, retrieves hourly time-series metrics, streams individual records to Kafka, and flattens nested data into ClickHouse tables.

## Quick Start

```bash
# Setup (first time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./clickhouse_setup.sh

# Run pipeline (requires Docker Desktop running on WSL2)
python kafka_producer.py           # Optional: re-fetch data from API (takes ~10-30s)
python kafka_to_clickhouse.py      # Load data to ClickHouse (Ctrl+C when done, ~30-60s)

# Query data
# Open browser: http://localhost:8123/play
# Or use CLI: docker exec -it clickhouse-server clickhouse-client
```

## Architecture

### Three-Module Design

1. **keycloak_auth.py** - Authentication module
   - Handles Keycloak OAuth2 authentication using password grant flow
   - Exports `get_access_token()` function used by other modules
   - Includes a standalone test mode that fetches sample API data when run directly
   - Disables SSL verification for sandbox environment

2. **kafka_producer.py** - Data ingestion pipeline
   - Imports authentication from `keycloak_auth.py`
   - Fetches transaction summary data from the Error Budget Statistics Service API
   - Parses response into transaction objects (each with nested hourly time-series data)
   - Publishes each transaction as a separate Kafka message (1 message per transaction/service endpoint)
   - Automatically detects response structure (handles `data`, `records`, `series` keys, or raw arrays)

3. **kafka_to_clickhouse.py** - Analytics data loader
   - Consumes messages from Kafka topic `services_series_12days`
   - Flattens nested `transactionSeries` arrays (each hourly record becomes one ClickHouse row)
   - Stores ALL ~80 fields from Kafka including performance metrics, SLO (standard + aspirational), health indicators, severity codes, and percentiles
   - Batches inserts for efficiency (5,000 rows per batch)
   - Creates ClickHouse table automatically on first run

### Data Flow

```
Keycloak Auth → API Fetch (12 days) → Parse → Kafka Topic → Flatten → ClickHouse
                                       (122 messages)        (21K-35K rows)
```

**Complete pipeline:**
1. Authenticate with Keycloak OAuth2
2. Fetch 122 transaction objects from API (each with 176-288 hourly data points)
3. Publish to Kafka (1 message per transaction)
4. Consume from Kafka and flatten nested arrays
5. Insert into ClickHouse for time-series analytics

**Important**: Each Kafka message represents ONE transaction/service endpoint, containing ALL its hourly data points (varies from 1 to 288 hours depending on service activity).

### API Response Structure and Message Grouping

The API returns an array of 122 transaction objects (one per unique API endpoint/service):

```json
[
  {
    "transactionName": "GET /api/endpoint1",
    "transactionSeries": [
      {"timestampStr": "...", "key": "...", "sumResponseTime": ..., ...},  // Hour 1
      {"timestampStr": "...", "key": "...", "sumResponseTime": ..., ...},  // Hour 2
      // ... variable number of hours (1-288) depending on service activity
    ]
  },
  // ... 121 more transactions
]
```

**Message Grouping Logic** (kafka_producer.py:110-137):
- Code detects the response is a list and treats it as an array of records (kafka_producer.py:110-111)
- Each transaction object is sent as 1 Kafka message (kafka_producer.py:126-149)
- Result: **122 Kafka messages** (one per transaction/service)
- Each message contains the complete `transactionSeries` array with all hourly metrics for that service

**Why variable hourly data points?**
- Services active 24/7: ~288 hourly data points (full 12-day span)
- Intermittently used services: 1-287 data points (only hours with activity)
- The API only returns data points for hours when the service was actually used

## Environment Setup

### Dependencies (requirements.txt)
- `requests==2.31.0` - HTTP client
- `urllib3==2.1.0` - Low-level HTTP utilities
- `kafka-python-ng==2.2.3` - Kafka client (use `kafka-python-ng`, NOT `kafka-python` for Python 3.12+ compatibility)
- `clickhouse-connect==0.7.0` - ClickHouse Python client for data loading

### Setup Commands
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### Step 1: Authentication Test
```bash
python keycloak_auth.py
```
Tests Keycloak authentication and saves response to `service_health_response.json`.

### Step 2: Kafka Data Ingestion
```bash
python kafka_producer.py
```
Runs the ingestion pipeline: authenticate → fetch → parse → publish to Kafka.
Saves debug copy to `api_response_debug.json`.

### Step 3: ClickHouse Setup

**First Time Setup:**
```bash
./clickhouse_setup.sh
```
Sets up ClickHouse using Docker (ports 8123 for HTTP, 9000 for native protocol).
Verifies installation and displays connection details.

**Important for WSL2 Users:**
- Ensure Docker Desktop is running on Windows
- Enable WSL2 integration: Docker Desktop → Settings → Resources → WSL Integration → Enable for your distro
- Verify Docker is accessible: `docker --version`

**Restarting After System Shutdown:**
If Docker Desktop is closed or system restarted, simply start the existing container:
```bash
docker start clickhouse-server
```
Or re-run the setup script (it will detect and start the existing container):
```bash
./clickhouse_setup.sh
```

**Data Persistence:**
All data in ClickHouse persists across container restarts. Data is only lost if you explicitly delete the container (`docker rm -f clickhouse-server`).

### Step 4: Load Data into ClickHouse
```bash
python kafka_to_clickhouse.py
```
Consumes from Kafka and loads flattened data into ClickHouse.

**Expected Behavior:**
- Processes all available Kafka messages from topic `services_series_12days`
- Displays progress for each message with time-series record count
- Inserts data in batches of 5,000 rows
- After consuming all messages, waits indefinitely for new messages (this is normal streaming consumer behavior)
- Press **Ctrl+C** to stop the consumer gracefully (it will flush remaining buffered rows before exiting)

**Expected Output:**
- 122 Kafka messages processed (one per transaction/service endpoint)
- Total rows inserted varies based on service activity (typically 8,000-35,000 rows)
- Final summary shows: messages processed, time-series records extracted, ClickHouse rows inserted

**If Schema Changes or Need to Re-load Data:**
If the table schema needs to be updated (e.g., adding/removing columns), drop and recreate:
```bash
# Drop existing table
docker exec clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"

# Re-run consumer to create new table with updated schema
python kafka_to_clickhouse.py
```
Note: If Kafka consumer group has already processed messages, change the `KAFKA_GROUP_ID` in kafka_to_clickhouse.py (e.g., from `_v2` to `_v3`) to re-consume all messages from the beginning.

## Configuration

### Hardcoded Credentials (keycloak_auth.py:91-92)
- Username: `wmadmin`
- Password: `WM@Dm1n@#2024!!$`
- Keycloak URL: `https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token`

### API Endpoint (kafka_producer.py:38-46)
- URL: `https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/transactions/summary/series/all`
- Parameters:
  - `application_id`: 31854 (WMPlatform)
  - `range`: CUSTOM
  - `start_time`: 1767205800000 (Dec 31, 2025, 07:30:00 UTC - hardcoded for this dataset)
  - `end_time`: 1768242540000 (Jan 12, 2026, 16:29:00 UTC - hardcoded for this dataset)
  - `index`: HOURLY
  - **Note**: These timestamps are hardcoded in kafka_producer.py:48-49. Update them to fetch data for different time ranges.

### Kafka Configuration (kafka_producer.py:165-166)
- Bootstrap servers: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092` (AWS EC2 broker)
- Broker version: Kafka 2.6.0
- Topic: `services_series_12days`
- Producer settings: `acks='all'`, 3 retries, max 1 in-flight request

### ClickHouse Configuration (kafka_to_clickhouse.py:486-494)
- Host: `localhost` (Docker container)
- HTTP Port: `8123`
- Native Port: `9000`
- Username: `default`
- Password: (empty)
- Consumer group: `clickhouse_consumer_group_v2` (changed from v1 to re-consume all messages with new schema)
- Batch size: 5,000 rows per insert

## Viewing Messages in Kafka

### Using Offset Explorer (Recommended)
See `OFFSET_EXPLORER_GUIDE.md` for detailed instructions.

**Quick setup:**
1. Download Offset Explorer from https://www.kafkatool.com/download.html (use Windows version for WSL2)
2. Add connection:
   - Cluster name: `AWS Kafka Cluster`
   - Kafka version: `2.6`
   - Bootstrap servers: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092`
3. Navigate to Topics → `services_series_12days` → Data tab → Click play button
4. View all 122 messages with their transaction data

### Using Python Consumer
```bash
# Activate virtual environment first
source venv/bin/activate

# Test connectivity
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected:', admin._client.cluster.brokers()); admin.close()"
```

## Querying Data in ClickHouse

### ClickHouse Table Schema

**Table:** `transaction_metrics` (~80 columns, MergeTree engine, partitioned by month)

**All fields from Kafka data (matching JSON structure exactly):**

**Transaction Identifiers:**
- `transaction_name`, `transaction_id`, `application_id`, `application_name`, `alias`

**Timestamps:**
- `timestamp` (DateTime64(3)), `timestamp_str`, `key`

**Metadata:**
- `timezone`, `no_data_found`, `index_type`, `sre_product`

**Performance Metrics:**
- `sum_response_time`, `avg_response_time`, `total_count`, `success_count`, `error_count`
- `success_rate`, `error_rate`, `total_data_points`

**SLO Metrics (Standard):**
- `short_target_slo`, `eb_allocated_percent`, `eb_allocated_count`, `eb_consumed_percent`
- `eb_consumed_count`, `eb_actual_consumed_percent`, `eb_left_percent`, `eb_left_count`

**SLO Metrics (Aspirational):**
- `aspirational_slo`, `aspirational_eb_allocated_percent`, `aspirational_eb_allocated_count`
- `aspirational_eb_consumed_percent`, `aspirational_eb_consumed_count`
- `aspirational_eb_actual_consumed_percent`, `aspirational_eb_left_percent`, `aspirational_eb_left_count`

**Response Metrics (Standard):**
- `response_breach_count`, `response_error_rate`, `response_success_rate`, `response_slo`
- `response_target_percent`, `response_allocated_percent`, `response_allocated_count`
- `response_consumed_percent`, `response_consumed_count`, `response_actual_consumed_percent`
- `response_left_percent`, `response_left_count`

**Response Metrics (Aspirational):**
- `aspirational_response_slo`, `aspirational_response_target_percent`
- `aspirational_response_allocated_percent`, `aspirational_response_allocated_count`
- `aspirational_response_consumed_percent`, `aspirational_response_consumed_count`
- `aspirational_response_actual_consumed_percent`, `aspirational_response_left_percent`
- `aspirational_response_left_count`

**Timeliness Metrics:**
- `timeliness_consumed_percent`, `aspirational_timeliness_consumed_percent`

**Health Indicators:**
- `timeliness_health`, `response_health`, `eb_health`
- `aspirational_response_health`, `aspirational_eb_health`

**Severity Indicators (color codes for UI):**
- `timeliness_severity`, `response_severity`, `eb_severity`
- `aspirational_response_severity`, `aspirational_eb_severity`

**Breach Flags:**
- `eb_breached`, `response_breached`, `eb_or_response_breached`

**Response Time Percentiles:**
- `percentile_25`, `percentile_50`, `percentile_75`, `percentile_80`, `percentile_85`
- `percentile_90`, `percentile_95`, `percentile_99`

**Auto-generated:**
- `ingestion_time` - Timestamp when row was inserted into ClickHouse

### Accessing ClickHouse

**Web UI (Recommended):**
Open in browser: `http://localhost:8123/play`
- No authentication required (default user with empty password)
- Interactive query interface with syntax highlighting
- View query results in table format
- Note: Large result sets (1000+ rows) are paginated

**Command-Line Client:**
```bash
# Interactive mode
docker exec -it clickhouse-server clickhouse-client

# Single query (use when running from scripts/automation)
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
```

**Common Queries:**
```sql
-- Verify data loaded
SELECT COUNT(*) FROM transaction_metrics;

-- View table structure
SHOW CREATE TABLE transaction_metrics;
DESCRIBE transaction_metrics;

-- Count unique transactions
SELECT COUNT(DISTINCT transaction_name) FROM transaction_metrics;
```

### Common Query Examples

**Row count by transaction:**
```sql
SELECT
    transaction_name,
    COUNT(*) as row_count
FROM transaction_metrics
GROUP BY transaction_name
ORDER BY row_count DESC
LIMIT 10;
```

**Average response time by transaction (last 7 days):**
```sql
SELECT
    transaction_name,
    AVG(avg_response_time) as avg_ms,
    COUNT(*) as data_points
FROM transaction_metrics
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY transaction_name
ORDER BY avg_ms DESC
LIMIT 10;
```

**Hourly aggregation with percentiles:**
```sql
SELECT
    toStartOfHour(timestamp) as hour,
    transaction_name,
    AVG(avg_response_time) as avg_response,
    AVG(percentile_95) as p95,
    AVG(percentile_99) as p99,
    SUM(total_count) as total_requests
FROM transaction_metrics
WHERE transaction_name = 'GET /api/endpoint'
GROUP BY hour, transaction_name
ORDER BY hour DESC
LIMIT 24;
```

**Error budget health overview:**
```sql
SELECT
    eb_health,
    COUNT(*) as count,
    AVG(eb_consumed_percent) as avg_consumed
FROM transaction_metrics
GROUP BY eb_health
ORDER BY count DESC;
```

**Transactions with high error rates:**
```sql
SELECT
    transaction_name,
    AVG(error_rate) as avg_error_rate,
    MAX(error_rate) as max_error_rate,
    COUNT(*) as occurrences
FROM transaction_metrics
WHERE error_rate > 0
GROUP BY transaction_name
HAVING avg_error_rate > 1.0
ORDER BY avg_error_rate DESC;
```

### Using Python Client
```python
import clickhouse_connect

# Connect
client = clickhouse_connect.get_client(host='localhost', port=8123)

# Query
result = client.query('SELECT COUNT(*) FROM transaction_metrics')
print(f"Total rows: {result.result_rows[0][0]:,}")

# Query with DataFrame
df = client.query_df('SELECT * FROM transaction_metrics LIMIT 100')
print(df.head())
```

### Useful ClickHouse Commands
```bash
# View database size
docker exec -it clickhouse-server clickhouse-client --query "SELECT formatReadableSize(sum(bytes)) as size FROM system.parts WHERE table = 'transaction_metrics'"

# View partition info
docker exec -it clickhouse-server clickhouse-client --query "SELECT partition, count() as parts, formatReadableSize(sum(bytes)) as size FROM system.parts WHERE table = 'transaction_metrics' GROUP BY partition ORDER BY partition"

# Export all data to file (bypasses web UI pagination)
docker exec clickhouse-server clickhouse-client --query "SELECT * FROM transaction_metrics" > all_rows.txt

# Export to CSV format
docker exec clickhouse-server clickhouse-client --query "SELECT * FROM transaction_metrics FORMAT CSV" > data.csv

# Export to JSON format
docker exec clickhouse-server clickhouse-client --query "SELECT * FROM transaction_metrics FORMAT JSONEachRow" > data.json

# Drop table (careful!)
docker exec -it clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"
```

**Note on Web UI Pagination:** The web UI at `http://localhost:8123/play` only displays the first ~1,000 rows even if your query returns more. Use the export commands above or the Python client to access all rows.

## Expected Pipeline Output

### Kafka Producer (`python kafka_producer.py`)
- Authentication success message
- API fetch confirmation with 122 transaction records
- Debug file saved: `api_response_debug.json` (~28MB)
- Kafka publishing: 122 messages sent (one per transaction/service)
- Total time: ~10-30 seconds depending on network

### ClickHouse Consumer (`python kafka_to_clickhouse.py`)
- Kafka connection established to topic `services_series_12days`
- ClickHouse connection confirmed
- Table `transaction_metrics` created (if first run)
- 122 Kafka messages processed, each showing:
  - Transaction name (e.g., "GET /api/endpoint")
  - Number of time-series records extracted (176-288 per transaction)
- Batch inserts every 5,000 rows
- Final summary:
  - Total messages: 122
  - Total time-series records: ~21,000-35,000
  - Total ClickHouse rows inserted: ~21,000-35,000
- Total time: ~30-60 seconds depending on data volume

## Docker Management

**Check ClickHouse Status:**
```bash
docker ps                           # View running containers
docker ps -a                        # View all containers (including stopped)
docker logs clickhouse-server       # View ClickHouse logs
```

**Start/Stop ClickHouse:**
```bash
docker start clickhouse-server      # Start existing container
docker stop clickhouse-server       # Stop running container
docker restart clickhouse-server    # Restart container
```

**Remove ClickHouse (WARNING: Deletes all data):**
```bash
docker rm -f clickhouse-server      # Remove container and all data
```

**Troubleshooting:**
- If ClickHouse won't start: Check Docker Desktop is running on Windows
- If ports are in use: Ensure no other services are using ports 8123 or 9000
- If authentication fails: The setup script configures ClickHouse with empty password for default user

## Known Issues

1. **SSL Verification Disabled** - Both modules use `verify=False` for HTTPS requests to work with sandbox certificates. This should be enabled for production with proper certificate validation.

2. **Hardcoded Credentials** - Authentication credentials are embedded in source code. Consider using environment variables or secret management for production.

3. **ClickHouse Version Compatibility** - The setup script has been updated (line 47) to include `-e CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1` to support ClickHouse v25+ which requires explicit authentication configuration.
