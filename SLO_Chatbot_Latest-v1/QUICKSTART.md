# SLO Chatbot - Quick Start Guide

## ✅ System Status

After ClickHouse migration (January 2026):
- **Data Source**: ClickHouse (read-only, pre-loaded)
- **Total Rows**: 8,759 hourly records
- **Services**: 122 unique transaction endpoints
- **Time Range**: Dec 31, 2025 - Jan 12, 2026 (12 days)
- **Granularity**: Hourly metrics
- **Test Results**: 38/38 passed ✅

---

## Quick Start (3 Steps)

### 1. Ensure ClickHouse is Running

```bash
# Check ClickHouse status
docker ps | grep clickhouse

# If not running, start it
docker start clickhouse-server

# Verify data exists
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"
# Expected: 8759
```

### 2. Activate Environment

```bash
# Navigate to project directory
cd /path/to/SLO_Chatbot_Latest-v1

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Run the Chatbot

```bash
streamlit run app.py
```

Open browser to: **http://localhost:8501**

---

## Using the Chatbot

### Chat Interface

The main interface is a chat window where you can ask natural language questions about service health, SLOs, and performance.

### Sample Questions

**🔍 Proactive Monitoring:**
```
"Which services have high burn rates?"
"Show services with exhausted error budgets"
"Which services are at risk - meeting 98% but failing 99%?"
"Predict which services will have issues today"
```

**📊 Health Analysis:**
```
"Show composite health scores for all services"
"Which services have timeliness issues?"
"Show the severity heatmap"
"Get service health overview"
"Which services are unhealthy?"
```

**📉 SLO Compliance:**
```
"Show services violating their SLO"
"Calculate error budget for GET /api/endpoint"
"What's the current SLI for GET /api/endpoint?"
"Show all services with burn rate > 2.0"
```

**⚡ Performance Analysis:**
```
"What are the slowest services by P99 latency?"
"Show volume trends for GET /api/endpoint over the past 7 days"
"Which services are degrading over the past week?"
"Show historical patterns for GET /api/endpoint"
"Detect anomalies in GET /api/endpoint"
```

**🔬 Advanced Analysis:**
```
"Compare error rates across GET /api/users, POST /api/orders, GET /api/products"
"Show me the aspirational SLO gap - services meeting 98% but failing 99%"
"Analyze breach vs error for GET /api/endpoint"
"Show services with budget exhausted (>100% consumed)"
```

---

## Example Conversations

### Example 1: Identifying At-Risk Services

**You:** "Which services have high burn rates?"

**Claude:** Based on the burn rate analysis, here are the top 5 services with the highest burn rates:

1. **GET /api/test-endpoint** - Burn rate: 102.04
   - Error rate: 100%
   - SLO target: 98%
   - Status: CRITICAL - budget consumption is extreme

2. **POST /api/critical-service** - Burn rate: 45.23
   - Error rate: 44.32%
   - SLO target: 98%
   - Status: WARNING - rapid budget consumption

[Additional services with analysis...]

**Recommended Actions:**
- Investigate GET /api/test-endpoint immediately - 100% error rate indicates complete service failure
- Review POST /api/critical-service for recent deployments or infrastructure issues
- Set up alerts for burn rate > 2.0 to catch issues earlier

---

### Example 2: Performance Deep Dive

**You:** "What are the slowest services by P99 latency?"

**Claude:** Here are the 5 slowest services based on P99 latency:

1. **GET /api/heavy-computation**
   - P99 Latency: 25.87 seconds
   - P95 Latency: 18.45 seconds
   - Average: 12.34 seconds
   - SLO Target: 1.0 second
   - Total Requests: 12,456
   - Status: ❌ VIOLATED (25.87x over SLO)

2. **POST /api/batch-process**
   - P99 Latency: 15.23 seconds
   - P95 Latency: 10.12 seconds
   - Average: 8.67 seconds
   - SLO Target: 1.0 second
   - Total Requests: 8,903
   - Status: ❌ VIOLATED (15.23x over SLO)

[Additional services...]

**Analysis:**
- The P99 latencies are significantly higher than averages, indicating occasional severe slowdowns
- All top 5 services exceed their 1-second SLO target
- Consider optimizing database queries, caching, or infrastructure scaling

---

### Example 3: Degradation Detection

**You:** "Which services are degrading over the past week?"

**Claude:** Degradation analysis (last 7 days vs previous 7 days):

Found **38 degrading services**. Top 5 by severity:

1. **GET /api/data-sets** - CRITICAL
   - Error rate change: +1992.7%
   - Baseline: 0.5%
   - Recent: 10.46%
   - Response time change: +15.3%
   - Severity: critical

2. **POST /api/bulk-import** - WARNING
   - Error rate change: +156.8%
   - Response time change: +89.2%
   - P99 change: +134.5%
   - Severity: warning

[Additional services...]

**Recommended Actions:**
- GET /api/data-sets requires immediate investigation - error rate increased 20x
- Review deployment history for the past 7 days
- Check for infrastructure changes or external dependencies

---

## Available Functions (20)

### Standard Analysis
1. `get_service_health_overview()` - System-wide health summary
2. `get_degrading_services(time_window_days)` - Week-over-week degradation
3. `get_slo_violations()` - Services currently violating SLO
4. `get_slowest_services(limit)` - Ranked by P99 latency
5. `get_top_services_by_volume(limit)` - High-traffic services
6. `get_service_summary(service_name)` - Comprehensive analysis
7. `get_current_sli(service_name)` - Current service level indicators
8. `calculate_error_budget(service_name)` - Error budget tracking
9. `predict_issues_today()` - ML-based predictions

### Advanced Functions
10. `get_services_by_burn_rate(limit)` - Proactive SLO risk monitoring
11. `get_aspirational_slo_gap()` - Services meeting 98%, failing 99%
12. `get_timeliness_issues()` - Batch job/scheduling problems
13. `get_breach_vs_error_analysis(service_name)` - Latency vs reliability
14. `get_budget_exhausted_services()` - Services over budget (>100%)
15. `get_composite_health_score()` - 0-100 health across 5 dimensions
16. `get_severity_heatmap()` - Red vs green indicator visualization

### Performance Patterns
17. `get_volume_trends(service_name, time_window_days)` - Traffic patterns
18. `get_historical_patterns(service_name)` - Statistical analysis
19. `get_anomalies(service_name, threshold_std)` - Anomaly detection
20. `compare_services(service_names)` - Multi-service comparison

---

## Understanding the Output

### Burn Rate
- **< 1.0**: Healthy - error rate below SLO target
- **1.0 - 2.0**: Warning - approaching SLO target
- **2.0 - 5.0**: High Risk - rapid budget consumption
- **> 5.0**: Critical - budget will exhaust quickly

### Error Budget
- **> 50% remaining**: Healthy
- **20-50% remaining**: Warning - monitor closely
- **10-20% remaining**: High Risk - reduce changes
- **< 10% remaining**: Critical - freeze deployments
- **0% (exhausted)**: SLO violated - incident response

### Health Status
- **HEALTHY**: All metrics within SLO targets
- **UNHEALTHY**: One or more metrics violated
- Check: `eb_health`, `response_health`, `timeliness_health`, `aspirational_eb_health`, `aspirational_response_health`

### Composite Health Score
- **90-100**: Excellent - all dimensions healthy
- **70-89**: Good - minor issues
- **50-69**: Fair - multiple dimensions unhealthy
- **30-49**: Poor - significant issues
- **0-29**: Critical - immediate action required

---

## Tips for Effective Use

### 1. Start Broad, Then Narrow
```
1. "Get service health overview"          # See system-wide status
2. "Which services are degrading?"        # Identify problem areas
3. "Show volume trends for [specific service]"  # Deep dive
```

### 2. Use Comparative Analysis
```
"Compare error rates across ServiceA, ServiceB, ServiceC"
```

### 3. Combine Multiple Metrics
```
"Show services with high burn rate AND degrading performance"
```

### 4. Investigate Patterns
```
"Show historical patterns for [service]"
"Detect anomalies in [service]"
```

### 5. Proactive Monitoring
```
"Predict which services will have issues today"
"Show aspirational SLO gap"
```

---

## Troubleshooting

### No Data Returned

**Symptoms**: Claude says "No data found" or returns empty results

**Solutions**:
```bash
# 1. Verify ClickHouse is running
docker ps | grep clickhouse

# 2. Check data exists
docker exec clickhouse-server clickhouse-client --query "SELECT COUNT(*) FROM transaction_metrics"

# 3. Check time range
docker exec clickhouse-server clickhouse-client --query "SELECT MIN(timestamp), MAX(timestamp) FROM transaction_metrics"
```

### Slow Responses

**Symptoms**: Queries take > 10 seconds

**Solutions**:
- ClickHouse queries should be fast (50-200ms)
- Slow responses are usually from Claude processing
- Try simpler questions first
- Check AWS Bedrock quota/limits

### Service Name Issues

**Symptoms**: "Service not found" errors

**Solutions**:
```bash
# List all available services
docker exec clickhouse-server clickhouse-client --query "SELECT DISTINCT transaction_name FROM transaction_metrics LIMIT 10"

# Service names are URLs like: "GET https://domain.com/api/endpoint"
# Use exact names when querying specific services
```

---

## Next Steps

1. **Explore the data**: Try the sample questions above
2. **Read the docs**: Check [README.md](README.md) for full feature list
3. **Run tests**: `python3 test_clickhouse_comprehensive.py`
4. **Customize**: Adjust SLO thresholds in `.env` if needed

---

**Need Help?**
- See [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Run `python3 test_clickhouse_comprehensive.py` to diagnose problems

---

**Happy monitoring!** 🚀
