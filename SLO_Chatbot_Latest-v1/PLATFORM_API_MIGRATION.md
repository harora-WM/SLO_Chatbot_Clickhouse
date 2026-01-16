# Platform API Migration Guide

**Migration Date:** January 2026
**Status:** ✅ Complete
**Breaking Changes:** Yes - OpenSearch replaced with Platform API

## Overview

This document describes the complete migration from OpenSearch to the WM Platform Error Budget Statistics Service API.

### What Changed

| **Before (OpenSearch)** | **After (Platform API)** |
|-------------------------|--------------------------|
| Data Source: OpenSearch index | Data Source: Platform API |
| Authentication: Basic Auth | Authentication: Keycloak OAuth2 |
| Data Limit: 10,000 results | Data Limit: Unlimited (pagination) |
| Time Window: 4 hours max | Time Window: 5-60 days |
| Data Granularity: Hourly | Data Granularity: Daily aggregated |
| Schema: 26 columns | Schema: 90+ columns |
| Tables: service_logs + error_logs | Tables: service_logs only (aggregated) |
| Analytics Functions: 15 | Analytics Functions: 20 (15 updated + 8 new - 3 deprecated) |

---

## Migration Summary

### Phase 1: API Client & Authentication ✅

**Files Created:**
- `data/ingestion/keycloak_auth.py` - Keycloak OAuth2 authentication with auto-refresh
- `data/ingestion/platform_api_client.py` - Platform API client with pagination

**Key Features:**
- Background token refresh every 4 minutes (daemon thread)
- Automatic pagination (handles any number of services)
- SSL bypass for sandbox environment (configurable)
- Comprehensive error handling and logging

**Configuration Added:**
```bash
# Keycloak Authentication
KEYCLOAK_URL=https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token
KEYCLOAK_USERNAME=your_keycloak_username
KEYCLOAK_PASSWORD=your_keycloak_password
KEYCLOAK_CLIENT_ID=web_app

# Platform API
PLATFORM_API_URL=https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/health
PLATFORM_API_APPLICATION=WMPlatform
PLATFORM_API_PAGE_SIZE=200
PLATFORM_API_VERIFY_SSL=False
```

---

### Phase 2: Data Loader ✅

**File Modified:** `data/ingestion/data_loader.py`

**Added Method:** `load_service_logs_from_platform_api(api_response: List[Dict])`

**Field Mapping (90+ fields):**
```python
# Core identifiers (5 columns)
'id', 'app_id', 'sid', 'service_name', 'record_time'

# Request volume & success metrics (6 columns)
'total_count', 'success_count', 'error_count', 'success_rate', 'error_rate', 'total_data_points'

# Response time metrics (11 columns)
'response_time_avg', 'response_time_min', 'response_time_max',
'response_time_p25', 'response_time_p50', 'response_time_p75',
'response_time_p80', 'response_time_p85', 'response_time_p90',
'response_time_p95', 'response_time_p99'

# Standard SLO targets (3 columns)
'target_error_slo_perc', 'target_response_slo_sec', 'response_target_percent'

# Standard error budget metrics (7 columns)
'eb_allocated_percent', 'eb_allocated_count', 'eb_consumed_percent',
'eb_consumed_count', 'eb_actual_consumed_percent', 'eb_left_percent', 'eb_left_count'

# Standard response budget metrics (7 columns)
'response_allocated_percent', 'response_allocated_count', 'response_consumed_percent',
'response_consumed_count', 'response_actual_consumed_percent', 'response_left_percent', 'response_left_count'

# Response breach tracking (4 columns)
'response_breached', 'response_breach_count', 'response_error_rate', 'response_success_rate'

# Aspirational SLO metrics (15 columns)
'aspirational_slo', 'aspirational_eb_allocated_percent', 'aspirational_eb_allocated_count',
'aspirational_eb_consumed_percent', 'aspirational_eb_consumed_count',
'aspirational_eb_actual_consumed_percent', 'aspirational_eb_left_percent', 'aspirational_eb_left_count',
'aspirational_response_target_percent', 'aspirational_response_allocated_percent',
'aspirational_response_allocated_count', 'aspirational_response_consumed_percent',
'aspirational_response_actual_consumed_percent', 'aspirational_response_left_percent',
'aspirational_response_left_count'

# Timeliness tracking (3 columns)
'timeliness_consumed_percent', 'aspirational_timeliness_consumed_percent', 'timeliness_health'

# Health indicators (6 columns)
'eb_health', 'response_health', 'aspirational_eb_health',
'aspirational_response_health', 'timeliness_severity', 'eb_or_response_breached'

# Severity color codes (4 columns)
'response_severity', 'eb_severity', 'aspirational_response_severity', 'aspirational_eb_severity'

# Advanced metrics (3 columns)
'burn_rate', 'eb_breached', 'eb_slo_status'

# Metadata (4 columns)
'sort_data', 'data_for', 'timezone', 'sre_product'
```

---

### Phase 3: Database Schema ✅

**File Modified:** `data/database/duckdb_manager.py`

**Changes:**
- Extended `service_logs` table from 26 columns to 90+ columns
- Added new indexes for Platform API-specific fields:
  - `idx_burn_rate` - Fast burn rate queries
  - `idx_eb_health` - Health status filtering
  - `idx_response_health` - Response health filtering
  - `idx_eb_breached` - Breach detection

**Backward Compatibility:**
- `error_logs` table kept for backward compatibility (not used with Platform API)
- Existing OpenSearch queries still work (but deprecated)

---

### Phase 4: Analytics Functions ✅

**File Modified:** `analytics/metrics.py`

**Added 8 New Functions:**

1. **get_services_by_burn_rate(limit=10)** → Proactive SLO Risk Monitoring
   ```python
   # Returns services sorted by burn rate (>2.0 = high risk, >5.0 = critical)
   # Use for: Early warning system, proactive alerts
   ```

2. **get_aspirational_slo_gap()** → At-Risk Service Identification
   ```python
   # Returns services meeting standard 98% but failing aspirational 99%
   # Use for: Identifying services at risk of degradation
   ```

3. **get_timeliness_issues()** → Batch Job & Scheduling Problems
   ```python
   # Returns services with timeliness_health = UNHEALTHY
   # Use for: Detecting batch job failures, scheduling issues
   ```

4. **get_breach_vs_error_analysis(service_name=None)** → Root Cause Analysis
   ```python
   # Distinguishes latency issues (response_breached) from availability issues (error_rate)
   # Use for: Diagnosing whether problem is speed or reliability
   ```

5. **get_budget_exhausted_services()** → Over-Budget Services
   ```python
   # Returns services with eb_actual_consumed_percent >= 100%
   # Use for: Immediate SLO breach alerts
   ```

6. **get_composite_health_score()** → Overall Health Scoring
   ```python
   # Calculates health score (0-100) across 5 dimensions:
   #   - Error budget health
   #   - Response time health
   #   - Timeliness health
   #   - Aspirational error budget health
   #   - Aspirational response health
   # Use for: Executive dashboards, high-level health overview
   ```

7. **get_severity_heatmap()** → Visual Pattern Recognition
   ```python
   # Returns count of red (#FD346E) vs green (#07AE86) severity indicators per service
   # Use for: Heatmap visualizations, pattern recognition
   ```

8. **get_slo_governance_status()** → SLO Approval Tracking
   ```python
   # Returns services grouped by eb_slo_status (APPROVED, UNDER_REVIEW, etc.)
   # Use for: SLO governance, compliance tracking
   ```

---

### Phase 5: Function Tools ✅

**File Modified:** `agent/function_tools.py`

**Changes:**
- Added 8 new wrapper functions for Platform API analytics
- Updated `TOOLS` list to 23 total tool definitions
- Updated `function_map` to include new functions
- **Deprecated 3 functions** (removed from `function_map`, kept in `TOOLS` for backward compatibility):
  - `get_error_code_distribution` - No error_logs table
  - `get_top_errors` - No error_logs table
  - `get_error_details_by_code` - Data is aggregated, no individual error logs

**Current Tool Count:**
- ✅ 20 usable functions with Platform API
- ⚠️ 3 deprecated functions (error_logs dependent)

---

### Phase 6: Configuration ✅

**Files Modified:**
- `utils/config.py` - Added Keycloak and Platform API settings
- `.env.example` - Updated template with new credentials

**New Configuration Variables:**
```python
# Keycloak
KEYCLOAK_URL
KEYCLOAK_USERNAME
KEYCLOAK_PASSWORD
KEYCLOAK_CLIENT_ID

# Platform API
PLATFORM_API_URL
PLATFORM_API_APPLICATION
PLATFORM_API_PAGE_SIZE
PLATFORM_API_VERIFY_SSL

# Updated time windows
DEFAULT_TIME_WINDOW_DAYS = 5
MAX_TIME_WINDOW_DAYS = 60
DEGRADATION_WINDOW_DAYS = 7  # Compare last 7 days vs previous 7 days
```

---

### Phase 7: UI Updates ✅

**File Modified:** `app.py`

**Changes:**

1. **Imports Updated:**
   ```python
   # Removed: from data.ingestion.opensearch_client import OpenSearchClient
   # Added:
   from data.ingestion.keycloak_auth import KeycloakAuthManager
   from data.ingestion.platform_api_client import PlatformAPIClient
   from utils.config import DEFAULT_TIME_WINDOW_DAYS, MAX_TIME_WINDOW_DAYS
   ```

2. **Time Range Selector Updated:**
   ```python
   # Before: ["Last 4 hours", "Custom"]
   # After:  ["Last 5 days", "Last 7 days", "Last 30 days", "Last 60 days", "Custom"]
   ```

3. **Data Loading Updated:**
   - Button changed: "🔄 Refresh from OpenSearch" → "🔄 Refresh from Platform API"
   - Now uses `api_client.query_service_health()` instead of OpenSearch queries
   - Shows health summary: unhealthy services, high burn rate services

4. **Sample Questions Updated:**
   ```
   **Proactive Monitoring:**
   - Which services have high burn rates?
   - Show services with exhausted error budgets
   - Which services are at risk (meeting 98% but failing 99%)?

   **Health Analysis:**
   - Show composite health scores for all services
   - Which services have timeliness issues?
   - Show the severity heatmap
   ```

---

### Phase 8: Claude System Prompt ✅

**File Modified:** `app.py` (system_prompt in `display_chat()`)

**Key Updates:**

1. **Data Understanding:**
   - Changed from "OpenSearch index" to "Platform API"
   - Updated from "hourly data" to "daily aggregated metrics"
   - Added description of 90+ fields including burn rate, health indicators, aspirational SLOs

2. **New Analysis Responsibilities:**
   ```python
   1) Identify At-Risk Services:
      - High burn rate (>2.0) = rapid error budget consumption
      - Budget exhaustion (eb_actual_consumed_percent >= 100%)
      - Aspirational SLO gap (meeting 98% but failing 99%)

   2) Multi-Dimensional Health Analysis:
      - Error budget health (eb_health)
      - Response time health (response_health)
      - Aspirational health (aspirational_eb_health, aspirational_response_health)
      - Timeliness health (batch jobs, scheduled tasks)
      - Composite score (0-100 across all 5 dimensions)

   3) Breach vs Error Distinction:
      - response_breached = latency SLO violations
      - error_rate = availability issues
   ```

3. **Tool List Updated:** 20 functions documented (with 3 deprecated noted)

4. **Output Format Updated:** Added aspirational SLO section, health dimensions, burn rate indicators

---

### Phase 9: Testing ✅

**File Created:** `test_platform_api.py`

**Test Coverage:**
1. ✅ Keycloak authentication with auto-refresh
2. ✅ Platform API client with pagination
3. ✅ Data loading with 90+ field mapping
4. ✅ All 20 analytics functions
5. ✅ End-to-end integration

**Running Tests:**
```bash
# Ensure .env has valid Keycloak credentials
source venv/bin/activate
python test_platform_api.py
```

**Expected Output:**
```
================================================================================
PLATFORM API MIGRATION - COMPREHENSIVE TEST SUITE
================================================================================

TEST 1: Keycloak Authentication          ✅ PASSED
TEST 2: Platform API Pagination          ✅ PASSED
TEST 3: Data Loading (90+ Field Mapping) ✅ PASSED
TEST 4: Analytics Functions (20 functions) ✅ PASSED
TEST 5: End-to-End Integration           ✅ PASSED

OVERALL: 5/5 tests passed (100.0%)
```

---

## Migration Benefits

### 1. No Data Limits
- **Before:** Max 10,000 results from OpenSearch
- **After:** Unlimited services via automatic pagination

### 2. Extended Time Windows
- **Before:** 4-hour maximum
- **After:** 5-60 days (configurable)

### 3. Better Historical Analysis
- **Before:** Hourly granularity, limited history
- **After:** Daily aggregated data, 2+ months of history for trend analysis

### 4. Proactive Monitoring
- **Before:** Reactive (detect SLO violations after they occur)
- **After:** Proactive (burn rate warns of impending violations)

### 5. Multi-Tier SLO Tracking
- **Before:** Single SLO target (98%)
- **After:** Standard (98%) + Aspirational (99%) SLO tracking

### 6. Advanced Pattern Detection
- **New:** Burn rate analysis (>2.0 = high risk)
- **New:** Aspirational SLO gap detection (at-risk services)
- **New:** Timeliness tracking (batch jobs, scheduling)
- **New:** Breach vs error root cause analysis
- **New:** Composite health scoring (0-100)

---

## Breaking Changes

### Removed Features
1. **OpenSearch Client** (`data/ingestion/opensearch_client.py`) - Now deprecated
2. **Error Logs Table** - Platform API provides aggregated metrics only
3. **3 Analytics Functions** - Deprecated (error_logs dependent):
   - `get_error_code_distribution()`
   - `get_top_errors()`
   - `get_error_details_by_code()`

### Configuration Changes
- **Required:** Add Keycloak credentials to `.env`
- **Required:** Add Platform API URL to `.env`
- **Optional:** Update time window settings (default 5-60 days)

### Code Changes Required
If you have custom code that calls deprecated functions:
- Replace `get_top_errors()` → Use `error_count` field from service_logs
- Replace `get_error_code_distribution()` → Use aggregated error_rate from service_logs
- Replace `get_error_details_by_code()` → Not available (data is aggregated)

---

## Backward Compatibility

### What Still Works
- ✅ All existing SLO calculation functions
- ✅ Degradation detection (updated for daily data)
- ✅ Trend analysis (updated for daily data)
- ✅ Service health overview
- ✅ Database schema (extended, not breaking)

### What's Deprecated
- ⚠️ OpenSearch client (still in codebase, but not used)
- ⚠️ Error logs loading (still in DataLoader, but not used with Platform API)
- ⚠️ 4-hour time window UI (replaced with 5-60 days)

---

## Migration Checklist

### For Developers
- [ ] Update `.env` with Keycloak credentials
- [ ] Update `.env` with Platform API URL
- [ ] Review new analytics functions (8 new functions)
- [ ] Update any custom code calling deprecated functions
- [ ] Run `python test_platform_api.py` to validate setup
- [ ] Test UI with "Refresh from Platform API" button
- [ ] Review new system prompt for Claude

### For Users
- [ ] No action required - migration is transparent
- [ ] New sample questions available in UI
- [ ] Extended time range options (5-60 days)
- [ ] New proactive monitoring insights

---

## Troubleshooting

### Issue: "Invalid user credentials" error
**Cause:** Keycloak credentials in `.env` are invalid
**Solution:** Update `KEYCLOAK_USERNAME` and `KEYCLOAK_PASSWORD` in `.env`

### Issue: Tests fail with "401 Unauthorized"
**Cause:** Keycloak authentication failed
**Solution:** Verify credentials with `test_keycloak_auth.py` first

### Issue: No data loaded from Platform API
**Cause:** Platform API URL or application name incorrect
**Solution:** Verify `PLATFORM_API_URL` and `PLATFORM_API_APPLICATION` in `.env`

### Issue: SSL verification errors
**Cause:** SSL certificate issues with sandbox environment
**Solution:** Set `PLATFORM_API_VERIFY_SSL=False` in `.env` (sandbox only)

### Issue: Missing columns in database
**Cause:** Old database schema
**Solution:** Delete `data/database/slo_analytics.duckdb` and restart app (will recreate with new schema)

---

## Performance Considerations

### Token Refresh
- Background thread refreshes token every 4 minutes
- No impact on API calls (token always valid)
- Thread automatically stops when application exits

### Pagination
- Automatic (no user intervention needed)
- Default page size: 200 services
- Handles 1000+ services without issues

### Database Size
- Daily data (not hourly) = smaller database
- 60 days × 200 services × 90 columns ≈ 1.08M rows
- Indexes on burn_rate, eb_health, response_health for fast queries

---

## Future Enhancements

### Potential Additions
1. Real-time burn rate alerts (Slack/email notifications)
2. Burn rate trend prediction (ML-based)
3. Automated SLO governance workflow
4. Custom health score weights (user-configurable)
5. Export to Prometheus/Grafana

### API Enhancements
1. Support for custom time ranges (hour-level granularity if API supports)
2. Multi-application support (query multiple applications)
3. Service dependencies mapping

---

## References

- **Platform API Docs:** [Internal WM Documentation]
- **Keycloak Docs:** [WM Keycloak Setup Guide]
- **Test File:** `test_keycloak_auth.py` (reference implementation)
- **Sample Response:** See `test_platform_api.py` for expected API response structure

---

## Contact & Support

For issues or questions:
1. Check `TROUBLESHOOTING.md`
2. Review `test_platform_api.py` test results
3. Check logs in console (INFO level shows detailed steps)
4. Contact SRE team for Keycloak credentials
