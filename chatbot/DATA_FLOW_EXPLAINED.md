# SLO Chatbot - Complete Data Flow Explanation

**Last Updated:** January 15, 2026
**Purpose:** Explain the complete journey of data from ClickHouse to Claude's response

---

## Executive Summary

Data flows through **6 distinct stages**:
1. **Storage Layer** - ClickHouse OLAP database (8,759 rows pre-loaded)
2. **Query Layer** - SQL queries executed via ClickHouseManager
3. **DataFrame Layer** - Query results converted to Pandas DataFrames
4. **Analytics Layer** - DataFrames processed by analytics modules
5. **Serialization Layer** - Results converted to JSON for Claude
6. **AI Response Layer** - Claude analyzes JSON and generates natural language response

**Key Insight:** Raw hourly data lives in ClickHouse → Gets filtered/aggregated into DataFrames → Converted to JSON dictionaries → Sent to Claude → Claude returns human-readable analysis

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: STORAGE LAYER (ClickHouse OLAP)                           │
│                                                                     │
│  ClickHouse Database (localhost:8123)                              │
│  ├─ Table: transaction_metrics                                     │
│  ├─ Rows: 8,759 hourly records                                     │
│  ├─ Services: 122 unique transaction endpoints                     │
│  ├─ Columns: 80+ fields (metrics, SLO, health, percentiles)       │
│  └─ Time Range: Dec 31, 2025 → Jan 12, 2026 (12 days)            │
│                                                                     │
│  Sample Data (3 rows out of 8,759):                               │
│  transaction_name              timestamp            error_rate  ... │
│  GET /api/endpoint1           2025-12-31 19:00:00   0.5%       ... │
│  GET /api/endpoint1           2025-12-31 20:00:00   0.3%       ... │
│  GET /api/endpoint2           2025-12-31 19:00:00   1.2%       ... │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: QUERY LAYER (ClickHouseManager)                           │
│                                                                     │
│  File: data/database/clickhouse_manager.py                         │
│  Class: ClickHouseManager                                          │
│                                                                     │
│  User Query Example: "Which services have high burn rates?"        │
│                                                                     │
│  Claude calls: get_services_by_burn_rate(limit=10)                 │
│                                                                     │
│  This triggers SQL query:                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ SELECT                                                        │ │
│  │     transaction_name as service_name,                        │ │
│  │     AVG(error_rate) as avg_error_rate,                       │ │
│  │     any(eb_health) as eb_health_status,                      │ │
│  │     (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0))     │ │
│  │         * 100 as burn_rate,                                  │ │
│  │     SUM(total_count) as total_requests                       │ │
│  │ FROM transaction_metrics                                     │ │
│  │ GROUP BY transaction_name                                    │ │
│  │ ORDER BY burn_rate DESC                                      │ │
│  │ LIMIT 10                                                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Method: db_manager.query(sql)                                     │
│  Returns: Pandas DataFrame ⬇                                       │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: DATAFRAME LAYER (Pandas In-Memory)                        │
│                                                                     │
│  Data Structure: Pandas DataFrame (in-memory, NOT stored)          │
│  Location: Variable in analytics/metrics.py                        │
│  Lifetime: Temporary (created per query, discarded after use)      │
│                                                                     │
│  DataFrame Contents (10 rows × 5 columns):                         │
│  ┌─────────────────────┬──────────────┬───────────────┬───────────┐│
│  │ service_name        │avg_error_rate│eb_health_status│burn_rate │││
│  ├─────────────────────┼──────────────┼───────────────┼───────────┤│
│  │ GET /api/test-ep    │   100.0%     │   UNHEALTHY   │  102.04   │││
│  │ POST /api/critical  │    44.3%     │   UNHEALTHY   │   45.23   │││
│  │ GET /api/slow       │    12.5%     │   WARNING     │   12.75   │││
│  │ ...                 │     ...      │      ...      │    ...    │││
│  └─────────────────────┴──────────────┴───────────────┴───────────┘│
│                                                                     │
│  Why DataFrame? Pandas provides:                                   │
│  • Easy iteration over rows (.iterrows())                          │
│  • Safe NaN handling (pd.notna() checks)                           │
│  • Data type conversions (int, float, string)                      │
│  • In-memory processing (fast for 10-1000 rows)                    │
│                                                                     │
│  Storage Location: RAM (NOT persisted to disk)                     │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: ANALYTICS LAYER (Python Processing)                       │
│                                                                     │
│  File: analytics/metrics.py                                        │
│  Class: MetricsAggregator                                          │
│  Method: get_services_by_burn_rate(limit=10)                       │
│                                                                     │
│  Python Code:                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ df = self.db_manager.query(sql)  # Got DataFrame from Stage 3│ │
│  │                                                               │ │
│  │ results = []                                                  │ │
│  │ for _, row in df.iterrows():  # Iterate each row             │ │
│  │     # Safe NaN handling                                      │ │
│  │     burn_rate = row['burn_rate']                             │ │
│  │     burn_rate_val = (float(burn_rate)                        │ │
│  │                      if pd.notna(burn_rate) else 0.0)        │ │
│  │                                                               │ │
│  │     results.append({                                         │ │
│  │         'service_name': row['service_name'],                 │ │
│  │         'burn_rate': burn_rate_val,                          │ │
│  │         'avg_error_rate': float(row['avg_error_rate']),      │ │
│  │         'total_requests': int(row['total_requests'])         │ │
│  │     })                                                        │ │
│  │                                                               │ │
│  │ return results  # List of dicts ⬇                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Output Format: List[Dict[str, Any]]                               │
│  Example:                                                          │
│  [                                                                 │
│    {                                                               │
│      'service_name': 'GET /api/test-endpoint',                    │
│      'burn_rate': 102.04,                                         │
│      'avg_error_rate': 100.0,                                     │
│      'total_requests': 1234                                       │
│    },                                                              │
│    { ... }, { ... }  # 9 more services                            │
│  ]                                                                 │
│                                                                     │
│  DataFrame is now DISCARDED (garbage collected)                    │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: SERIALIZATION LAYER (Python → JSON)                       │
│                                                                     │
│  File: agent/claude_client.py                                      │
│  Class: DateTimeEncoder (custom JSON encoder)                      │
│                                                                     │
│  Process: Convert Python objects to JSON string                    │
│                                                                     │
│  Code:                                                             │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ result = tool_executor.execute('get_services_by_burn_rate',  │ │
│  │                                {'limit': 10})                 │ │
│  │ # result is the list of dicts from Stage 4                   │ │
│  │                                                               │ │
│  │ result_json = json.dumps(result, cls=DateTimeEncoder)        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  JSON Output (sent to Claude):                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ [                                                             │ │
│  │   {                                                           │ │
│  │     "service_name": "GET /api/test-endpoint",                │ │
│  │     "burn_rate": 102.04,                                     │ │
│  │     "avg_error_rate": 100.0,                                 │ │
│  │     "total_requests": 1234                                   │ │
│  │   },                                                          │ │
│  │   { "service_name": "POST /api/critical", ... },             │ │
│  │   { "service_name": "GET /api/slow", ... }                   │ │
│  │ ]                                                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  DateTimeEncoder handles:                                          │
│  • pd.Timestamp → ISO string ("2025-12-31T19:00:00")              │
│  • np.int64 → Python int (1234)                                   │
│  • np.float64 → Python float (102.04)                             │
│  • pd.NA / np.nan → null                                          │
│                                                                     │
│  This JSON is attached to Claude's API request as tool_result      │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 6: AI RESPONSE LAYER (Claude Sonnet 4.5 on AWS Bedrock)     │
│                                                                     │
│  Service: AWS Bedrock                                              │
│  Model: Claude Sonnet 4.5 (global.anthropic.claude-sonnet-4.5...) │
│  Region: ap-south-1 (Mumbai)                                       │
│                                                                     │
│  Claude receives:                                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ User Query: "Which services have high burn rates?"           │ │
│  │                                                               │ │
│  │ System Prompt: [Analytics function descriptions, field       │ │
│  │                 definitions, interpretation guidelines]       │ │
│  │                                                               │ │
│  │ Tool Result (from Stage 5): JSON data                        │ │
│  │ {                                                             │ │
│  │   "tool_use_id": "toolu_123abc",                             │ │
│  │   "content": "[{\"service_name\": \"GET /api/test-ep\", ...}]"│ │
│  │ }                                                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  Claude's Processing:                                              │
│  1. Parses JSON data                                               │
│  2. Analyzes burn_rate values (102.04 = critical, 45.23 = high)   │
│  3. Applies domain knowledge from system prompt                    │
│  4. Generates natural language response with insights              │
│                                                                     │
│  Claude's Response (streamed back to user):                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Based on the burn rate analysis, here are the top 5 services │ │
│  │ with the highest burn rates:                                 │ │
│  │                                                               │ │
│  │ 1. **GET /api/test-endpoint** - Burn rate: 102.04           │ │
│  │    - Error rate: 100%                                        │ │
│  │    - Status: CRITICAL - This service is completely failing  │ │
│  │    - Action: Immediate investigation required                │ │
│  │                                                               │ │
│  │ 2. **POST /api/critical-service** - Burn rate: 45.23        │ │
│  │    - Error rate: 44.32%                                      │ │
│  │    - Status: HIGH RISK - Rapid budget consumption           │ │
│  │    - Action: Review recent deployments                       │ │
│  │                                                               │ │
│  │ [Additional analysis...]                                     │ │
│  │                                                               │ │
│  │ Burn Rate Interpretation:                                    │ │
│  │ • < 1.0: Healthy                                             │ │
│  │ • 1.0-2.0: Warning                                           │ │
│  │ • 2.0-5.0: High Risk                                         │ │
│  │ • > 5.0: Critical                                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  This response is streamed back to the Streamlit UI                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
                          User sees the response!
```

---

## Detailed Stage-by-Stage Breakdown

### Stage 1: Storage Layer (ClickHouse OLAP)

**Location:** ClickHouse Docker container (`localhost:8123`)

**Data Characteristics:**
- **Table:** `transaction_metrics`
- **Storage Type:** Columnar OLAP database (optimized for analytics queries)
- **Data Volume:** 8,759 rows (hourly granularity)
- **Time Range:** 12 days (Dec 31, 2025 → Jan 12, 2026)
- **Services:** 122 unique transaction endpoints
- **Columns:** 80+ fields per row

**Key Fields Stored:**
```sql
transaction_name          VARCHAR   -- Service identifier (e.g., "GET /api/endpoint")
timestamp                 DateTime  -- Hourly timestamp
error_rate               Float64   -- 0.0 to 100.0
avg_response_time        Float64   -- Milliseconds
total_count              UInt64    -- Request count
percentile_50, p95, p99  Float64   -- Latency percentiles
eb_health                String    -- HEALTHY/UNHEALTHY
short_target_slo         Float64   -- Standard SLO target (98%)
... (70+ more fields)
```

**Data Loading (Happens BEFORE user queries):**
```bash
# In kafka_put project:
python kafka_producer.py        # Fetch from Platform API → Kafka
python kafka_to_clickhouse.py   # Load Kafka → ClickHouse

# Result: 8,759 rows inserted into ClickHouse
# This chatbot does NOT insert data - read-only access
```

**Important:** This is a **read-only** data source. The chatbot never writes to ClickHouse.

---

### Stage 2: Query Layer (ClickHouseManager)

**File:** `data/database/clickhouse_manager.py`
**Class:** `ClickHouseManager`
**Purpose:** Execute SQL queries and return results as DataFrames

**Initialization:**
```python
# In app.py - initialize_system()
db_manager = ClickHouseManager(host='localhost', port=8123)
# Connects to ClickHouse, verifies transaction_metrics table exists
```

**Query Execution Flow:**

1. **User asks:** "Which services have high burn rates?"

2. **Claude decides** to call function: `get_services_by_burn_rate(limit=10)`

3. **Analytics module** builds SQL query:
```python
# In analytics/metrics.py - get_services_by_burn_rate()
sql = """
    SELECT
        transaction_name as service_name,
        AVG(error_rate) as avg_error_rate,
        any(eb_health) as eb_health_status,
        (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as burn_rate,
        SUM(total_count) as total_requests
    FROM transaction_metrics
    GROUP BY transaction_name
    ORDER BY burn_rate DESC
    LIMIT 10
"""
```

4. **Execute query:**
```python
df = self.db_manager.query(sql)
# Calls ClickHouse via clickhouse_connect library
# Returns Pandas DataFrame
```

**What happens inside `query()` method:**
```python
def query(self, sql: str) -> pd.DataFrame:
    # Execute query and get DataFrame from ClickHouse
    df = self.client.query_df(sql)  # clickhouse_connect method

    # Automatic field mapping for compatibility
    if 'transaction_name' in df.columns and 'service_name' not in df.columns:
        df['service_name'] = df['transaction_name']

    return df  # Returns Pandas DataFrame
```

**Key Insight:** ClickHouse aggregates 8,759 hourly rows down to 122 service-level rows (or 10 with LIMIT), returning only the aggregated data.

---

### Stage 3: DataFrame Layer (Pandas In-Memory)

**Data Structure:** Pandas DataFrame
**Storage Location:** RAM (temporary variable)
**Lifetime:** Created during function execution, discarded after use
**NOT persisted to disk**

**Example DataFrame Contents:**

```python
# Variable: df
# Type: pandas.DataFrame
# Shape: (10 rows, 5 columns)

print(df)
```

Output:
```
                    service_name  avg_error_rate eb_health_status  burn_rate  total_requests
0    GET /api/test-endpoint              100.0      UNHEALTHY     102.04          1234
1  POST /api/critical-service             44.3      UNHEALTHY      45.23         56789
2         GET /api/slow-service             12.5       WARNING      12.75         23456
3       GET /api/normal-service              0.8       HEALTHY       0.82        123456
...
```

**Why Pandas DataFrame?**

1. **Easy Iteration:**
```python
for _, row in df.iterrows():
    service_name = row['service_name']  # Access like dictionary
    burn_rate = row['burn_rate']
```

2. **Safe NaN Handling:**
```python
import pandas as pd

burn_rate = row['burn_rate']
if pd.notna(burn_rate):  # Check for NaN/NULL values
    value = float(burn_rate)
else:
    value = 0.0
```

3. **Type Conversions:**
```python
total_requests = int(row['total_requests'])  # numpy.int64 → Python int
avg_error = float(row['avg_error_rate'])     # numpy.float64 → Python float
```

4. **In-Memory Performance:**
   - Fast for 10-1000 rows (typical analytics query results)
   - No disk I/O overhead
   - Direct memory access

**Storage Details:**
- **NOT stored in a database** (DuckDB, ClickHouse, PostgreSQL, etc.)
- **NOT written to disk** (no CSV, JSON, Parquet files created)
- **Lives in Python process memory** during function execution
- **Garbage collected** after function returns (Python memory management)

**Memory Location:**
```
Python Process Memory (RAM)
├── ClickHouseManager object
├── MetricsAggregator object
└── Local variables in get_services_by_burn_rate()
    └── df (Pandas DataFrame) ← HERE
        └── Deleted when function returns
```

---

### Stage 4: Analytics Layer (Python Processing)

**File:** `analytics/metrics.py` (or other analytics modules)
**Purpose:** Process DataFrame rows into structured dictionaries for Claude

**Code Example:**

```python
class MetricsAggregator:
    def get_services_by_burn_rate(self, limit: int = 10) -> List[Dict[str, Any]]:
        # Stage 2: Build SQL query
        sql = """..."""

        # Stage 3: Get DataFrame from ClickHouse
        df = self.db_manager.query(sql)

        # Stage 4: Process DataFrame into list of dicts
        results = []
        for _, row in df.iterrows():  # Iterate each row
            # Safe NaN handling (CRITICAL pattern)
            burn_rate = row['burn_rate']
            burn_rate_val = float(burn_rate) if pd.notna(burn_rate) else 0.0

            avg_error = row['avg_error_rate']
            avg_error_val = float(avg_error) if pd.notna(avg_error) else 0.0

            total_req = row['total_requests']
            total_req_val = int(total_req) if pd.notna(total_req) else 0

            # Build structured dictionary
            results.append({
                'service_name': row['service_name'],
                'burn_rate': burn_rate_val,
                'avg_error_rate': avg_error_val,
                'eb_health': row['eb_health_status'],
                'total_requests': total_req_val
            })

        # DataFrame is now out of scope and will be garbage collected
        return results  # List of dicts
```

**Output Format:**
```python
[
    {
        'service_name': 'GET /api/test-endpoint',
        'burn_rate': 102.04,
        'avg_error_rate': 100.0,
        'eb_health': 'UNHEALTHY',
        'total_requests': 1234
    },
    {
        'service_name': 'POST /api/critical-service',
        'burn_rate': 45.23,
        'avg_error_rate': 44.3,
        'eb_health': 'UNHEALTHY',
        'total_requests': 56789
    },
    # ... 8 more services
]
```

**Why Convert DataFrame to List of Dicts?**

1. **JSON Serialization:** Dicts convert easily to JSON for Claude
2. **Type Safety:** Explicit type conversions (int, float, str)
3. **Clean Structure:** Only relevant fields, no extra DataFrame metadata
4. **API Compatibility:** Claude expects JSON-serializable data

**DataFrame Lifecycle:**
```
Created → Used in for loop → Function returns → Garbage collected
(Stage 3)   (Stage 4)          (End of Stage 4)  (Python memory cleanup)
```

---

### Stage 5: Serialization Layer (Python → JSON)

**File:** `agent/claude_client.py`
**Class:** `DateTimeEncoder`
**Purpose:** Convert Python objects to JSON string for Claude API

**The Problem:**

Pandas and NumPy types are **NOT JSON serializable** by default:

```python
import json
import pandas as pd
import numpy as np

data = {
    'timestamp': pd.Timestamp('2025-12-31 19:00:00'),
    'count': np.int64(1234),
    'rate': np.float64(102.04)
}

json.dumps(data)  # ❌ ERROR: Object of type Timestamp is not JSON serializable
```

**The Solution: Custom Encoder**

```python
class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and pandas objects."""

    def default(self, obj):
        # Handle pandas Timestamp and Python datetime
        if isinstance(obj, (pd.Timestamp, datetime, date)):
            return obj.isoformat()  # "2025-12-31T19:00:00"

        # Handle NumPy integers
        if isinstance(obj, np.integer):
            return int(obj)  # np.int64(1234) → 1234

        # Handle NumPy floats
        if isinstance(obj, np.floating):
            return float(obj)  # np.float64(102.04) → 102.04

        # Handle NumPy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # [1, 2, 3]

        # Handle pandas NA values
        if pd.isna(obj):
            return None  # null in JSON

        # Default behavior for other types
        return super().default(obj)
```

**Usage in Code:**

```python
# In claude_client.py - chat_stream() method

# Execute analytics function (returns list of dicts from Stage 4)
result = tool_executor.execute('get_services_by_burn_rate', {'limit': 10})

# Serialize to JSON using custom encoder
result_json = json.dumps(result, cls=DateTimeEncoder)

# Create tool result for Claude
tool_results.append({
    "type": "tool_result",
    "tool_use_id": tool_use_id,
    "content": result_json  # JSON string
})
```

**JSON Output (actual string sent to Claude):**

```json
[
  {
    "service_name": "GET /api/test-endpoint",
    "burn_rate": 102.04,
    "avg_error_rate": 100.0,
    "eb_health": "UNHEALTHY",
    "total_requests": 1234
  },
  {
    "service_name": "POST /api/critical-service",
    "burn_rate": 45.23,
    "avg_error_rate": 44.3,
    "eb_health": "UNHEALTHY",
    "total_requests": 56789
  }
]
```

**This JSON is attached to the AWS Bedrock API request:**

```python
# Message sent to Claude
{
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123abc",
            "content": "[{\"service_name\": \"GET /api/test-endpoint\", ...}]"
        }
    ]
}
```

---

### Stage 6: AI Response Layer (Claude on AWS Bedrock)

**Service:** AWS Bedrock
**Model:** Claude Sonnet 4.5 (`global.anthropic.claude-sonnet-4-5-20250929-v1:0`)
**Region:** ap-south-1 (Mumbai, India)
**API:** Streaming API (`invoke_model_with_response_stream`)

**Claude Receives 3 Inputs:**

1. **User Query:**
```
"Which services have high burn rates?"
```

2. **System Prompt (from app.py):**
```
You are an expert SLO analyst with access to 20 analytics functions.

Available Functions:
- get_services_by_burn_rate(limit): Returns services ranked by burn rate
  Fields: service_name, burn_rate, avg_error_rate, eb_health, total_requests

Burn Rate Interpretation:
- < 1.0: Healthy (error rate below SLO target)
- 1.0-2.0: Warning (approaching SLO target)
- 2.0-5.0: High Risk (rapid budget consumption)
- > 5.0: Critical (budget will exhaust quickly)
- > 100: Extreme (100% error rate, complete failure)

When analyzing burn rates, provide:
1. Top services with specific values
2. Status assessment (HEALTHY/WARNING/CRITICAL)
3. Actionable recommendations
...
```

3. **Tool Result (JSON from Stage 5):**
```json
{
  "tool_use_id": "toolu_123abc",
  "content": "[{\"service_name\": \"GET /api/test-endpoint\", \"burn_rate\": 102.04, ...}]"
}
```

**Claude's Internal Processing:**

1. **Parse JSON data** (10 services with burn rates)
2. **Apply domain knowledge** from system prompt
3. **Analyze patterns:**
   - burn_rate 102.04 = > 100 = Extreme/Critical
   - burn_rate 45.23 = 2.0-5.0 range = High Risk
   - error_rate 100% = Complete service failure
4. **Generate insights:**
   - Prioritize by severity
   - Provide specific values
   - Add context and recommendations

**Claude Generates Response (streamed back):**

```markdown
Based on the burn rate analysis, here are the top 5 services with the highest burn rates:

**1. GET /api/test-endpoint - Burn rate: 102.04**
   - Error rate: 100%
   - SLO Health: UNHEALTHY
   - Total Requests: 1,234
   - Status: **CRITICAL** - This service has a 100% error rate, indicating complete failure
   - Recommended Action: **Immediate investigation required** - All requests are failing

**2. POST /api/critical-service - Burn rate: 45.23**
   - Error rate: 44.3%
   - SLO Health: UNHEALTHY
   - Total Requests: 56,789
   - Status: **HIGH RISK** - Burn rate indicates rapid error budget consumption
   - Recommended Action: Review recent deployments, check for infrastructure issues

**3. GET /api/slow-service - Burn rate: 12.75**
   - Error rate: 12.5%
   - Status: **HIGH RISK** - Above 5.0 threshold
   - Recommended Action: Investigate performance bottlenecks

[Additional services...]

**Burn Rate Interpretation:**
- **< 1.0**: Healthy - error rate below SLO target
- **1.0-2.0**: Warning - approaching SLO target
- **2.0-5.0**: High Risk - rapid budget consumption
- **> 5.0**: Critical - budget will exhaust quickly
- **> 100**: Extreme - indicates 100%+ error rates

**Summary:**
2 services are in CRITICAL state requiring immediate attention. I recommend focusing on GET /api/test-endpoint first due to its 100% error rate.
```

**Streaming Process:**

```python
# In claude_client.py
for chunk in response['body']:  # AWS Bedrock streaming response
    chunk_data = json.loads(chunk['chunk']['bytes'].decode())

    if chunk_data['type'] == 'content_block_delta':
        delta = chunk_data.get('delta', {})
        if delta.get('type') == 'text_delta':
            text = delta.get('text', '')
            yield text  # Send to Streamlit UI immediately
```

**User sees the response appear character-by-character** in the Streamlit chat interface!

---

## Summary: Complete Data Journey

```
User Question
    ↓
User types: "Which services have high burn rates?"
    ↓
Streamlit captures input (app.py)
    ↓
Claude API call with system prompt + tools
    ↓
Claude decides: "Call get_services_by_burn_rate(limit=10)"
    ↓
FunctionExecutor routes to MetricsAggregator
    ↓
SQL Query built: "SELECT ... GROUP BY transaction_name ... LIMIT 10"
    ↓
ClickHouseManager.query(sql) executes query
    ↓
ClickHouse returns aggregated data (10 rows from 8,759)
    ↓
Result converted to Pandas DataFrame (in RAM)
    ↓
DataFrame rows iterated, converted to list of dicts
    ↓
List of dicts serialized to JSON (DateTimeEncoder)
    ↓
JSON sent back to Claude as tool_result
    ↓
Claude analyzes JSON data + applies system prompt knowledge
    ↓
Claude generates natural language response (streaming)
    ↓
Response streamed character-by-character to Streamlit
    ↓
User sees: "Based on the burn rate analysis, here are..."
```

---

## Key Takeaways

1. **ClickHouse stores raw hourly data** (8,759 rows, 122 services, 12 days)
2. **SQL queries aggregate to service level** (122 or fewer rows)
3. **DataFrames are temporary** (created per query, exist in RAM only)
4. **Analytics modules process** DataFrames into clean dicts
5. **JSON serialization** converts Python types for Claude
6. **Claude receives structured JSON** and generates human-readable insights
7. **No intermediate storage** - data flows directly from ClickHouse → RAM → Claude → User

**The DataFrame never touches disk** - it's purely an in-memory intermediate format between SQL results and JSON serialization.

---

**Questions?** See:
- `CLICKHOUSE_MIGRATION.md` - SQL query patterns
- `MIGRATION_COMPLETE.md` - List of all fixes applied
- `test_clickhouse_comprehensive.py` - Test suite showing all data flows
