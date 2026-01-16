# SLO Chatbot

AI-powered Service Level Objective (SLO) monitoring and analysis chatbot using Claude Sonnet 4.5 via AWS Bedrock.

**Latest Update (January 2026):** Migrated from OpenSearch to Platform API with 90+ metrics, unlimited pagination, and 5-60 day time windows. See [PLATFORM_API_MIGRATION.md](PLATFORM_API_MIGRATION.md) for details.

## Features

### Core Capabilities
- **Real-time Service Analysis**: Monitor service health, error rates, and response times across 90+ metrics
- **Proactive Burn Rate Monitoring**: Early warning system for SLO violations (burn rate >2.0 = high risk)
- **Multi-Tier SLO Tracking**: Standard (98%) and Aspirational (99%) SLO compliance monitoring
- **Degradation Detection**: Identify services degrading over week-long time windows
- **Predictive Analysis**: Predict which services are likely to have issues based on historical patterns
- **Error Budget Tracking**: Calculate and monitor error budget consumption with breach detection
- **Conversational Interface**: Natural language queries powered by Claude Sonnet 4.5
- **Interactive Dashboard**: Visualize service health metrics and trends

### Advanced Platform API Features
- **Unlimited Services**: No 10k limit - automatic pagination handles any number of services
- **Extended Time Windows**: Query 5-60 days of historical data (vs 4-hour OpenSearch limit)
- **Daily Aggregated Metrics**: Better for long-term trend analysis and pattern detection
- **Timeliness Tracking**: Monitor batch jobs and scheduled task performance
- **Composite Health Scoring**: Overall health (0-100) across 5 dimensions
- **Severity Heatmap**: Visual pattern recognition with red/green indicators
- **SLO Governance**: Track SLO approval status and compliance
- **Breach vs Error Analysis**: Distinguish latency issues from availability issues

## Architecture

```
┌─────────────────────┐
│   Streamlit UI      │
│   (Web Interface)   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Claude Sonnet 4.5 │
│   (AWS Bedrock)     │
│    20 Functions     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Function Executor  │
│  (Tool Calling)     │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────┐
│         Analytics Engine             │
├──────────────────────────────────────┤
│  • SLO Calculator (EB, Burn Rate)    │
│  • Degradation Detector (Week/Week)  │
│  • Trend Analyzer (Predictions)      │
│  • Metrics Aggregator (20 Functions) │
└──────────┬───────────────────────────┘
           │
┌──────────▼──────────┐
│     DuckDB          │
│  (OLAP Database)    │
│   90+ Columns       │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────────┐
│      Platform API                    │
│  (WM Error Budget Statistics)        │
├──────────────────────────────────────┤
│  • Keycloak OAuth2 (Auto-Refresh)    │
│  • Unlimited Services (Pagination)   │
│  • 5-60 Day Windows                  │
│  • Daily Aggregated Metrics          │
└──────────────────────────────────────┘
```

## Important Documentation

- **[PLATFORM_API_MIGRATION.md](PLATFORM_API_MIGRATION.md)** - ⭐ **Complete migration guide (OpenSearch → Platform API)**
- **README.md** (this file) - Main documentation
- **QUICKSTART.md** - Quick start guide with examples
- **PROJECT_SUMMARY.md** - Complete project overview
- **DATA_LIMITS_GUIDE.md** - ⚠️ Deprecated (OpenSearch specific)

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** in `.env` (copy from `.env.example`):
```bash
# AWS Bedrock (for Claude Sonnet 4.5)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

# Keycloak Authentication (for Platform API)
KEYCLOAK_URL=https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token
KEYCLOAK_USERNAME=your_keycloak_username
KEYCLOAK_PASSWORD=your_keycloak_password
KEYCLOAK_CLIENT_ID=web_app

# Platform API Configuration
PLATFORM_API_URL=https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/health
PLATFORM_API_APPLICATION=WMPlatform
PLATFORM_API_PAGE_SIZE=200
PLATFORM_API_VERIFY_SSL=False

# Logging
LOG_LEVEL=INFO
```

3. **Run tests** (optional):
```bash
python test_platform_api.py
```

## Usage

### Start the Chatbot

```bash
streamlit run app.py
```

The web interface will open at `http://localhost:8501`

### Using the Dashboard

1. **Select Time Range**: Choose from 5 days, 7 days, 30 days, 60 days, or custom range
2. **Load Data**: Click "🔄 Refresh from Platform API" in the sidebar to fetch aggregated SLO metrics
3. **View Health Summary**: Check for unhealthy services and high burn rates
4. **Chat**: Ask Claude questions about service health, SLOs, and patterns

### Sample Questions

**Proactive Monitoring:**
- "Which services have high burn rates?" (>2.0 = high risk)
- "Show services with exhausted error budgets"
- "Which services are at risk?" (meeting 98% but failing 99%)

**Health Analysis:**
- "Show composite health scores for all services"
- "Which services have timeliness issues?" (batch jobs, scheduling)
- "Show the severity heatmap"

**SLO Compliance:**
- "Show services violating their SLO"
- "Calculate error budget for [service name]"
- "What's the current SLO governance status?"

**Performance:**
- "What are the slowest services by P99 latency?"
- "Show volume trends for [service name]"
- "Which services are degrading over the past week?"

## Components

### Data Layer
- **DuckDBManager**: OLAP database for fast analytical queries (90+ columns)
- **DataLoader**: Parse Platform API responses into structured DataFrames
- **KeycloakAuthManager**: OAuth2 authentication with auto-refresh (every 4 minutes)
- **PlatformAPIClient**: Platform API client with automatic pagination

### Analytics Layer
- **SLOCalculator**: SLI/SLO calculations, error budgets, burn rates, breach detection
- **DegradationDetector**: Identify degrading services using week-over-week time-series analysis
- **TrendAnalyzer**: Predictive analysis and historical patterns (2+ weeks of data)
- **MetricsAggregator**: Service metrics, aggregations, and 8 new Platform API functions

### Agent Layer
- **ClaudeClient**: AWS Bedrock integration with streaming support
- **FunctionExecutor**: Execute analytics functions via tool calling
- **TOOLS**: 20 analytics functions for Claude (23 total, 3 deprecated)

### UI Layer
- **Streamlit App**: Web-based chat interface with 5-60 day time range selector

## Analytics Functions

The chatbot has access to **20 analytics functions** (3 deprecated with Platform API):

### Standard Performance & Health (7 functions)
1. `get_service_health_overview` - System-wide health summary
2. `get_degrading_services` - Week-over-week degradation detection
3. `get_slo_violations` - Services currently violating SLO
4. `get_slowest_services` - Ranked by P99 latency
5. `get_top_services_by_volume` - High-traffic services
6. `get_service_summary` - Comprehensive single-service analysis
7. `get_current_sli` - Current service level indicators

### Platform API Advanced Functions (8 new functions)
8. `get_services_by_burn_rate` - Proactive SLO risk monitoring (>2.0 = high risk)
9. `get_aspirational_slo_gap` - At-risk services (meeting 98%, failing 99%)
10. `get_timeliness_issues` - Batch job/scheduling problems
11. `get_breach_vs_error_analysis` - Latency vs reliability root cause analysis
12. `get_budget_exhausted_services` - Services over budget (>100%)
13. `get_composite_health_score` - Overall health (0-100) across 5 dimensions
14. `get_severity_heatmap` - Red vs green indicator visualization
15. `get_slo_governance_status` - SLO approval tracking

### Performance Patterns (5 functions)
16. `calculate_error_budget` - Error budget tracking with time windows
17. `get_volume_trends` - Request volume patterns
18. `predict_issues_today` - ML-based predictions using historical patterns
19. `get_historical_patterns` - Statistical analysis
20. `get_error_prone_services` - High error rate services

### Deprecated (3 functions - error_logs table no longer exists)
❌ `get_error_code_distribution` - Not available with Platform API
❌ `get_top_errors` - Use error_count from service_logs instead
❌ `get_error_details_by_code` - Data is aggregated, no individual error logs

## Configuration

Edit `utils/config.py` to customize:
- **SLO thresholds**: Standard (98%) and Aspirational (99%) targets
- **Burn rate thresholds**: High risk (>2.0), Critical (>5.0)
- **Degradation detection**: Week-over-week comparison windows
- **Time windows**: Default 5 days, Max 60 days
- **Database paths**: DuckDB file location
- **Platform API settings**: URL, application, page size

## No Vector Database Needed!

This implementation **does NOT use Pinecone or vector embeddings** because:

✅ **Structured data**: Metrics have well-defined schema (error_rate, burn_rate, health indicators)
✅ **Time-series queries**: Need aggregations, not semantic search
✅ **Fast analytics**: DuckDB is optimized for OLAP workloads
✅ **Simpler architecture**: Direct SQL queries are faster and more precise
✅ **90+ columns**: Pre-calculated metrics from Platform API

Vector databases are for **unstructured text** semantic search. Our SLO data is **highly structured** and benefits from traditional OLAP engines.

## Platform API Benefits

### No Data Limits
- **Unlimited Services**: Automatic pagination handles any number of services
- **No 10k Cap**: Platform API doesn't have OpenSearch's 10,000 result limit
- **Efficient Pagination**: Configurable page size (default 200 services per page)

### Extended Time Windows
✅ **Time Range Selection**:
- Last 5 days
- Last 7 days (default)
- Last 30 days
- Last 60 days
- Custom date range (max 60 days)

✅ **Daily Aggregated Data**: Better for long-term trend analysis

**Note**: Daily granularity enables 2+ months of historical analysis for pattern detection and prediction.

## Future Enhancements

- [ ] Real-time burn rate alerting (Slack/email notifications)
- [ ] Automated SLO governance workflow (approval tracking)
- [ ] Custom composite health score weights
- [ ] Export dashboard reports (PDF, CSV)
- [ ] Multi-user authentication with RBAC
- [ ] Prometheus/Grafana integration
- [ ] Burn rate trend prediction using ML
- [ ] Service dependency mapping
- [ ] Custom alert thresholds per service

## License

MIT
