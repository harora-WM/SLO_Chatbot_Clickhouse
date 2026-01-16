# SLO Chatbot - Documentation Index

Complete guide to all documentation files after ClickHouse migration (January 2026).

## 🚀 Start Here

### For New Users
1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Step-by-step setup (10 minutes)
2. **[README.md](README.md)** - Main documentation and features
3. **[QUICKSTART.md](QUICKSTART.md)** - Usage examples and sample questions

### For Existing Users (After Migration)
1. **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Migration sign-off and changes
2. **[CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md)** - Detailed migration guide
3. **[_deprecated/README.md](_deprecated/README.md)** - Old architecture reference

## 📚 Documentation by Category

### Setup & Installation

| Document | Purpose | Audience |
|----------|---------|----------|
| **[SETUP_GUIDE.md](SETUP_GUIDE.md)** | Complete setup from scratch | New users |
| **[.env.example](.env.example)** | Environment configuration template | All users |
| **[requirements.txt](requirements.txt)** | Python dependencies | Developers |

**Time to setup**: ~10 minutes
**Prerequisites**: Docker, Python 3.12+, AWS Bedrock access

### Usage & Examples

| Document | Purpose | Audience |
|----------|---------|----------|
| **[QUICKSTART.md](QUICKSTART.md)** | Sample questions and examples | All users |
| **[README.md](README.md)** | Feature documentation | All users |

**Key features**: 20 analytics functions, natural language queries, hourly metrics

### Migration & Architecture

| Document | Purpose | Audience |
|----------|---------|----------|
| **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** | Migration status and test results | Technical users |
| **[CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md)** | Detailed migration guide | Developers |
| **[_deprecated/README.md](_deprecated/README.md)** | Old Platform API architecture | Developers |

**Migration status**: ✅ Complete (38/38 tests passed)
**Date**: January 15, 2026

### Testing & Troubleshooting

| Document | Purpose | Audience |
|----------|---------|----------|
| **[test_clickhouse_comprehensive.py](test_clickhouse_comprehensive.py)** | Comprehensive test suite (38 tests) | Developers |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Common issues and solutions | All users |

**Test coverage**: Connection, fields, analytics, data quality
**Run tests**: `python3 test_clickhouse_comprehensive.py`

### Historical Documentation (Deprecated)

| Document | Status | Notes |
|----------|--------|-------|
| **PLATFORM_API_MIGRATION.md** | Deprecated | OpenSearch → Platform API (Jan 2026) |
| **DATA_LIMITS_GUIDE.md** | Deprecated | OpenSearch limitations |
| **DEPRECATED.md** | Deprecated | Old files list |
| **OPENSEARCH_LIMITS_SUMMARY.md** | Deprecated | OpenSearch specific |
| **MIGRATION_STEPS.md** | Deprecated | Old migration steps |

These files are kept for historical reference but no longer apply to the current ClickHouse architecture.

## 📖 Documentation Quick Reference

### By Use Case

**"I'm new and want to get started"**
→ [SETUP_GUIDE.md](SETUP_GUIDE.md)

**"I want to use the chatbot"**
→ [QUICKSTART.md](QUICKSTART.md)

**"I need to understand the features"**
→ [README.md](README.md)

**"I need to configure the environment"**
→ [.env.example](.env.example)

**"Something isn't working"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**"I want to understand the migration"**
→ [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)

**"I need technical details about the migration"**
→ [CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md)

**"I want to verify everything works"**
→ Run: `python3 test_clickhouse_comprehensive.py`

**"I need to understand the old architecture"**
→ [_deprecated/README.md](_deprecated/README.md)

### By Role

**End User**
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Get it running
2. [QUICKSTART.md](QUICKSTART.md) - Learn to use it
3. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Fix issues

**Developer**
1. [README.md](README.md) - Architecture overview
2. [CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md) - Technical details
3. [test_clickhouse_comprehensive.py](test_clickhouse_comprehensive.py) - Test suite
4. [_deprecated/README.md](_deprecated/README.md) - Old architecture

**DevOps/SRE**
1. [SETUP_GUIDE.md](SETUP_GUIDE.md) - Deployment guide
2. [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md) - Migration status
3. [.env.example](.env.example) - Configuration reference

## 🔧 Configuration Files

### Required Configuration

**`.env`** (copy from `.env.example`)
- **Required**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- **Optional**: All other variables have defaults

### Python Dependencies

**`requirements.txt`**
- Core: `streamlit`, `clickhouse-connect`, `boto3`, `pandas`
- Analytics: `numpy`, `plotly`, `altair`
- Deprecated: `duckdb` (marked as deprecated)

### Streamlit Secrets (Cloud Deployment)

**`.streamlit/secrets.toml`** (not in repo)
```toml
AWS_ACCESS_KEY_ID = "your_key"
AWS_SECRET_ACCESS_KEY = "your_secret"
CLICKHOUSE_HOST = "your-host"
```

## 📊 Data Documentation

### ClickHouse Schema

**Database**: ClickHouse (Docker container)
**Table**: `transaction_metrics`
**Rows**: 8,759 (hourly records)
**Services**: 122 unique transactions
**Time Range**: Dec 31, 2025 - Jan 12, 2026 (12 days)
**Fields**: 80+ metrics per row

**Key fields documented in**: [CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md#key-changes)

### Data Pipeline

**Source**: kafka_put project
**Pipeline**: Platform API → Kafka → ClickHouse
**Documentation**: See `kafka_put/CLAUDE.md`

## 🧪 Testing Documentation

### Test Suite

**File**: `test_clickhouse_comprehensive.py`
**Tests**: 38 tests across 7 categories
**Status**: 38/38 passed ✅

**Test categories:**
1. ClickHouse connection (5 tests)
2. Field existence (17 tests)
3. MetricsAggregator (6 tests)
4. SLOCalculator (4 tests)
5. DegradationDetector (2 tests)
6. TrendAnalyzer (3 tests)
7. Data quality (3 tests)

**Run tests**: `python3 test_clickhouse_comprehensive.py`

## 📝 Code Documentation

### Main Modules

**`app.py`**
- Streamlit UI
- System prompt for Claude
- Chat interface

**`data/database/clickhouse_manager.py`**
- Read-only ClickHouse client
- Automatic field mapping
- Query interface

**`analytics/`**
- `metrics.py` - 13 functions
- `slo_calculator.py` - 4 functions
- `degradation_detector.py` - 3 functions
- `trend_analyzer.py` - 6 functions

**`agent/`**
- `claude_client.py` - AWS Bedrock integration
- `function_tools.py` - 20 tool definitions

### Deprecated Modules

**`_deprecated/data/ingestion/`**
- `platform_api_client.py` - Platform API client
- `keycloak_auth.py` - OAuth2 authentication
- `data_loader.py` - Data parsing
- `opensearch_client.py` - Legacy OpenSearch

**`_deprecated/data/database/`**
- `duckdb_manager.py` - Old OLAP database

## 🔄 Version History

### January 15, 2026 - ClickHouse Migration
- ✅ Migrated from DuckDB + Platform API to ClickHouse
- ✅ Updated all documentation
- ✅ 38/38 tests passing
- ✅ Production ready

### January 2026 - Platform API Migration
- Migrated from OpenSearch to Platform API
- Extended time windows (4 hours → 5-60 days)
- Unlimited services (removed 10k limit)
- 90+ metrics (vs 26 with OpenSearch)

### December 2025 - Initial Version
- OpenSearch integration
- Basic analytics
- 15 functions

## 📞 Support Resources

### Documentation
- [README.md](README.md) - Main documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Installation guide

### Testing
- Run: `python3 test_clickhouse_comprehensive.py`
- Expected: 38/38 tests passed

### Verification
```bash
# Check ClickHouse
docker ps | grep clickhouse

# Check data
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# Check Python deps
python -c "import streamlit, clickhouse_connect, boto3; print('OK')"

# Check AWS
python -c "import boto3; boto3.client('bedrock-runtime', region_name='ap-south-1'); print('OK')"
```

## 📚 External Resources

### ClickHouse
- Official docs: https://clickhouse.com/docs
- Python client: https://github.com/ClickHouse/clickhouse-connect

### AWS Bedrock
- Claude docs: https://docs.anthropic.com/claude/reference/
- Bedrock docs: https://docs.aws.amazon.com/bedrock/

### Streamlit
- Official docs: https://docs.streamlit.io
- Cloud deployment: https://streamlit.io/cloud

## 🗂️ File Organization

```
SLO_Chatbot_Latest-v1/
├── README.md                       ⭐ Start here
├── SETUP_GUIDE.md                  ⭐ Setup instructions
├── QUICKSTART.md                   ⭐ Usage examples
├── DOCUMENTATION_INDEX.md          ⭐ This file
│
├── MIGRATION_COMPLETE.md           📋 Migration sign-off
├── CLICKHOUSE_MIGRATION.md         📋 Detailed migration guide
├── TROUBLESHOOTING.md              🔧 Common issues
│
├── .env.example                    ⚙️ Configuration template
├── requirements.txt                ⚙️ Dependencies
├── app.py                          💻 Main application
├── test_clickhouse_comprehensive.py 🧪 Test suite
│
├── analytics/                      📊 Analytics modules
├── agent/                          🤖 Claude integration
├── data/database/                  🗄️ ClickHouse manager
├── utils/                          🛠️ Utilities
│
└── _deprecated/                    📦 Old architecture
    ├── README.md                   📋 Deprecation guide
    ├── data/database/              (Old DuckDB)
    └── data/ingestion/             (Old Platform API)
```

## 🎯 Documentation Status

| Category | Status | Last Updated |
|----------|--------|--------------|
| Setup Guide | ✅ Complete | Jan 15, 2026 |
| User Guide | ✅ Complete | Jan 15, 2026 |
| API Docs | ✅ Complete | Jan 15, 2026 |
| Migration Guide | ✅ Complete | Jan 15, 2026 |
| Test Suite | ✅ Complete | Jan 15, 2026 |
| Configuration | ✅ Complete | Jan 15, 2026 |
| Troubleshooting | ✅ Complete | Jan 15, 2026 |

## 🚀 Next Steps

1. **New users**: Start with [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. **Existing users**: Check [MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)
3. **Developers**: Review [CLICKHOUSE_MIGRATION.md](CLICKHOUSE_MIGRATION.md)
4. **Everyone**: Try [QUICKSTART.md](QUICKSTART.md) examples

---

**Documentation Last Updated**: January 15, 2026
**Version**: 2.0.0 (ClickHouse Migration)
**Status**: Production Ready ✅
