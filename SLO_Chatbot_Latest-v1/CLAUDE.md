# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**SLO Chatbot** - AI-powered Service Level Objective monitoring using Claude Sonnet 4.5 via AWS Bedrock. Analyzes **hourly metrics from ClickHouse** with **20 analytics functions**.

**Latest Update (January 2026):** Migrated to ClickHouse with hourly granularity. Data pre-loaded from kafka_put pipeline (read-only access).

## Quick Start

```bash
# First-time setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with AWS credentials

# Ensure ClickHouse is running (from kafka_put project)
docker ps | grep clickhouse
# If not running: docker start clickhouse-server

# Run the application
streamlit run app.py

# Run comprehensive tests
python3 test_clickhouse_comprehensive.py
```

## Architecture

### Data Flow
```
[kafka_put pipeline]: Platform API → Kafka → ClickHouse (pre-loaded, 8,759 rows)
                                                    ↓
User → Streamlit → Claude + TOOLS → Analytics → ClickHouse → DataFrame (RAM) → JSON → Claude → User
```

### Key Architectural Decisions
1. **ClickHouse (OLAP)** - Pre-loaded hourly data, read-only access, 8,759 rows for 122 services
2. **Hourly granularity** - More detailed than daily aggregations, fixed 12-day dataset
3. **No authentication layer** - Direct ClickHouse connection (localhost:8123)
4. **Pandas DataFrames** - Temporary in-memory processing, never persisted to disk
5. **AWS Bedrock** - Streaming responses from Claude Sonnet 4.5

### Component Layers

**Data:** `data/database/`
- `clickhouse_manager.py` - Read-only ClickHouse client with automatic field mapping

**Analytics:** `analytics/`
- `slo_calculator.py` - SLI/SLO metrics, error budgets, burn rates (4 functions)
- `degradation_detector.py` - Week-over-week comparison (3 functions)
- `trend_analyzer.py` - Predictions with linear regression (6 functions)
- `metrics.py` - Core aggregations and advanced Platform API functions (13 functions)

**Agent:** `agent/`
- `claude_client.py` - AWS Bedrock integration with streaming + DateTimeEncoder
- `function_tools.py` - FunctionExecutor dispatches 20 tool calls

**UI:** `app.py` - Streamlit with `@st.cache_resource` for component initialization

**Deprecated:** `_deprecated/` - Old Platform API client, DuckDB manager, Keycloak auth (kept for reference)

## Critical Code Patterns

### ClickHouse GROUP BY Pattern (MOST IMPORTANT)

**CRITICAL:** With hourly data (8,759 rows for 122 services), always GROUP BY only `transaction_name` to avoid duplicates:

```python
# ❌ WRONG - Creates 214+ duplicate services
sql = """
    SELECT transaction_name, eb_health, response_health, AVG(error_rate)
    FROM transaction_metrics
    GROUP BY transaction_name, eb_health, response_health  -- Multiple fields
"""

# ✅ CORRECT - Returns exactly 122 unique services
sql = """
    SELECT
        transaction_name as service_name,
        any(eb_health) as eb_health_status,        -- Use any() for status
        any(response_health) as response_health_status,
        AVG(error_rate) as avg_error_rate,         -- Use AVG() for metrics
        SUM(total_count) as total_requests,        -- Use SUM() for counts
        SUM(CASE WHEN eb_health = 'HEALTHY' THEN 1 ELSE 0 END) as healthy_hours
    FROM transaction_metrics
    GROUP BY transaction_name  -- ONLY transaction_name
    ORDER BY avg_error_rate DESC
"""
```

**Best Practices:**
1. **Always GROUP BY only `transaction_name`** when aggregating to service level
2. **Use `any()` for text/status fields** (picks arbitrary value from group)
3. **Use unique aliases** to avoid ClickHouse conflicts (`eb_health_status` not `eb_health`)
4. **Use `AVG()` for metrics**, `SUM()` for counts, `SUM(CASE...)` for conditional counts

**This pattern is used in:**
- `get_budget_exhausted_services()` - analytics/metrics.py:263
- `get_aspirational_slo_gap()` - analytics/metrics.py:309
- `get_timeliness_issues()` - analytics/metrics.py:350
- `get_composite_health_score()` - analytics/metrics.py:483
- `get_severity_heatmap()` - analytics/metrics.py:551
- `get_slo_governance_status()` - analytics/metrics.py:619

### NaN Handling Pattern

**ALWAYS** use `pd.notna()` checks before converting to integers:

```python
# ❌ WRONG - Will crash on NaN
total_requests = int(row['total_requests'])

# ✅ CORRECT - Handles NaN safely
total_req = row['total_requests']
total_requests = int(total_req) if pd.notna(total_req) else 0
```

This pattern appears in all analytics modules.

### JSON Serialization Pattern for Claude Tool Results

**ALWAYS** use the custom `DateTimeEncoder` when serializing tool results:

```python
import json
from agent.claude_client import DateTimeEncoder

# ✅ CORRECT - Handles pandas Timestamp, datetime, numpy types
result = {"timestamp": pd.Timestamp.now(), "value": np.int64(42)}
result_json = json.dumps(result, cls=DateTimeEncoder)

# ❌ WRONG - Will crash with "Object of type Timestamp is not JSON serializable"
result_json = json.dumps(result)
```

**What DateTimeEncoder handles:**
- `pd.Timestamp` → ISO format string
- `datetime/date` → ISO format string
- `np.integer` → Python int
- `np.floating` → Python float
- `np.ndarray` → Python list
- `pd.NA/np.nan` → `null`

### DataFrame Lifecycle Pattern

DataFrames are **temporary in-memory** structures, never persisted:

```python
# Stage 1: ClickHouse query returns DataFrame
df = self.db_manager.query(sql)  # Pandas DataFrame in RAM

# Stage 2: Process rows into dicts
results = []
for _, row in df.iterrows():
    results.append({
        'service_name': row['service_name'],
        'burn_rate': float(row['burn_rate']) if pd.notna(row['burn_rate']) else 0.0
    })

# Stage 3: DataFrame goes out of scope and is garbage collected
return results  # List of dicts, not DataFrame
```

**Key points:**
- DataFrames exist only during function execution
- Never written to disk (no CSV, JSON, Parquet files)
- Converted to list of dicts before returning
- Python garbage collector frees memory automatically

## Configuration

**File:** `utils/config.py` - Centralized configuration with Streamlit Cloud support

**Required `.env` variables:**
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

**Optional (with defaults):**
```bash
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
DEFAULT_ERROR_SLO_THRESHOLD=1.0
DEFAULT_RESPONSE_TIME_SLO=1.0
DEFAULT_SLO_TARGET_PERCENT=98
ASPIRATIONAL_SLO_TARGET_PERCENT=99
```

## Tool Calling Flow

**Flow:** User query → Claude decides which tool to call → FunctionExecutor routes to analytics module → SQL query executes → DataFrame created → Converted to dict → Serialized to JSON → Sent to Claude → Claude generates response

**FunctionExecutor** (`agent/function_tools.py`): Routes 20 functions to appropriate analytics modules.

### Available Functions (20 total)

**Standard (9):**
- `get_service_health_overview()` - System-wide summary
- `get_degrading_services(time_window_days)` - Week-over-week comparison
- `get_slo_violations()` - Active SLO violations
- `get_slowest_services(limit)` - Ranked by P99 latency
- `get_top_services_by_volume(limit)` - High-traffic services
- `get_service_summary(service_name)` - Comprehensive service analysis
- `get_current_sli(service_name)` - Current service level indicators
- `calculate_error_budget(service_name)` - Error budget tracking
- `get_error_prone_services(limit)` - Services with highest error rates

**Advanced (8):**
- `get_services_by_burn_rate(limit)` - Burn rate rankings
- `get_aspirational_slo_gap()` - Services meeting 98% but failing 99%
- `get_timeliness_issues()` - Batch job/scheduling problems
- `get_breach_vs_error_analysis(service_name)` - Latency vs reliability
- `get_budget_exhausted_services()` - Over-budget services (>100%)
- `get_composite_health_score()` - 0-100 health across 5 dimensions
- `get_severity_heatmap()` - Red/green indicator visualization
- `get_slo_governance_status()` - SLO approval status tracking

**Trend Analysis (3):**
- `predict_issues_today()` - ML-based predictions
- `get_volume_trends(service_name, time_window_days)` - Traffic patterns
- `get_historical_patterns(service_name)` - Statistical analysis

## Testing

```bash
# Comprehensive test suite (38 tests)
python3 test_clickhouse_comprehensive.py
# Expected: 38/38 passed

# Verify ClickHouse connection and data
docker ps | grep clickhouse
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759
```

## Common Issues

| Issue | Solution |
|-------|----------|
| **Streamlit cache not updating** | `find . -type d -name "__pycache__" -exec rm -r {} +` then restart |
| **NaN to integer conversion crash** | Use pattern: `int(val) if pd.notna(val) else 0` |
| **JSON serialization error** | Use `json.dumps(result, cls=DateTimeEncoder)` |
| **Duplicate services (214 instead of 122)** | Check GROUP BY - should only use `transaction_name` |
| **ClickHouse not running** | `docker start clickhouse-server` |
| **No data in ClickHouse** | Re-run kafka_put pipeline: `python kafka_producer.py && python kafka_to_clickhouse.py` |
| **AWS Bedrock auth errors** | Verify `.env` has correct AWS credentials |
| **Aggregate function errors in SQL** | Don't reuse field names as aliases when using `any()` |

## Database Schema

**ClickHouse Table:** `transaction_metrics` (80+ columns)

**Key fields:**
- Identifiers: `transaction_name`, `transaction_id`, `application_id`
- Time: `timestamp` (DateTime64(3))
- Core metrics: `total_count`, `error_count`, `success_count`, `error_rate`, `success_rate`
- Response times: `avg_response_time`, `percentile_25/50/75/95/99`
- SLO (Standard): `short_target_slo` (98%), `eb_consumed_percent`, `eb_health`
- SLO (Aspirational): `aspirational_slo` (99%), `aspirational_eb_health`, `aspirational_response_health`
- Advanced: `burn_rate`, `timeliness_health`, `eb_severity`, `response_severity`

**Data characteristics:**
- 8,759 rows (hourly records)
- 122 unique services
- 12 days (Dec 31, 2025 → Jan 12, 2026)
- Hourly granularity

## Data Flow Details

See `DATA_FLOW_EXPLAINED.md` for complete 6-stage data flow from ClickHouse to Claude response:
1. Storage Layer (ClickHouse OLAP)
2. Query Layer (ClickHouseManager)
3. DataFrame Layer (Pandas in-memory)
4. Analytics Layer (Python processing)
5. Serialization Layer (JSON conversion)
6. AI Response Layer (Claude Sonnet 4.5)

## Development Workflows

### Adding New Analytics Functions

1. Add method to appropriate module (`analytics/metrics.py`, etc.)
2. Use GROUP BY pattern: only `transaction_name`
3. Use NaN-safe conversions: `int(val) if pd.notna(val) else 0`
4. Return list of dicts (not DataFrame)
5. Add wrapper in `FunctionExecutor` (`agent/function_tools.py`)
6. Register in `function_map`
7. Add tool definition to `TOOLS` list
8. Update system prompt in `app.py`
9. Test with `python3 test_clickhouse_comprehensive.py`

### Modifying SQL Queries

**Golden Rules:**
- GROUP BY only `transaction_name` for service-level aggregations
- Use `any()` for status fields with unique aliases
- Use `AVG()` for metrics, `SUM()` for counts
- Test query returns exactly 122 services (or specified LIMIT)

### Debugging

```bash
# Check ClickHouse data
docker exec clickhouse-server clickhouse-client --query "SELECT * FROM transaction_metrics LIMIT 5"

# Clear Streamlit cache
find . -type d -name "__pycache__" -exec rm -r {} +

# Run single test
python3 -c "from analytics.metrics import MetricsAggregator; from data.database.clickhouse_manager import ClickHouseManager; m = MetricsAggregator(ClickHouseManager()); print(len(m.get_services_by_burn_rate(limit=10)))"
```

## Migration Notes

**January 2026:** Migrated from DuckDB + Platform API to ClickHouse

**Key changes:**
- DuckDB → ClickHouse (OLAP database)
- Daily aggregation → Hourly granularity
- 5-60 day windows → Fixed 12-day dataset
- Platform API client → Pre-loaded data (read-only)
- 90+ columns → 80+ columns (similar field coverage)

**Deprecated components** (in `_deprecated/`):
- `data/database/duckdb_manager.py`
- `data/ingestion/platform_api_client.py`
- `data/ingestion/keycloak_auth.py`
- `data/ingestion/data_loader.py`

See `MIGRATION_COMPLETE.md` and `CLICKHOUSE_MIGRATION.md` for complete migration details.
