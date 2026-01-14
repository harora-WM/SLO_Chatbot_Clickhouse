# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a data ingestion and analytics pipeline that fetches transaction summary data from a Watermelon monitoring API, publishes it to Kafka, and loads it into ClickHouse for analysis. The pipeline authenticates via Keycloak, retrieves hourly time-series metrics, streams individual records to Kafka, and flattens nested data into ClickHouse tables.

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
   - Parses response into individual records (hourly time-series data points)
   - Publishes each record as a separate Kafka message with timestamp as key
   - Automatically detects response structure (handles `data`, `records`, `series` keys, or raw arrays)

3. **kafka_to_clickhouse.py** - Analytics data loader
   - Consumes messages from Kafka topic `services_series_12days`
   - Flattens nested `transactionSeries` arrays (each hourly record becomes one ClickHouse row)
   - Handles 35 columns of metrics including performance, SLO, health indicators, and percentiles
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

### Step 3: ClickHouse Setup (First Time Only)
```bash
./clickhouse_setup.sh
```
Sets up ClickHouse using Docker (ports 8123 for HTTP, 9000 for native protocol).
Verifies installation and displays connection details.

### Step 4: Load Data into ClickHouse
```bash
python kafka_to_clickhouse.py
```
Consumes from Kafka and loads flattened data into ClickHouse.
Expected output:
- 122 Kafka messages processed
- ~21,000-35,000 rows inserted into `transaction_metrics` table
- Progress displayed per message with hourly record count

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
  - `start_time`: 1767205800000 (Dec 31, 2025, 07:30:00 UTC)
  - `end_time`: 1768242540000 (Jan 12, 2026, 16:29:00 UTC)
  - `index`: HOURLY

### Kafka Configuration (kafka_producer.py:165-166)
- Bootstrap servers: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092` (AWS EC2 broker)
- Broker version: Kafka 2.6.0
- Topic: `services_series_12days`
- Producer settings: `acks='all'`, 3 retries, max 1 in-flight request

### ClickHouse Configuration (kafka_to_clickhouse.py:233-238)
- Host: `localhost` (Docker container)
- HTTP Port: `8123`
- Native Port: `9000`
- Username: `default`
- Password: (empty)
- Consumer group: `clickhouse_consumer_group`
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

**Table:** `transaction_metrics` (35 columns, MergeTree engine, partitioned by month)

**Key columns:**
- `transaction_name` - API endpoint identifier (e.g., "GET /api/users")
- `timestamp` - DateTime64(3) when metric was recorded
- `avg_response_time` - Average response time in milliseconds
- `total_count` - Total number of requests
- `success_rate`, `error_rate` - Request success/error rates
- `eb_allocated_percent`, `eb_consumed_percent` - Error budget metrics
- `percentile_25` through `percentile_99` - Response time percentiles
- `timeliness_health`, `response_health`, `eb_health` - Health status indicators

### Interactive ClickHouse Client
```bash
# Access ClickHouse SQL client
docker exec -it clickhouse-server clickhouse-client

# Once inside, run SQL queries:
SELECT COUNT(*) FROM transaction_metrics;
SHOW CREATE TABLE transaction_metrics;
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

# Drop table (careful!)
docker exec -it clickhouse-server clickhouse-client --query "DROP TABLE IF EXISTS transaction_metrics"
```

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

## Known Issues

1. **SSL Verification Disabled** - Both modules use `verify=False` for HTTPS requests to work with sandbox certificates. This should be enabled for production with proper certificate validation.

2. **Hardcoded Credentials** - Authentication credentials are embedded in source code. Consider using environment variables or secret management for production.
