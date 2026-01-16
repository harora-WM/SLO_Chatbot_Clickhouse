# SLO Chatbot

AI-powered Service Level Objective (SLO) monitoring and analysis chatbot using **Claude Sonnet 4.5** via AWS Bedrock and **ClickHouse** for real-time metrics.

**Latest Update (January 2026):** ✅ Migrated to ClickHouse with hourly granularity, read-only access, and streamlined architecture. See [CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md) and [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) for details.

## 🚀 Quick Start

### Prerequisites
1. **Docker** - For ClickHouse database
2. **Python 3.12+** - For the application
3. **AWS Bedrock Access** - For Claude Sonnet 4.5

### Setup (5 minutes)

```bash
# 1. Clone the repository
cd /path/to/SLO_Chatbot_Latest-v1

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Start ClickHouse (from kafka_put project)
cd ../kafka_put
./clickhouse_setup.sh
# Or if already set up: docker start clickhouse-server

# 4. Load data into ClickHouse (from kafka_put project)
python kafka_producer.py           # Fetch from Platform API → Kafka
python kafka_to_clickhouse.py      # Load Kafka → ClickHouse (Ctrl+C after done)

# 5. Configure environment (back to SLO_Chatbot)
cd ../SLO_Chatbot_Latest-v1
cp .env.example .env
# Edit .env and add your AWS credentials:
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret

# 6. Run the chatbot
streamlit run app.py

# Access at: http://localhost:8501
```

## ✨ Features

### Core Capabilities
- **🔍 Real-time Service Analysis**: Monitor 122 services with hourly granularity
- **⚡ Proactive Burn Rate Monitoring**: Early warning for SLO violations (burn rate >2.0 = high risk)
- **📊 Multi-Tier SLO Tracking**: Standard (98%) and Aspirational (99%) compliance
- **📉 Degradation Detection**: Identify services degrading over 7-day windows
- **🔮 Predictive Analysis**: ML-based predictions for at-risk services
- **💰 Error Budget Tracking**: Real-time budget consumption monitoring
- **💬 Conversational Interface**: Natural language queries powered by Claude Sonnet 4.5

### Advanced Analytics (20 Functions)
- **Burn Rate Rankings**: Identify fastest-deteriorating services
- **Aspirational SLO Gap**: Services meeting 98% but failing 99%
- **Timeliness Issues**: Batch job and scheduled task monitoring
- **Breach vs Error Analysis**: Distinguish latency from availability issues
- **Composite Health Scoring**: 0-100 health across 5 dimensions
- **Severity Heatmap**: Visual red/green indicator patterns
- **Anomaly Detection**: Z-score based outlier identification
- **Historical Patterns**: Statistical analysis and trends

## 📊 Architecture

### Current (ClickHouse)
```
┌─────────────────────┐
│   Streamlit UI      │
│  (Web Interface)    │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│ Claude Sonnet 4.5   │
│   (AWS Bedrock)     │
│   20 Functions      │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────┐
│     Analytics Engine             │
├──────────────────────────────────┤
│ • SLOCalculator                  │
│ • DegradationDetector            │
│ • TrendAnalyzer                  │
│ • MetricsAggregator              │
└──────────┬───────────────────────┘
           │
┌──────────▼──────────┐
│   ClickHouse        │
│   (Read-Only)       │
│   8,759 rows        │
│   122 services      │
│   80+ columns       │
└──────────┬──────────┘
           │
    [Pre-loaded via kafka_put pipeline]
```

### Data Pipeline (kafka_put)
```
Platform API → Keycloak OAuth2 → Kafka → ClickHouse
     │                             │         ↑
     └─ Daily Aggregations         └─ Hourly Records
```

## 📁 Project Structure

```
SLO_Chatbot_Latest-v1/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
│
├── agent/
│   ├── claude_client.py            # AWS Bedrock integration
│   └── function_tools.py           # Tool calling (20 functions)
│
├── analytics/
│   ├── metrics.py                  # MetricsAggregator (13 functions)
│   ├── slo_calculator.py           # SLO & error budget (4 functions)
│   ├── degradation_detector.py     # Week-over-week analysis
│   └── trend_analyzer.py           # Predictions & patterns
│
├── data/
│   └── database/
│       └── clickhouse_manager.py   # ClickHouse client (read-only)
│
├── utils/
│   ├── config.py                   # Configuration management
│   └── logger.py                   # Logging setup
│
├── _deprecated/                    # Old Platform API components
│   ├── README.md                   # Migration reference
│   ├── data/database/
│   │   └── duckdb_manager.py       # Old OLAP DB
│   └── data/ingestion/
│       ├── platform_api_client.py  # API client
│       ├── keycloak_auth.py        # OAuth2 auth
│       └── data_loader.py          # Data parsing
│
└── docs/
    ├── CLICKHOUSE_MIGRATION.md     # Detailed migration guide
    ├── MIGRATION_COMPLETE.md       # Migration sign-off
    ├── README.md                   # This file
    ├── QUICKSTART.md               # Quick examples
    └── TROUBLESHOOTING.md          # Common issues
```

## 🔧 Configuration

### Required Environment Variables

Only **2 required** variables (add to `.env`):

```bash
# AWS Bedrock (Required)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
```

### Optional Configuration

All other variables have sensible defaults:

```bash
# AWS Region (Default: ap-south-1)
AWS_REGION=ap-south-1

# Claude Model (Default: Sonnet 4.5)
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# ClickHouse Connection (Default: localhost Docker)
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=

# SLO Thresholds (Industry standard defaults)
DEFAULT_ERROR_SLO_THRESHOLD=1.0          # 1% error rate
DEFAULT_RESPONSE_TIME_SLO=1.0            # 1 second
DEFAULT_SLO_TARGET_PERCENT=98            # 98% compliance
ASPIRATIONAL_SLO_TARGET_PERCENT=99       # 99% aspirational

# Degradation Detection
DEGRADATION_WINDOW_DAYS=7                # 7-day comparison
DEGRADATION_THRESHOLD_PERCENT=20         # 20% change threshold

# Logging
LOG_LEVEL=INFO
```

See `.env.example` for full documentation.

## 📖 Usage Examples

### Sample Questions

**Proactive Monitoring:**
```
"Which services have high burn rates?"
"Show services with exhausted error budgets"
"Which services are at risk (meeting 98% but failing 99%)?"
"Predict which services will have issues today"
```

**Health Analysis:**
```
"Show composite health scores for all services"
"Which services have timeliness issues?"
"Show the severity heatmap"
"Get service health overview"
```

**SLO Compliance:**
```
"Show services violating their SLO"
"Calculate error budget for [service name]"
"What's the current SLI for [service name]?"
"Show burn rate for all services"
```

**Performance:**
```
"What are the slowest services by P99 latency?"
"Show volume trends for [service name]"
"Which services are degrading over the past week?"
"Show historical patterns for [service name]"
"Detect anomalies in [service name]"
```

### API Functions (20 Available)

**Standard Analysis:**
- `get_service_health_overview()` - System-wide summary
- `get_degrading_services(time_window_days)` - Week-over-week
- `get_slo_violations()` - Active violations
- `get_slowest_services(limit)` - P99 rankings
- `get_top_services_by_volume(limit)` - Traffic leaders
- `get_service_summary(service_name)` - Complete analysis
- `get_current_sli(service_name)` - Current indicators
- `calculate_error_budget(service_name)` - Budget tracking
- `predict_issues_today()` - ML predictions

**Advanced Functions:**
- `get_services_by_burn_rate(limit)` - Burn rate rankings
- `get_aspirational_slo_gap()` - 98% vs 99% gap
- `get_timeliness_issues()` - Batch job problems
- `get_breach_vs_error_analysis(service_name)` - Latency vs errors
- `get_budget_exhausted_services()` - Over-budget services
- `get_composite_health_score()` - 0-100 health scores
- `get_severity_heatmap()` - Red/green indicators

**Performance Patterns:**
- `get_volume_trends(service_name, time_window_days)` - Traffic patterns
- `get_historical_patterns(service_name)` - Statistical analysis
- `get_anomalies(service_name, threshold_std)` - Outlier detection
- `compare_services(service_names)` - Multi-service comparison

## 🗄️ Data

### ClickHouse Dataset
- **Source**: kafka_put pipeline (Platform API → Kafka → ClickHouse)
- **Granularity**: Hourly metrics
- **Time Range**: Dec 31, 2025 - Jan 12, 2026 (12 days)
- **Total Rows**: 8,759 (hourly records)
- **Services**: 122 unique transaction endpoints
- **Fields**: 80+ metrics per row

### Key Metrics
**Core:**
- transaction_name, timestamp, total_count, error_count, success_count
- error_rate, success_rate, avg_response_time

**Percentiles:**
- percentile_25, percentile_50, percentile_75, percentile_95, percentile_99

**SLO Metrics:**
- short_target_slo (98%), aspirational_slo (99%)
- response_slo (latency target)

**Error Budget:**
- eb_consumed_percent, eb_allocated_percent, eb_left_percent
- eb_health (HEALTHY/UNHEALTHY), eb_breached

**Advanced:**
- timeliness_health, response_health
- aspirational_eb_health, aspirational_response_health
- eb_severity, response_severity (color codes)

### Updating Data

To refresh the dataset:

```bash
cd ../kafka_put

# 1. Re-fetch from Platform API
python kafka_producer.py

# 2. Re-load to ClickHouse
python kafka_to_clickhouse.py

# Note: May need to update consumer group ID if re-consuming
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run test suite (38 tests)
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

### Test Coverage
- ClickHouse connection (5 tests)
- Field existence (17 tests)
- MetricsAggregator (6 tests)
- SLOCalculator (4 tests)
- DegradationDetector (2 tests)
- TrendAnalyzer (3 tests)
- Data quality (3 tests)

## 🔍 Troubleshooting

### Common Issues

**1. ClickHouse Not Running**
```bash
# Check status
docker ps | grep clickhouse

# Start if stopped
docker start clickhouse-server

# Setup if not exists
cd ../kafka_put
./clickhouse_setup.sh
```

**2. No Data in ClickHouse**
```bash
# Verify data exists
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# Expected: 8759

# If zero, load data:
cd ../kafka_put
python kafka_producer.py
python kafka_to_clickhouse.py
```

**3. AWS Bedrock Authentication Errors**
```bash
# Verify credentials in .env
cat .env | grep AWS_

# Test AWS connection
python3 -c "import boto3; print(boto3.client('bedrock-runtime', region_name='ap-south-1').meta.region_name)"
```

**4. Module Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**5. Streamlit Port Already in Use**
```bash
# Use different port
streamlit run app.py --server.port 8502
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

## 📚 Documentation

### Main Documentation
- **[README.md](README.md)** (this file) - Main documentation
- **[CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md)** - Detailed migration guide
- **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Migration sign-off & test results
- **[.env.example](.env.example)** - Configuration template

### Additional Guides
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start with examples
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[_deprecated/README.md](_deprecated/README.md)** - Old architecture reference

### Historical Documentation (Deprecated)
- **PLATFORM_API_MIGRATION.md** - OpenSearch → Platform API migration (Jan 2026)
- **DATA_LIMITS_GUIDE.md** - OpenSearch limitations (no longer relevant)
- **DEPRECATED.md** - Deprecated files list

## 🚢 Deployment

### Local Development
```bash
streamlit run app.py
# Access at: http://localhost:8501
```

### Streamlit Cloud

1. **Push to GitHub**
2. **Deploy on Streamlit Cloud**: https://streamlit.io/cloud
3. **Add secrets** in Streamlit Cloud dashboard (Settings → Secrets):
```toml
AWS_ACCESS_KEY_ID = "your_key"
AWS_SECRET_ACCESS_KEY = "your_secret"
AWS_REGION = "ap-south-1"
CLICKHOUSE_HOST = "your-clickhouse-host"
CLICKHOUSE_PORT = 8123
```

### Docker Deployment

```bash
# Build image
docker build -t slo-chatbot .

# Run container
docker run -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  slo-chatbot
```

## 📊 Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Query Time** | 50-200ms | ClickHouse queries |
| **Initial Load** | 0s | Pre-loaded data |
| **Memory Usage** | 150MB | Streamlit + Analytics |
| **Response Time** | 2-5s | Claude + Analytics |
| **Services** | 122 | Concurrent monitoring |
| **Data Points** | 8,759 | Hourly records |

## 🛠️ Development

### Adding New Analytics Functions

1. **Add function to analytics module** (e.g., `metrics.py`)
2. **Add wrapper in FunctionExecutor** (`agent/function_tools.py`)
3. **Register in TOOLS list** (`agent/function_tools.py`)
4. **Update system prompt** (`app.py`)
5. **Test via Streamlit**

Example:
```python
# In analytics/metrics.py
def my_new_function(self, param: str) -> Dict[str, Any]:
    sql = "SELECT * FROM transaction_metrics WHERE ..."
    df = self.db_manager.query(sql)
    return {'result': df.to_dict()}

# In agent/function_tools.py
def my_new_function(self, param: str) -> Dict[str, Any]:
    return self.metrics_aggregator.my_new_function(param)
```

### Code Style
- Use type hints for all functions
- Follow NaN handling pattern: `int(val) if pd.notna(val) else 0`
- Log errors with `logger.error()`
- Document all functions with docstrings

## 🔄 Migration History

### January 2026: ClickHouse Migration ✅
- **From**: DuckDB + Platform API (daily aggregations, 5-60 days)
- **To**: ClickHouse (hourly data, 12-day fixed window)
- **Benefits**: Faster queries, hourly granularity, simplified architecture
- **Status**: Complete - 38/38 tests passed

### January 2026: Platform API Migration ✅
- **From**: OpenSearch (4-hour window, 10k limit)
- **To**: Platform API (5-60 days, unlimited services)
- **Benefits**: Extended time windows, unlimited services, 90+ metrics
- **Status**: Complete - deprecated after ClickHouse migration

## 📞 Support

### Getting Help
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Run `python3 test_clickhouse_comprehensive.py` to diagnose issues
- Review logs in console output

### Reporting Issues
Include:
1. Error message
2. Steps to reproduce
3. Environment (Python version, OS)
4. Test results (`test_clickhouse_comprehensive.py`)

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- **AWS Bedrock** - Claude Sonnet 4.5 API
- **ClickHouse** - Fast OLAP database
- **Streamlit** - Web UI framework
- **Kafka** - Data streaming (kafka_put pipeline)

---

**Ready to start?** Run `streamlit run app.py` 🚀
