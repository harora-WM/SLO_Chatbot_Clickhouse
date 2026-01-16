# SLO Chatbot Data Flow Architecture

This document explains how data flows through the SLO Chatbot system, from OpenSearch ingestion to Claude's responses.

## 🏗️ Complete Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER (Streamlit UI)                          │
│  - Clicks "Refresh from OpenSearch" button                           │
│  - Asks question: "Which services are degrading?"                    │
└────────────┬──────────────────────────────┬──────────────────────────┘
             │                              │
             │ 1. LOAD DATA                 │ 2. CHAT QUERY
             │                              │
┌────────────▼──────────────────┐          │
│   OpenSearchClient            │          │
│   (opensearch_client.py)      │          │
│                               │          │
│ - Connects to OpenSearch      │          │
│ - Queries service logs index  │          │
│ - Queries error logs index    │          │
│ - Max 4-hour window           │          │
│ - Returns JSON response       │          │
└────────────┬──────────────────┘          │
             │                              │
             │ Raw JSON                     │
             │                              │
┌────────────▼──────────────────┐          │
│   DataLoader                  │          │
│   (data_loader.py)            │          │
│                               │          │
│ - Parses OpenSearch JSON      │          │
│ - Extracts from:              │          │
│   • _source.scripted_metric   │          │
│   • fields (fallback)         │          │
│ - Creates pandas DataFrames   │          │
│ - Handles NaN values          │          │
└────────────┬──────────────────┘          │
             │                              │
             │ pandas DataFrame             │
             │                              │
┌────────────▼──────────────────┐          │
│   DuckDBManager               │◄─────────┼────────────┐
│   (duckdb_manager.py)         │          │            │
│                               │          │            │
│ TABLES:                       │          │            │
│ ├─ service_logs               │          │            │
│ │  • error_rate               │          │            │
│ │  • response_time_avg/p95/99 │          │            │
│ │  • total_count              │          │            │
│ │  • record_time              │          │            │
│ │                             │          │            │
│ └─ error_logs                 │          │            │
│    • error_codes              │          │            │
│    • error_count              │          │            │
│    • error_details            │          │            │
│                               │          │            │
│ - Fast SQL queries            │          │            │
│ - Aggregations                │          │            │
│ - Time-series analysis        │          │            │
└────────────┬──────────────────┘          │            │
             │                              │            │
             │                              │            │
             │ Data Ready ✓                 │            │
             │                              │            │
             │      ┌───────────────────────▼───┐        │
             │      │  ClaudeClient             │        │
             │      │  (claude_client.py)       │        │
             │      │                           │        │
             │      │ - Receives user question  │        │
             │      │ - Has TOOLS list (15)     │        │
             │      │ - Calls AWS Bedrock API   │        │
             │      │ - Maintains conversation  │        │
             │      │   history                 │        │
             │      └───────────┬───────────────┘        │
             │                  │                        │
             │                  │ "Which services are    │
             │                  │  degrading?"           │
             │                  │                        │
             │      ┌───────────▼───────────────┐        │
             │      │  AWS Bedrock              │        │
             │      │  (Claude Sonnet 4.5)      │        │
             │      │                           │        │
             │      │ - Analyzes question       │        │
             │      │ - Decides to call:        │        │
             │      │   get_degrading_services()│        │
             │      │ - Returns tool_use        │        │
             │      └───────────┬───────────────┘        │
             │                  │                        │
             │                  │ tool_use: {           │
             │                  │   name: "get_degrading_│
             │                  │         services",     │
             │                  │   input: {            │
             │                  │     time_window: 30   │
             │                  │   }                   │
             │                  │ }                     │
             │                  │                        │
             │      ┌───────────▼───────────────┐        │
             │      │  FunctionExecutor         │        │
             │      │  (function_tools.py)      │        │
             │      │                           │        │
             │      │ - Receives tool call      │        │
             │      │ - Maps to analytics module│        │
             │      │ - Executes function       │        │
             │      └───────────┬───────────────┘        │
             │                  │                        │
             │                  │ Call:                  │
             │                  │ degradation_detector.  │
             │                  │ detect_degrading_      │
             │                  │ services(30)           │
             │                  │                        │
             │      ┌───────────▼───────────────┐        │
             │      │  DegradationDetector      │        │
             │      │  (degradation_detector.py)│        │
             │      │                           │        │
             │      │ - Queries DuckDB ─────────┼────────┘
             │      │ - Compares time windows:  │
             │      │   • Recent (last 30min)   │
             │      │   • Baseline (prev 30min) │
             │      │ - Calculates % change     │
             │      │ - Returns results         │
             │      └───────────┬───────────────┘
             │                  │
             │                  │ Result: [
             │                  │   {service: "API-1",
             │                  │    degradation: "45%",
             │                  │    metric: "p95_latency"}
             │                  │ ]
             │                  │
             │      ┌───────────▼───────────────┐
             │      │  FunctionExecutor         │
             │      │                           │
             │      │ - Serializes with         │
             │      │   DateTimeEncoder         │
             │      │ - Returns to Claude       │
             │      └───────────┬───────────────┘
             │                  │
             │                  │ tool_result: {
             │                  │   tool_use_id: "...",
             │                  │   content: JSON
             │                  │ }
             │                  │
             │      ┌───────────▼───────────────┐
             │      │  AWS Bedrock              │
             │      │  (Claude Sonnet 4.5)      │
             │      │                           │
             │      │ - Receives tool result    │
             │      │ - Synthesizes answer      │
             │      │ - Returns natural language│
             │      └───────────┬───────────────┘
             │                  │
             │                  │ "Based on the data,
             │                  │  API-1 is degrading
             │                  │  with 45% increase in
             │                  │  P95 latency..."
             │                  │
┌────────────▼──────────────────▼───┐
│   Streamlit UI                    │
│                                   │
│ - Displays Claude's response      │
│ - Shows formatted metrics         │
│ - Updates chat history            │
└───────────────────────────────────┘
```

## 📊 Two Separate Data Flows

### **Flow 1: Data Loading (Left Side) - WRITE Operations**

Happens when user clicks **"🔄 Refresh from OpenSearch"** button.

```
OpenSearch → OpenSearchClient → DataLoader → DuckDBManager
             (Queries)           (Parses)     (INSERT INTO tables)
```

**Step-by-step:**

1. **OpenSearchClient** (`data/ingestion/opensearch_client.py`)
   - Connects to OpenSearch cluster
   - Queries service_logs index (max 4-hour window)
   - Queries error_logs index (max 4-hour window)
   - Returns raw JSON response

2. **DataLoader** (`data/ingestion/data_loader.py`)
   - Parses JSON from `_source.scripted_metric` (primary)
   - Falls back to `fields` for test compatibility
   - Creates pandas DataFrames with proper types
   - Handles NaN values safely

3. **DuckDBManager** (`data/database/duckdb_manager.py`)
   - Clears old data: `DELETE FROM service_logs`
   - Inserts new data: `INSERT INTO service_logs`
   - Resets DataFrame index for compatibility
   - Stores in OLAP database for fast queries

### **Flow 2: Chat Queries (Right Side) - READ Operations**

Happens when user asks a question in chat.

```
User Question → ClaudeClient → AWS Bedrock (Claude) → FunctionExecutor
                                     ↓                        ↓
                               tool_use decision      Execute analytics function
                                                              ↓
                                                   DegradationDetector/Metrics
                                                              ↓
                                                   SELECT * FROM DuckDB (READ)
                                                              ↓
                                                      Analyze & Return Results
                                                              ↓
                                                   Back to Claude (tool_result)
                                                              ↓
                                                   Natural language response
```

**Step-by-step:**

1. **ClaudeClient** (`agent/claude_client.py:63`)
   - Receives user question
   - Sends to AWS Bedrock with TOOLS list (15 functions)
   - Maintains conversation history for context

2. **AWS Bedrock (Claude Sonnet 4.5)**
   - Analyzes question
   - Decides which tool(s) to call
   - Returns `tool_use` request with function name + parameters

3. **FunctionExecutor** (`agent/function_tools.py:35`)
   - Maps tool name to analytics module
   - Example: `get_degrading_services` → `degradation_detector.detect_degrading_services()`
   - Executes the function

4. **Analytics Module** (e.g., `analytics/degradation_detector.py`)
   - **Queries DuckDB** (READ operation):
     ```sql
     SELECT service_name, AVG(error_rate), AVG(response_time_p95)
     FROM service_logs
     WHERE record_time > NOW() - INTERVAL '30 minutes'
     GROUP BY service_name
     ```
   - Compares recent vs baseline windows
   - Calculates percentage changes
   - Returns structured results

5. **FunctionExecutor** serializes results
   - Uses `DateTimeEncoder` to handle pandas/numpy types
   - Converts to JSON string

6. **ClaudeClient** sends tool_result back to Bedrock
   - Adds to conversation history as user message
   - Claude synthesizes natural language response

7. **Streamlit UI** displays response to user

## 🔑 Key Architecture Points

### Why DuckDB Instead of Vector Database?

```python
# ❌ NOT semantic search - data is STRUCTURED
{
  "service_name": "API-1",
  "error_rate": 2.5,        # Numbers, not text
  "response_time": 150,     # Metrics, not embeddings
  "record_time": "2026-01-08T10:00:00"
}

# ✅ SQL aggregations are PERFECT for this
SELECT service_name, AVG(error_rate), MAX(response_time_p95)
FROM service_logs
WHERE record_time > '2026-01-08'
GROUP BY service_name
```

**DuckDB is chosen because:**
- SLO data is highly structured (not unstructured text)
- Need SQL aggregations, not semantic similarity
- OLAP optimized for analytical queries
- No need for embeddings or vector search

### Why 15 Analytics Functions?

Each function = specialized SQL query optimized for specific analysis:

- `get_degrading_services()` → Time-window comparison SQL
- `get_slowest_services()` → `ORDER BY response_time_p99 DESC`
- `calculate_error_budget()` → SLO compliance calculations
- `get_error_details_by_code()` → `WHERE error_codes = 'X'`

**Claude doesn't write SQL** - it picks the right pre-built function based on the question!

### Conversation History Pattern

```python
# Turn 1
User: "Which services are degrading?"
Assistant: [tool_use: get_degrading_services]
User: [tool_result: API-1 degrading]
Assistant: "API-1 is degrading by 45%"

# Turn 2 - Claude REMEMBERS Turn 1
User: "What are the error codes for that service?"
Assistant: [tool_use: get_error_code_distribution(service_name="API-1")]
         # ↑ Claude knows "that service" = API-1 from history!
```

The `conversation_history` list maintains context across multiple turns.

### Data Persistence

- **DuckDB file persists** between app restarts
- **Chat queries** only READ data (no modifications)
- **Data only changes** when user clicks "Refresh from OpenSearch"
- **To update data**: Click refresh button → overwrites tables

### Critical Patterns

#### 1. NaN Handling
```python
# Always check before converting to int
total_req = row['total_requests']
total_requests = int(total_req) if pd.notna(total_req) else 0
```

#### 2. DuckDB INSERT Pattern
```python
# Reset index for DuckDB compatibility
df = df.reset_index(drop=True)

# Use explicit registration
self.conn.register('temp_service_df', df)
self.conn.execute("INSERT INTO service_logs SELECT * FROM temp_service_df")
self.conn.unregister('temp_service_df')
```

#### 3. JSON Serialization for Claude
```python
# Use DateTimeEncoder for pandas/numpy types
result = json.dumps(data, cls=DateTimeEncoder)
```

## 📁 File References

- **Data Ingestion**: `data/ingestion/opensearch_client.py`, `data/ingestion/data_loader.py`
- **Database**: `data/database/duckdb_manager.py`
- **Analytics**: `analytics/degradation_detector.py`, `analytics/slo_calculator.py`, `analytics/trend_analyzer.py`, `analytics/metrics.py`
- **Agent**: `agent/claude_client.py`, `agent/function_tools.py`
- **UI**: `app.py`

## 🔄 Data Flow Summary

1. **User clicks "Refresh"** → OpenSearch → DuckDB (WRITE)
2. **Data persists** in DuckDB file
3. **User asks question** → Claude → Analytics Functions → DuckDB (READ)
4. **Results returned** → Claude synthesizes → User sees response
5. **No data changes** during chat - only during refresh

---

*For more details, see CLAUDE.md for critical code patterns and development workflows.*
