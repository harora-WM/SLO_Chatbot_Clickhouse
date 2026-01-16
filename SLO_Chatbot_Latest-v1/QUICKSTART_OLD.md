# SLO Chatbot - Quick Start Guide

## System Test Results ✅

All tests passed successfully:
- **Data Loading**: ✅ 150 service logs + 186 error logs
- **SLO Calculator**: ✅ 63 services analyzed
- **Degradation Detector**: ✅ 1 degrading service detected
- **Trend Analyzer**: ✅ 2 services predicted to have issues
- **Metrics Aggregator**: ✅ 56 healthy, 7 degraded services

**Total Services**: 63
**Time Range**: 2025-12-31 07:00:00 to 11:00:00 (4 hours)
**Overall Error Rate**: 1.64%

---

## Start the Chatbot

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Run the Streamlit App
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## Using the Chatbot

### Step 1: Load Data
Click **"🔄 Refresh from OpenSearch"** in the sidebar to load data from OpenSearch (max 4-hour window).

### Step 2: View Dashboard
Check the **Dashboard tab** to see:
- Total services (63)
- Healthy vs degraded services
- Top services by volume
- Current SLO violations

### Step 3: Ask Questions
Switch to the **Chat tab** and try these questions:

**Service Health Questions:**
```
Which services are degrading over the past 30 minutes?
Show the volume and error code distribution for degrading services
Which services are expected to have issues today?
What's the current SLI for all services?
Show me services violating their SLO
```

**Detailed Analysis:**
```
Get a summary for "GET https://wm-sandbox-1.watermelon.us:443/api/sts/grant-token"
Calculate error budget for the grant-token service
What are the top errors?
Show me the slowest services
Which services have the highest error rates?
```

**Predictive Analysis:**
```
Which services are expected to have issues today?
Show historical patterns for the grant-token service
What's the error rate trend for degrading services?
```

---

## Real-time OpenSearch Integration

To fetch live data from OpenSearch:

1. Click **"🔄 Refresh from OpenSearch"** in the sidebar
2. Select time range (Last 4 hours or Custom - max 4 hours)
3. Adjust Max Results if needed (100-10,000)
4. The chatbot will fetch logs from OpenSearch
5. All analytics will update with fresh data

**Note:** The maximum time window is 4 hours to stay within OpenSearch limits. Scroll API is not used.

---

## Example Conversation

**You**: Which services are degrading over the past 30 minutes?

**Assistant**: I found 1 service degrading:

- **Others** (Severity: critical)
  - Error rate change: +7.70%
  - Response time change: +434.25%
  - This service needs immediate attention!

Would you like me to show the error code distribution for this service?

**You**: Yes, show the error code distribution

**Assistant**: Here's the error code distribution for degrading services:

| Error Code | Count | Percentage |
|------------|-------|------------|
| 500        | 243   | 45.2%      |
| 404        | 187   | 34.8%      |
| 400        | 108   | 20.0%      |

The majority of errors (45.2%) are HTTP 500 (Internal Server Error).

---

## Architecture Highlights

✅ **No Vector DB Required** - Uses DuckDB for fast OLAP queries
✅ **Claude Sonnet 4.5** - AWS Bedrock integration with function calling
✅ **14 Analytics Functions** - SLO calculations, degradation detection, predictions
✅ **Real-time Streaming** - OpenSearch integration for live data
✅ **Interactive Dashboard** - Streamlit UI with charts and metrics

---

## Customization

Edit `utils/config.py` to customize:

```python
DEFAULT_ERROR_SLO_THRESHOLD = 1.0      # 1% error rate target
DEFAULT_RESPONSE_TIME_SLO = 1.0        # 1 second target
DEGRADATION_WINDOW_MINUTES = 30        # Time window for degradation
DEGRADATION_THRESHOLD_PERCENT = 20     # 20% change = degradation
```

---

## Troubleshooting

**No data displayed?**
- Click "🔄 Refresh from OpenSearch" in the sidebar
- Make sure OpenSearch credentials are configured in `.env`
- Verify OpenSearch connection with `python debug_opensearch.py`

**Chat not working?**
- Check AWS credentials in `.env`
- Verify internet connection for AWS Bedrock
- Check console for error messages

**Slow queries?**
- DuckDB is optimized for analytics
- Large datasets (>1M rows) will benefit from more RAM

---

## Next Steps

1. **Explore the Dashboard** - View service health metrics
2. **Chat with the AI** - Ask natural language questions
3. **Monitor Real-time** - Set up periodic OpenSearch refreshes
4. **Customize SLOs** - Define your own SLO targets per service
5. **Export Reports** - Use the analytics functions to generate reports

Happy monitoring! 📊
