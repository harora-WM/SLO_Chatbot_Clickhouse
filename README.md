# SLO Monitoring System

Complete data pipeline and AI-powered Service Level Objective (SLO) monitoring system using **Kafka**, **ClickHouse**, and **Claude Sonnet 4.5**.

```
Platform API → Kafka → ClickHouse → Claude AI Chatbot → Real-time SLO Insights
```

## 🚀 Overview

This repository contains two integrated projects that work together:

### 1. Data Pipeline (`pipeline/`)
Ingests transaction metrics from the Watermelon Platform API, streams through Kafka, and loads into ClickHouse for analysis.

- **OAuth2 authentication** via Keycloak
- **Kafka streaming** with AWS EC2 broker
- **ClickHouse storage** with 80+ metrics per service
- **Hourly granularity** across 122 services

### 2. SLO Chatbot (`chatbot/`)
AI-powered monitoring application using Claude Sonnet 4.5 to analyze SLO compliance, error budgets, and service health.

- **Natural language queries** - Ask questions in plain English
- **20 analytics functions** - Burn rate, degradation, predictions
- **Multi-tier SLO tracking** - Standard (98%) + Aspirational (99%)
- **Real-time insights** - Streaming responses from Claude

## 📁 Project Structure

```
slo-monitoring/
├── README.md                    # This file
├── CLAUDE.md                   # Developer guide for Claude Code
├── requirements.txt            # Unified dependencies
├── .gitignore
│
├── pipeline/                   # Data ingestion pipeline
│   ├── keycloak_auth.py       # OAuth2 authentication
│   ├── kafka_producer.py      # API → Kafka ingestion
│   ├── kafka_to_clickhouse.py # Kafka → ClickHouse loader
│   └── clickhouse_setup.sh    # Docker setup script
│
├── chatbot/                    # SLO monitoring chatbot
│   ├── app.py                 # Streamlit web UI
│   ├── requirements.txt       # Chatbot-specific deps
│   ├── .env.example          # Configuration template
│   │
│   ├── agent/                # Claude integration
│   │   ├── claude_client.py  # AWS Bedrock client
│   │   └── function_tools.py # 20 tool functions
│   │
│   ├── analytics/            # Analytics modules
│   │   ├── metrics.py        # Core metrics (13 functions)
│   │   ├── slo_calculator.py # SLO calculations (4 functions)
│   │   ├── degradation_detector.py
│   │   └── trend_analyzer.py # Predictions (6 functions)
│   │
│   ├── data/database/       # Data access layer
│   │   └── clickhouse_manager.py # Read-only ClickHouse client
│   │
│   ├── utils/               # Utilities
│   │   ├── config.py        # Configuration management
│   │   └── logger.py        # Logging setup
│   │
│   └── tests/               # Test files
│       └── test_clickhouse_comprehensive.py
│
└── docs/                    # Documentation
    └── OFFSET_EXPLORER_GUIDE.md # Kafka viewer guide
```

## 🎯 Quick Start

### Prerequisites

- **Docker Desktop** - For ClickHouse database
- **Python 3.12+** - For both projects
- **AWS Bedrock access** - For Claude Sonnet 4.5 (chatbot only)
- **Kafka broker access** - AWS EC2 instance (pre-configured)

### Step 1: Setup ClickHouse Database

```bash
# Navigate to repository root
cd slo-monitoring

# Setup ClickHouse using Docker
./pipeline/clickhouse_setup.sh

# Verify ClickHouse is running
docker ps | grep clickhouse
# Should show: clickhouse-server running on ports 8123, 9000
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended: one venv for both projects)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 3: Run Data Pipeline

```bash
# Fetch data from Platform API and load into Kafka
python pipeline/kafka_producer.py
# Expected: 122 messages published (~10-30 seconds)

# Load data from Kafka into ClickHouse
python pipeline/kafka_to_clickhouse.py
# Expected: 8,759 rows inserted (~30-60 seconds)
# Press Ctrl+C after all messages processed

# Verify data loaded
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759
```

### Step 4: Configure and Run Chatbot

```bash
# Navigate to chatbot directory
cd chatbot

# Configure environment variables
cp .env.example .env
# Edit .env and add:
#   AWS_ACCESS_KEY_ID=your_key
#   AWS_SECRET_ACCESS_KEY=your_secret

# Run the chatbot
streamlit run app.py

# Access at: http://localhost:8501
```

## 🛠️ System Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Keycloak OAuth2 → Platform API                             │
│  (122 services, 12 days, hourly metrics)                    │
│                    ↓                                         │
│  kafka_producer.py                                          │
│  (Parse nested JSON, 1 message per service)                 │
│                    ↓                                         │
│  Kafka Topic: services_series_12days                        │
│  (AWS EC2 broker, 122 messages)                             │
│                    ↓                                         │
│  kafka_to_clickhouse.py                                     │
│  (Flatten arrays, batch inserts)                            │
│                    ↓                                         │
└─────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              SHARED DATA LAYER (Docker)                     │
├─────────────────────────────────────────────────────────────┤
│  ClickHouse (localhost:8123)                                │
│  • Table: transaction_metrics                               │
│  • 8,759 rows (hourly granularity)                          │
│  • 122 unique services                                      │
│  • 80+ columns (SLO, error budget, latency, health)         │
└─────────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   SLO CHATBOT                               │
├─────────────────────────────────────────────────────────────┤
│  User Query → Streamlit UI                                  │
│                    ↓                                         │
│  Claude Sonnet 4.5 (AWS Bedrock)                            │
│  (Decides which of 20 tools to call)                        │
│                    ↓                                         │
│  Analytics Modules (SQL queries)                            │
│                    ↓                                         │
│  ClickHouse (read-only queries)                             │
│                    ↓                                         │
│  DataFrame → JSON → Claude                                  │
│                    ↓                                         │
│  Natural Language Response                                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Architecture Decisions

1. **Shared ClickHouse** - Pipeline writes, chatbot reads (no direct coupling)
2. **Hourly granularity** - More detailed than daily aggregations
3. **Read-only chatbot** - Never modifies source data
4. **In-memory DataFrames** - Temporary processing, never persisted
5. **Tool calling** - Claude decides which analytics function to execute

## 📊 Features

### Data Pipeline Features

- ✅ **OAuth2 Authentication** - Secure Keycloak integration
- ✅ **Kafka Streaming** - Reliable message queue
- ✅ **Automatic Flattening** - Nested JSON → flat rows
- ✅ **Batch Inserts** - 5,000 rows per batch for efficiency
- ✅ **Schema Auto-creation** - ClickHouse table created on first run
- ✅ **Docker Integration** - Persistent storage across restarts

### SLO Chatbot Features

- 🤖 **20 Analytics Functions**:
  - Burn rate rankings (proactive monitoring)
  - Aspirational SLO gap analysis (98% vs 99%)
  - Degradation detection (week-over-week)
  - ML-based predictions
  - Composite health scoring (0-100 across 5 dimensions)
  - Severity heatmaps
  - Budget exhaustion alerts

- 💬 **Natural Language Interface**:
  - Ask questions in plain English
  - Streaming responses from Claude
  - Multi-turn conversations with context

- 📈 **Advanced Analytics**:
  - Percentile tracking (P95, P99)
  - Error budget consumption
  - Timeliness monitoring (batch jobs)
  - Latency vs reliability analysis

## 🔧 Configuration

### Data Pipeline Configuration

**File:** `pipeline/kafka_producer.py`

```python
# Hardcoded configuration (edit for different environments)
APPLICATION_ID = 31854  # WMPlatform
START_TIME = 1767205800000  # Dec 31, 2025
END_TIME = 1768242540000    # Jan 12, 2026
KAFKA_BROKER = "ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092"
KAFKA_TOPIC = "services_series_12days"
```

### SLO Chatbot Configuration

**File:** `chatbot/.env`

```bash
# Required
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Optional (with defaults)
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
DEFAULT_SLO_TARGET_PERCENT=98
ASPIRATIONAL_SLO_TARGET_PERCENT=99
```

## 🧪 Testing

### Test Data Pipeline

```bash
# Test authentication
python pipeline/keycloak_auth.py
# Should save: service_health_response.json

# Verify Kafka connectivity
python3 -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']); print('Connected')"

# Verify ClickHouse data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759

docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(DISTINCT transaction_name) FROM transaction_metrics"
# Expected: 122
```

### Test SLO Chatbot

```bash
cd chatbot

# Run comprehensive test suite (38 tests)
python test_clickhouse_comprehensive.py
# Expected: 38/38 passed

# Test specific analytics function
python3 -c "
from analytics.metrics import MetricsAggregator
from data.database.clickhouse_manager import ClickHouseManager
m = MetricsAggregator(ClickHouseManager())
print('Services with high burn rate:', len(m.get_services_by_burn_rate(limit=10)))
"
```

## 📖 Usage Examples

### Sample Chatbot Queries

**Proactive Monitoring:**
```
"Which services have high burn rates?"
"Show services with exhausted error budgets"
"Predict which services will have issues today"
```

**Health Analysis:**
```
"Show composite health scores for all services"
"Which services have timeliness issues?"
"Get service health overview"
```

**Performance:**
```
"What are the slowest services by P99 latency?"
"Show volume trends for [service name]"
"Which services are degrading over the past week?"
```

### Direct ClickHouse Queries

```sql
-- Web UI: http://localhost:8123/play

-- Services by burn rate
SELECT
    transaction_name,
    AVG(error_rate) / MAX(short_target_slo) as burn_rate
FROM transaction_metrics
GROUP BY transaction_name
ORDER BY burn_rate DESC
LIMIT 10;

-- Error budget overview
SELECT
    transaction_name,
    AVG(eb_consumed_percent) as avg_consumed,
    any(eb_health) as health_status
FROM transaction_metrics
GROUP BY transaction_name
HAVING avg_consumed > 80;
```

## 🔍 Common Issues

### Issue: ClickHouse Not Running

```bash
# Check status
docker ps | grep clickhouse

# Start if stopped
docker start clickhouse-server

# If doesn't exist, run setup
./pipeline/clickhouse_setup.sh
```

### Issue: No Data in ClickHouse

```bash
# Verify table exists
docker exec clickhouse-server clickhouse-client --query "SHOW TABLES"

# Check row count
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# If zero, re-run pipeline
python pipeline/kafka_producer.py
python pipeline/kafka_to_clickhouse.py
```

### Issue: Chatbot Returns No Data

**Cause:** ClickHouse not running or empty table

```bash
# 1. Verify ClickHouse is running
docker ps | grep clickhouse

# 2. Check data exists
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# 3. Check time range matches data
docker exec clickhouse-server clickhouse-client --query "SELECT MIN(timestamp), MAX(timestamp) FROM transaction_metrics"
```

### Issue: Import Errors After Refactoring

The refactoring maintains all import paths. If you encounter issues:

```bash
# Ensure you're in the correct directory
cd slo-monitoring  # Repository root

# Run pipeline from root
python pipeline/kafka_producer.py

# Run chatbot from its directory
cd chatbot
streamlit run app.py
```

## 📚 Documentation

### Main Documentation
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer guide for Claude Code
- **[chatbot/README.md](chatbot/README.md)** - Chatbot user guide
- **[chatbot/QUICKSTART.md](chatbot/QUICKSTART.md)** - Quick examples
- **[docs/OFFSET_EXPLORER_GUIDE.md](docs/OFFSET_EXPLORER_GUIDE.md)** - Kafka viewer guide

### Migration Documentation
- **[chatbot/CLICKHOUSE_MIGRATION.md](chatbot/CLICKHOUSE_MIGRATION.md)** - ClickHouse migration details
- **[chatbot/MIGRATION_COMPLETE.md](chatbot/MIGRATION_COMPLETE.md)** - Migration sign-off

## 🚢 Deployment

### Local Development (Recommended)

```bash
# Terminal 1: Ensure ClickHouse is running
docker start clickhouse-server

# Terminal 2: Run chatbot
cd chatbot
streamlit run app.py
```

### Streamlit Cloud

1. Push to GitHub
2. Deploy on https://streamlit.io/cloud
3. Add secrets in dashboard (Settings → Secrets):

```toml
AWS_ACCESS_KEY_ID = "your_key"
AWS_SECRET_ACCESS_KEY = "your_secret"
AWS_REGION = "ap-south-1"
CLICKHOUSE_HOST = "your-clickhouse-host"
CLICKHOUSE_PORT = 8123
```

## 📊 Data Characteristics

- **8,759 rows** - Hourly metrics across 12 days
- **122 services** - Unique transaction endpoints
- **80+ columns** - SLO, error budget, latency percentiles, health indicators
- **Time range** - Dec 31, 2025 → Jan 12, 2026
- **Granularity** - 1 hour per row

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python chatbot/test_clickhouse_comprehensive.py`
5. Submit a pull request

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- **Anthropic** - Claude Sonnet 4.5 via AWS Bedrock
- **ClickHouse** - Fast OLAP database
- **Apache Kafka** - Reliable message streaming
- **Streamlit** - Interactive web UI framework

---

**Ready to start?** Follow the Quick Start guide above! 🚀

**Questions?** See [CLAUDE.md](CLAUDE.md) for developer documentation.
