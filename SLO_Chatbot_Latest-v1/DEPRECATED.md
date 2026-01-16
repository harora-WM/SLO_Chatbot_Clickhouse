# Deprecated Files & Features

**Last Updated:** January 2026
**Reason:** Migration from OpenSearch to Platform API

This document lists files and features that are **deprecated** but kept for backward compatibility. They are not used in the current Platform API workflow and may be removed in future versions.

---

## Deprecated Files

### 1. `data/ingestion/opensearch_client.py`

**Status:** ⚠️ **DEPRECATED**
**Replaced By:** `data/ingestion/platform_api_client.py`
**Reason:** OpenSearch has been replaced by Platform API as the data source

**What It Did:**
- Queried OpenSearch indices for service and error logs
- Limited to 10,000 results per query
- Supported 4-hour maximum time windows
- Used basic HTTP authentication

**Migration Path:**
```python
# OLD (OpenSearch)
from data.ingestion.opensearch_client import OpenSearchClient
os_client = OpenSearchClient()
service_logs = os_client.query_service_logs(start_time, end_time)

# NEW (Platform API)
from data.ingestion.keycloak_auth import KeycloakAuthManager
from data.ingestion.platform_api_client import PlatformAPIClient
auth_manager = KeycloakAuthManager()
api_client = PlatformAPIClient(auth_manager)
service_health = api_client.query_service_health(start_time_ms, end_time_ms)
```

**Why Keep It:**
- Some users may still have custom scripts using OpenSearch
- Can be used as reference for understanding legacy data structure

---

### 2. `debug_opensearch.py`

**Status:** ⚠️ **DEPRECATED**
**Replaced By:** `test_platform_api.py`
**Reason:** Debugging tool specific to OpenSearch connectivity

**What It Did:**
- Tested OpenSearch connectivity
- Validated authentication
- Debugged query issues

**Migration Path:**
Use `test_platform_api.py` instead for validating Platform API connectivity:
```bash
# OLD
python debug_opensearch.py

# NEW
python test_platform_api.py
```

---

### 3. `DATA_LIMITS_GUIDE.md`

**Status:** ⚠️ **DEPRECATED**
**Replaced By:** Section in `PLATFORM_API_MIGRATION.md`
**Reason:** Document specific to OpenSearch 10k limit and Scroll API

**What It Covered:**
- OpenSearch 10,000 result limit
- Scroll API usage for large datasets
- 4-hour time window restrictions

**Platform API Equivalent:**
- No 10k limit (automatic pagination)
- No Scroll API needed
- 5-60 day time windows supported

---

### 4. `OPENSEARCH_LIMITS_SUMMARY.md`

**Status:** ⚠️ **DEPRECATED**
**Replaced By:** `PLATFORM_API_MIGRATION.md`
**Reason:** Document specific to OpenSearch limitations

**What It Covered:**
- OpenSearch result limits
- Time window restrictions
- Performance considerations

**Platform API Equivalent:**
See `PLATFORM_API_MIGRATION.md` for new capabilities and benefits.

---

## Deprecated Analytics Functions

The following 3 analytics functions are **deprecated** because they depend on the `error_logs` table, which doesn't exist with Platform API (data is aggregated).

### 1. `get_error_code_distribution(service_name, time_window_minutes)`

**Status:** ⚠️ **DEPRECATED**
**Reason:** Platform API provides aggregated error metrics only (no individual error codes)

**Replacement:**
Use `error_count` and `error_rate` fields from `service_logs` table:
```python
# OLD
error_dist = get_error_code_distribution("MyService", 30)

# NEW
service_summary = get_service_summary("MyService")
error_count = service_summary['error_count']
error_rate = service_summary['error_rate']
```

---

### 2. `get_top_errors(limit=10)`

**Status:** ⚠️ **DEPRECATED**
**Reason:** No `error_logs` table with Platform API

**Replacement:**
Use `get_error_prone_services(limit)` to find services with highest error rates:
```python
# OLD
top_errors = get_top_errors(10)

# NEW
error_prone_services = get_error_prone_services(10)
# Returns services sorted by error_rate
```

---

### 3. `get_error_details_by_code(error_code)`

**Status:** ⚠️ **DEPRECATED**
**Reason:** Platform API provides aggregated data (no individual error log details)

**Replacement:**
No direct replacement. Platform API data is aggregated daily. Use `get_breach_vs_error_analysis()` for root cause analysis:
```python
# OLD
error_details = get_error_details_by_code("500")

# NEW (Root Cause Analysis)
breach_analysis = get_breach_vs_error_analysis("MyService")
# Returns:
# - response_breached (latency issues)
# - error_rate (availability issues)
# - Helps distinguish root cause
```

---

## Deprecated Configuration Variables

### OpenSearch Configuration

**Status:** ⚠️ **DEPRECATED (but kept for backward compatibility)**

The following environment variables are no longer used with Platform API:

```bash
# DEPRECATED - OpenSearch Configuration
OPENSEARCH_HOST=your-opensearch-host.com
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_opensearch_password
OPENSEARCH_USE_SSL=False
OPENSEARCH_INDEX_SERVICE=hourly_wm_wmplatform_31854
OPENSEARCH_INDEX_ERROR=hourly_wm_wmplatform_31854_error
```

**Replaced By:**
```bash
# NEW - Platform API Configuration
KEYCLOAK_URL=https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token
KEYCLOAK_USERNAME=your_keycloak_username
KEYCLOAK_PASSWORD=your_keycloak_password
KEYCLOAK_CLIENT_ID=web_app

PLATFORM_API_URL=https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/health
PLATFORM_API_APPLICATION=WMPlatform
PLATFORM_API_PAGE_SIZE=200
PLATFORM_API_VERIFY_SSL=False
```

---

## Deprecated UI Elements

### Time Range Options

**OLD (OpenSearch):**
- "Last 4 hours" (default)
- Custom (max 4 hours)

**NEW (Platform API):**
- "Last 5 days"
- "Last 7 days" (default)
- "Last 30 days"
- "Last 60 days"
- Custom (max 60 days)

### Data Loading Button

**OLD:** "🔄 Refresh from OpenSearch"
**NEW:** "🔄 Refresh from Platform API"

---

## Deprecated Database Tables

### `error_logs` Table

**Status:** ⚠️ **KEPT FOR BACKWARD COMPATIBILITY** (not used with Platform API)

**Schema:**
```sql
CREATE TABLE IF NOT EXISTS error_logs (
    id VARCHAR PRIMARY KEY,
    wm_application_id INTEGER,
    wm_application_name VARCHAR,
    wm_transaction_id INTEGER,
    wm_transaction_name VARCHAR,
    error_codes VARCHAR,
    error_count INTEGER,
    total_count INTEGER,
    technical_error_count INTEGER,
    business_error_count INTEGER,
    response_time_avg DOUBLE,
    response_time_min DOUBLE,
    response_time_max DOUBLE,
    error_details VARCHAR,
    record_time TIMESTAMP
)
```

**Reason:** Platform API provides aggregated error metrics in `service_logs` table (no separate error logs).

**What Replaced It:**
Aggregated error fields in `service_logs`:
- `error_count`
- `error_rate`
- `success_count`
- `success_rate`
- `technical_error_count` (if available from API)
- `business_error_count` (if available from API)

---

## Migration Timeline

| **Date** | **Action** | **Impact** |
|----------|-----------|-----------|
| January 2026 | Platform API migration complete | OpenSearch files deprecated |
| January 2026 | Deprecated files marked | No breaking changes (backward compatible) |
| Future TBD | May remove deprecated files | Warning will be provided in advance |

---

## Cleanup Recommendations

### For New Installations
If you're setting up this project from scratch with Platform API, you can **safely ignore** the following files:
- `data/ingestion/opensearch_client.py`
- `debug_opensearch.py`
- `DATA_LIMITS_GUIDE.md`
- `OPENSEARCH_LIMITS_SUMMARY.md`

### For Existing Installations
If you have existing custom scripts or integrations using OpenSearch:
1. Review `PLATFORM_API_MIGRATION.md` for migration guide
2. Update custom scripts to use Platform API client
3. Test thoroughly with `test_platform_api.py`
4. Only then remove OpenSearch-related files

---

## Questions & Support

**Q: When will deprecated files be removed?**
A: No timeline yet. They will remain until all users have migrated to Platform API.

**Q: Can I still use OpenSearch?**
A: Yes, the code is still present, but it's not maintained or used in the UI.

**Q: How do I migrate my custom scripts?**
A: See the "Migration Path" sections above for each deprecated file.

**Q: What if I need error code details?**
A: Platform API provides aggregated data only. Consider logging error details separately if needed.

---

## References

- **Migration Guide:** [PLATFORM_API_MIGRATION.md](PLATFORM_API_MIGRATION.md)
- **Main Documentation:** [README.md](README.md)
- **Test Suite:** `test_platform_api.py`
