# Deprecated Files

This directory contains files that are no longer used after the migration to ClickHouse.

## Migration Summary

**Date:** January 15, 2026
**Change:** Migrated from DuckDB + Platform API to ClickHouse (kafka_put pipeline)

## Deprecated Components

### Data Ingestion (`data/ingestion/`)

All data ingestion components have been removed since the chatbot now uses **read-only** access to ClickHouse:

- **`platform_api_client.py`** - Fetched daily aggregated metrics from WM Platform Error Budget Statistics Service API
- **`keycloak_auth.py`** - OAuth2 authentication with Keycloak (auto-refresh tokens)
- **`opensearch_client.py`** - Legacy OpenSearch integration (before Platform API)
- **`data_loader.py`** - Parsed API responses and loaded data into DuckDB

**Replacement:** Data is now ingested via the `kafka_put` pipeline:
1. `kafka_producer.py` fetches from Platform API → Kafka
2. `kafka_to_clickhouse.py` consumes from Kafka → ClickHouse
3. Chatbot queries ClickHouse read-only

### Database (`data/database/`)

- **`duckdb_manager.py`** - OLAP database for 90+ SLO metrics (daily aggregated data)

**Replacement:** `clickhouse_manager.py` - Read-only queries to ClickHouse (hourly metrics, 12-day fixed dataset)

## Key Differences

| Aspect | Old (DuckDB + Platform API) | New (ClickHouse) |
|--------|----------------------------|------------------|
| **Data Source** | Platform API (fetched on demand) | ClickHouse (pre-loaded by kafka_put) |
| **Granularity** | Daily aggregated | Hourly |
| **Time Window** | 5-60 days (dynamic) | 12 days (fixed: Dec 31, 2025 - Jan 12, 2026) |
| **Data Loading** | On-demand via UI button | Pre-loaded via kafka_put pipeline |
| **Field Names** | camelCase (Platform API) | snake_case (ClickHouse) |
| **Total Rows** | ~100-200 (one per service per day) | ~8,759-35,000 (hourly records) |
| **Burn Rate** | Provided by API | Calculated: `(error_rate / short_target_slo) * 100` |

## Field Mapping Changes

### Key Field Name Conversions

| Platform API (Old) | ClickHouse (New) |
|--------------------|------------------|
| `response_time_avg` | `avg_response_time` |
| `target_error_slo_perc` | `short_target_slo` |
| `target_response_slo_sec` | `response_slo` |
| `response_time_p95` | `percentile_95` |
| `response_time_p99` | `percentile_99` |

### Removed Fields (Not in ClickHouse)

- `response_time_min` / `response_time_max` → Use `avg_response_time` instead
- `burn_rate` → Must be calculated from `error_rate` and `short_target_slo`
- `eb_slo_status` (SLO governance status) → Not available

## Why Keep These Files?

These files are preserved for:

1. **Documentation** - Understanding the previous architecture
2. **Reference** - Field mappings and data structures
3. **Rollback** - In case we need to revert the migration

## If You Need to Use These Files

⚠️ **Warning:** These files are no longer maintained and will not work with the current codebase.

To restore the old system:
1. Restore files from `_deprecated/` back to their original locations
2. Revert `app.py` to use `DuckDBManager` instead of `ClickHouseManager`
3. Revert analytics modules to use old field names
4. Update `.env` with Keycloak credentials
5. Restore UI buttons for Platform API data loading

## Related Documentation

- **CLAUDE.md** - Project overview (mentions deprecated Platform API migration)
- **PLATFORM_API_MIGRATION.md** - Original Platform API migration guide (OpenSearch → Platform API)
- **kafka_put/CLAUDE.md** - kafka_put pipeline documentation (Platform API → Kafka → ClickHouse)
