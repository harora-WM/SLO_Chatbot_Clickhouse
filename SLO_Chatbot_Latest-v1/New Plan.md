 🚀 Platform API Migration Plan (COMPREHENSIVE)

     Overview

     Migrate from OpenSearch (10k limit, 4-hour window) to Platform API with FULL field utilization for advanced
     pattern detection and multi-dimensional SLO analysis.

     Key Benefits

     - ✅ No 10k limit - Unlimited data via pagination
     - ✅ 60-day historical analysis - Better trend detection
     - ✅ Multi-dimensional SLO tracking - Standard + Aspirational + Timeliness
     - ✅ Advanced correlations - Breach vs Error, Budget exhaustion patterns
     - ✅ Pre-calculated metrics - Burn rate, health indicators, severity scores
     - ✅ Single unified table - No error_logs complexity

     ---
     📊 Complete Database Schema (service_logs table)

     Core Identifiers (5 columns)

     id VARCHAR PRIMARY KEY
     app_id INTEGER
     sid INTEGER  -- Maps to transactionId
     service_name VARCHAR  -- Maps to transactionName
     record_time TIMESTAMP

     Request Volume & Success Metrics (6 columns)

     total_count INTEGER  -- totalCount
     success_count INTEGER  -- successCount
     error_count INTEGER  -- errorCount
     success_rate DOUBLE  -- successRate
     error_rate DOUBLE  -- errorRate
     total_data_points DOUBLE  -- totalDataPoints

     Response Time Metrics (11 columns)

     response_time_avg DOUBLE  -- avgResponseTime
     response_time_min DOUBLE  -- Calculated from percentiles
     response_time_max DOUBLE  -- sumResponseTime / totalCount
     response_time_p25 DOUBLE  -- avgPercentiles.25.0
     response_time_p50 DOUBLE  -- avgPercentiles.50.0
     response_time_p75 DOUBLE  -- avgPercentiles.75.0
     response_time_p80 DOUBLE  -- avgPercentiles.80.0
     response_time_p85 DOUBLE  -- avgPercentiles.85.0
     response_time_p90 DOUBLE  -- avgPercentiles.90.0
     response_time_p95 DOUBLE  -- avgPercentiles.95.0 ⚠️ CRITICAL
     response_time_p99 DOUBLE  -- avgPercentiles.99.0 ⚠️ CRITICAL

     Standard SLO Targets (3 columns)

     target_error_slo_perc DOUBLE  -- shortTargetSLO (98.0)
     target_response_slo_sec DOUBLE  -- responseSlo (1.0)
     response_target_percent DOUBLE  -- responseTargetPercent (98.0)

     Standard Error Budget Metrics (7 columns)

     eb_allocated_percent DOUBLE  -- eBAllocatedPercent (2.0)
     eb_allocated_count INTEGER  -- eBAllocatedCount
     eb_consumed_percent DOUBLE  -- eBConsumedPercent
     eb_consumed_count INTEGER  -- eBConsumedCount
     eb_actual_consumed_percent DOUBLE  -- eBActualConsumedPercent ⚠️ (100% = exhausted)
     eb_left_percent DOUBLE  -- eBLeftPercent (negative = over budget)
     eb_left_count INTEGER  -- eBLeftCount (negative = over budget)

     Standard Response Budget Metrics (7 columns)

     response_allocated_percent DOUBLE  -- responseAllocatedPercent
     response_allocated_count INTEGER  -- responseAllocatedCount
     response_consumed_percent DOUBLE  -- responseConsumedPercent
     response_consumed_count INTEGER  -- responseConsumedCount
     response_actual_consumed_percent DOUBLE  -- responseActualConsumedPercent
     response_left_percent DOUBLE  -- responseLeftPercent
     response_left_count INTEGER  -- responseLeftCount

     Response Breach Tracking (4 columns) ⚠️ IMPORTANT

     response_breached BOOLEAN  -- responseBreached
     response_breach_count INTEGER  -- responseBreachCount
     response_error_rate DOUBLE  -- responseErrorRate (breach rate, different from error_rate!)
     response_success_rate DOUBLE  -- responseSuccessRate

     Aspirational SLO Metrics (13 columns) 🆕

     aspirational_slo DOUBLE  -- aspirationalSLO (99.0)
     aspirational_eb_allocated_percent DOUBLE  -- aspirationalEBAllocatedPercent
     aspirational_eb_allocated_count INTEGER  -- aspirationalEBAllocatedCount
     aspirational_eb_consumed_percent DOUBLE  -- aspirationalEBConsumedPercent
     aspirational_eb_consumed_count INTEGER  -- aspirationalEBConsumedCount
     aspirational_eb_actual_consumed_percent DOUBLE  -- aspirationalEBActualConsumedPercent
     aspirational_eb_left_percent DOUBLE  -- aspirationalEBLeftPercent
     aspirational_eb_left_count INTEGER  -- aspirationalEBLeftCount
     aspirational_response_target_percent DOUBLE  -- aspirationalResponseTargetPercent
     aspirational_response_allocated_percent DOUBLE  -- aspirationalResponseAllocatedPercent
     aspirational_response_consumed_percent DOUBLE  -- aspirationalResponseConsumedPercent
     aspirational_response_actual_consumed_percent DOUBLE  -- aspirationalResponseActualConsumedPercent
     aspirational_response_left_percent DOUBLE  -- aspirationalResponseLeftPercent

     Timeliness Tracking (3 columns) 🆕

     timeliness_consumed_percent DOUBLE  -- timelinessConsumedPercent
     aspirational_timeliness_consumed_percent DOUBLE  -- aspirationalTimelinessConsumedPercent
     timeliness_health VARCHAR  -- timelinessHealth (HEALTHY/UNHEALTHY)

     Health Indicators (6 columns) 🆕

     eb_health VARCHAR  -- ebHealth (HEALTHY/UNHEALTHY)
     response_health VARCHAR  -- responseHealth (HEALTHY/UNHEALTHY)
     aspirational_eb_health VARCHAR  -- aspirationalEBHealth
     aspirational_response_health VARCHAR  -- aspirationalResponseHealth
     timeliness_severity VARCHAR  -- timelinessSeverity (#07AE86 = green, #FD346E = red)
     eb_or_response_breached BOOLEAN  -- ebOrResponseBreached

     Severity Color Codes (4 columns) 🆕

     response_severity VARCHAR  -- responseSeverity (color hex)
     eb_severity VARCHAR  -- ebSeverity (color hex)
     aspirational_response_severity VARCHAR  -- aspirationalResponseSeverity
     aspirational_eb_severity VARCHAR  -- aspirationalEBSeverity

     Advanced Metrics (3 columns)

     burn_rate DOUBLE  -- burnRate ⚠️ CRITICAL for prediction
     eb_breached BOOLEAN  -- ebBreached
     eb_slo_status VARCHAR  -- eBSloStatus (UNDER_REVIEW, APPROVED, etc.)

     Metadata (4 columns)

     sort_data DOUBLE  -- sortData (priority score)
     data_for VARCHAR  -- dataFor (TRANSACTION, SERVICE, etc.)
     timezone VARCHAR  -- timezone
     sre_product VARCHAR  -- sre_product

     Total columns: 90+ (vs 26 in current schema)

     ---
     🎯 Complete Analytics Function Suite (20 Functions)

     Existing Functions (Keep, Update for Daily Data) - 10 Functions

     1. get_degrading_services(time_window_days=7)
       - Compare last 7 days vs previous 7 days (was 30 minutes)
       - Uses P95/P99, error_rate, burn_rate
     2. get_volume_trends(service_name, time_window_days=30)
       - Request volume patterns over longer periods
       - Daily aggregation perfect for trend lines
     3. get_current_sli(service_name)
       - Add burn_rate, health indicators to output
       - Show both standard and aspirational SLI
     4. get_slo_violations()
       - Use health indicators (ebHealth, responseHealth)
       - Filter eb_breached=true OR response_breached=true
     5. calculate_error_budget(service_name, time_window_days=30)
       - Use pre-calculated eb_consumed_percent, eb_left_count
       - Show budget exhaustion trends
     6. get_service_summary(service_name)
       - Comprehensive analysis including all new metrics
       - Multi-dimensional health view
     7. predict_issues_today()
       - Leverage 60 days of history for better predictions
       - Use burn_rate trends to forecast SLO breaches
     8. get_historical_patterns(service_name, days=60)
       - Analyze up to 2 months of patterns
       - Identify day-of-week, time-of-day patterns
     9. get_service_health_overview()
       - System-wide health across all dimensions
       - Count services by health status
     10. get_top_services_by_volume(limit=10)
       - High-traffic services
       - Include health indicators

     Standard Performance Functions (Keep) - 3 Functions

     11. get_slowest_services(limit=10)
       - Sort by P99 latency
       - Show response_breach_count
     12. get_error_prone_services(limit=10)
       - Sort by error_rate
       - Show eb_actual_consumed_percent
     13. get_services_by_burn_rate(limit=10) 🆕
       - Sort by burn_rate descending
       - Proactive risk detection

     New Multi-Dimensional Analysis Functions - 7 Functions 🆕

     14. get_aspirational_slo_gap() 🆕
     # Returns services where:
     # - ebHealth = "HEALTHY" AND aspirationalEBHealth = "UNHEALTHY"
     # OR
     # - responseHealth = "HEALTHY" AND aspirationalResponseHealth = "UNHEALTHY"
     # These are "at risk" services
     15. get_timeliness_issues() 🆕
     # Returns services where:
     # - timelinessHealth = "UNHEALTHY"
     # Cross-correlate with responseHealth to identify root cause
     16. get_breach_vs_error_analysis(service_name=None) 🆕
     # Compare responseErrorRate vs errorRate
     # Identifies:
     # - High responseErrorRate + Low errorRate = Latency issues (slow but working)
     # - Low responseErrorRate + High errorRate = Reliability issues (fast but broken)
     17. get_budget_exhausted_services() 🆕
     # Returns services where:
     # - eb_actual_consumed_percent >= 100 OR eb_left_count < 0
     # These services are over budget
     18. get_composite_health_score() 🆕
     # Aggregate health across dimensions:
     # - ebHealth, responseHealth, timelinessHealth
     # - aspirationalEBHealth, aspirationalResponseHealth
     # Return overall health score (0-100)
     19. get_severity_heatmap() 🆕
     # Visual representation of severity across dimensions
     # Count red (#FD346E) vs green (#07AE86) indicators
     # Shows which services have multiple unhealthy dimensions
     20. get_slo_governance_status() 🆕
     # Track services by eBSloStatus
     # Filter eBSloStatus = "UNDER_REVIEW"
     # Helps prioritize SLO approval workflow

     ---
     🔄 Phase-by-Phase Implementation

     Phase 1: API Client & Authentication (3-4 hours)

     1.1 Create data/ingestion/keycloak_auth.py
     class KeycloakAuthManager:
         def __init__(self):
             self.token = None
             self.token_expiry = None
             self._start_refresh_thread()

         def get_access_token(self):
             """Get valid token (cached or refreshed)"""
             if self._is_token_valid():
                 return self.token
             return self._fetch_new_token()

         def _refresh_token_loop(self):
             """Background thread - refresh every 4 minutes"""
             while True:
                 time.sleep(240)  # 4 minutes
                 self._fetch_new_token()

         def _fetch_new_token(self):
             """POST to Keycloak token endpoint"""
             # Uses credentials from config
             # verify=False for SSL bypass

     1.2 Create data/ingestion/platform_api_client.py
     class PlatformAPIClient:
         def __init__(self, auth_manager):
             self.auth_manager = auth_manager

         def query_service_health(self, start_time, end_time, application="WMPlatform"):
             """Fetch all services with pagination"""
             all_data = []
             page_id = 0

             while True:
                 response = self._fetch_page(start_time, end_time, application, page_id)
                 data = response.json()

                 if not data or len(data) == 0:
                     break

                 all_data.extend(data)
                 page_id += 1

             return all_data

         def _fetch_page(self, start_time, end_time, application, page_id):
             """Fetch single page (200 services)"""
             url = f"{PLATFORM_API_URL}"
             params = {
                 'start_time': start_time,
                 'end_time': end_time,
                 'application': application,
                 'page_id': page_id,
                 'page_size': 200
             }
             headers = {
                 'Authorization': f'Bearer {self.auth_manager.get_access_token()}'
             }
             return requests.get(url, params=params, headers=headers, verify=False)

     ---
     Phase 2: Data Loader Update (3-4 hours)

     2.1 Update data/ingestion/data_loader.py

     Create comprehensive field mapping:

     def load_service_logs_from_json(self, json_data):
         """Parse Platform API response into DataFrame"""

         records = []
         for item in json_data:
             record = {
                 # Core identifiers
                 'id': str(item.get('key', '')),
                 'app_id': None,  # Not in API response
                 'sid': item.get('transactionId'),
                 'service_name': item.get('transactionName'),
                 'record_time': pd.Timestamp.now(),  # API doesn't return timestamp per record

                 # Volume metrics
                 'total_count': item.get('totalCount', 0),
                 'success_count': item.get('successCount', 0),
                 'error_count': item.get('errorCount', 0),
                 'success_rate': item.get('successRate', 0.0),
                 'error_rate': item.get('errorRate', 0.0),
                 'total_data_points': item.get('totalDataPoints', 0.0),

                 # Response time metrics
                 'response_time_avg': item.get('avgResponseTime', 0.0),
                 'response_time_p25': item.get('avgPercentiles', {}).get('25.0', 0.0),
                 'response_time_p50': item.get('avgPercentiles', {}).get('50.0', 0.0),
                 'response_time_p75': item.get('avgPercentiles', {}).get('75.0', 0.0),
                 'response_time_p80': item.get('avgPercentiles', {}).get('80.0', 0.0),
                 'response_time_p85': item.get('avgPercentiles', {}).get('85.0', 0.0),
                 'response_time_p90': item.get('avgPercentiles', {}).get('90.0', 0.0),
                 'response_time_p95': item.get('avgPercentiles', {}).get('95.0', 0.0),
                 'response_time_p99': item.get('avgPercentiles', {}).get('99.0', 0.0),

                 # Standard SLO targets
                 'target_error_slo_perc': item.get('shortTargetSLO', 98.0),
                 'target_response_slo_sec': item.get('responseSlo', 1.0),
                 'response_target_percent': item.get('responseTargetPercent', 98.0),

                 # Standard error budget
                 'eb_allocated_percent': item.get('eBAllocatedPercent', 0.0),
                 'eb_allocated_count': item.get('eBAllocatedCount', 0),
                 'eb_consumed_percent': item.get('eBConsumedPercent', 0.0),
                 'eb_consumed_count': item.get('eBConsumedCount', 0),
                 'eb_actual_consumed_percent': item.get('eBActualConsumedPercent', 0.0),
                 'eb_left_percent': item.get('eBLeftPercent', 0.0),
                 'eb_left_count': item.get('eBLeftCount', 0),

                 # Standard response budget
                 'response_allocated_percent': item.get('responseAllocatedPercent', 0.0),
                 'response_allocated_count': item.get('responseAllocatedCount', 0),
                 'response_consumed_percent': item.get('responseConsumedPercent', 0.0),
                 'response_consumed_count': item.get('responseConsumedCount', 0),
                 'response_actual_consumed_percent': item.get('responseActualConsumedPercent', 0.0),
                 'response_left_percent': item.get('responseLeftPercent', 0.0),
                 'response_left_count': item.get('responseLeftCount', 0),

                 # Response breach tracking
                 'response_breached': item.get('responseBreached', False),
                 'response_breach_count': item.get('responseBreachCount', 0),
                 'response_error_rate': item.get('responseErrorRate', 0.0),
                 'response_success_rate': item.get('responseSuccessRate', 100.0),

                 # Aspirational SLO metrics
                 'aspirational_slo': item.get('aspirationalSLO', 99.0),
                 'aspirational_eb_allocated_percent': item.get('aspirationalEBAllocatedPercent', 0.0),
                 'aspirational_eb_consumed_percent': item.get('aspirationalEBConsumedPercent', 0.0),
                 'aspirational_eb_actual_consumed_percent': item.get('aspirationalEBActualConsumedPercent', 0.0),
                 'aspirational_eb_left_percent': item.get('aspirationalEBLeftPercent', 0.0),
                 'aspirational_response_consumed_percent': item.get('aspirationalResponseConsumedPercent', 0.0),
                 'aspirational_response_actual_consumed_percent':
     item.get('aspirationalResponseActualConsumedPercent', 0.0),

                 # Timeliness tracking
                 'timeliness_consumed_percent': item.get('timelinessConsumedPercent', 0.0),
                 'aspirational_timeliness_consumed_percent': item.get('aspirationalTimelinessConsumedPercent', 0.0),
                 'timeliness_health': item.get('timelinessHealth', 'HEALTHY'),

                 # Health indicators
                 'eb_health': item.get('ebHealth', 'HEALTHY'),
                 'response_health': item.get('responseHealth', 'HEALTHY'),
                 'aspirational_eb_health': item.get('aspirationalEBHealth', 'HEALTHY'),
                 'aspirational_response_health': item.get('aspirationalResponseHealth', 'HEALTHY'),
                 'timeliness_severity': item.get('timelinessSeverity', '#07AE86'),
                 'eb_or_response_breached': item.get('ebOrResponseBreached', False),

                 # Severity color codes
                 'response_severity': item.get('responseSeverity', '#07AE86'),
                 'eb_severity': item.get('ebSeverity', '#07AE86'),
                 'aspirational_response_severity': item.get('aspirationalResponseSeverity', '#07AE86'),
                 'aspirational_eb_severity': item.get('aspirationalEBSeverity', '#07AE86'),

                 # Advanced metrics
                 'burn_rate': item.get('burnRate', 0.0),
                 'eb_breached': item.get('ebBreached', False),
                 'eb_slo_status': item.get('eBSloStatus', 'APPROVED'),

                 # Metadata
                 'sort_data': item.get('sortData', 0.0),
                 'data_for': item.get('dataFor', 'TRANSACTION'),
                 'timezone': item.get('timezone', 'UTC'),
                 'sre_product': item.get('sre_product', '')
             }
             records.append(record)

         return pd.DataFrame(records)

     Delete load_error_logs_from_json() method

     ---
     Phase 3: Database Schema Migration (2-3 hours)

     3.1 Update data/database/duckdb_manager.py

     Create migration script for existing databases:
     def migrate_schema_to_v2(self):
         """Migrate from v1 (26 columns) to v2 (90+ columns)"""

         # Backup existing data
         existing_data = self.conn.execute("SELECT * FROM service_logs").fetchdf()

         # Drop old table
         self.conn.execute("DROP TABLE IF EXISTS service_logs")

         # Create new table with all columns
         self._create_service_logs_table_v2()

         # Migrate existing data with default values for new columns
         # ... (set defaults for new columns)

     Update table creation:
     CREATE TABLE IF NOT EXISTS service_logs (
         -- Core identifiers (5 columns)
         id VARCHAR PRIMARY KEY,
         app_id INTEGER,
         sid INTEGER,
         service_name VARCHAR,
         record_time TIMESTAMP,

         -- Volume metrics (6 columns)
         total_count INTEGER,
         success_count INTEGER,
         error_count INTEGER,
         success_rate DOUBLE,
         error_rate DOUBLE,
         total_data_points DOUBLE,

         -- Response time metrics (11 columns)
         response_time_avg DOUBLE,
         response_time_min DOUBLE,
         response_time_max DOUBLE,
         response_time_p25 DOUBLE,
         response_time_p50 DOUBLE,
         response_time_p75 DOUBLE,
         response_time_p80 DOUBLE,
         response_time_p85 DOUBLE,
         response_time_p90 DOUBLE,
         response_time_p95 DOUBLE,
         response_time_p99 DOUBLE,

         -- Standard SLO targets (3 columns)
         target_error_slo_perc DOUBLE,
         target_response_slo_sec DOUBLE,
         response_target_percent DOUBLE,

         -- Standard error budget (7 columns)
         eb_allocated_percent DOUBLE,
         eb_allocated_count INTEGER,
         eb_consumed_percent DOUBLE,
         eb_consumed_count INTEGER,
         eb_actual_consumed_percent DOUBLE,
         eb_left_percent DOUBLE,
         eb_left_count INTEGER,

         -- Standard response budget (7 columns)
         response_allocated_percent DOUBLE,
         response_allocated_count INTEGER,
         response_consumed_percent DOUBLE,
         response_consumed_count INTEGER,
         response_actual_consumed_percent DOUBLE,
         response_left_percent DOUBLE,
         response_left_count INTEGER,

         -- Response breach tracking (4 columns)
         response_breached BOOLEAN,
         response_breach_count INTEGER,
         response_error_rate DOUBLE,
         response_success_rate DOUBLE,

         -- Aspirational SLO metrics (13 columns)
         aspirational_slo DOUBLE,
         aspirational_eb_allocated_percent DOUBLE,
         aspirational_eb_allocated_count INTEGER,
         aspirational_eb_consumed_percent DOUBLE,
         aspirational_eb_consumed_count INTEGER,
         aspirational_eb_actual_consumed_percent DOUBLE,
         aspirational_eb_left_percent DOUBLE,
         aspirational_eb_left_count INTEGER,
         aspirational_response_target_percent DOUBLE,
         aspirational_response_allocated_percent DOUBLE,
         aspirational_response_consumed_percent DOUBLE,
         aspirational_response_actual_consumed_percent DOUBLE,
         aspirational_response_left_percent DOUBLE,

         -- Timeliness tracking (3 columns)
         timeliness_consumed_percent DOUBLE,
         aspirational_timeliness_consumed_percent DOUBLE,
         timeliness_health VARCHAR,

         -- Health indicators (6 columns)
         eb_health VARCHAR,
         response_health VARCHAR,
         aspirational_eb_health VARCHAR,
         aspirational_response_health VARCHAR,
         timeliness_severity VARCHAR,
         eb_or_response_breached BOOLEAN,

         -- Severity color codes (4 columns)
         response_severity VARCHAR,
         eb_severity VARCHAR,
         aspirational_response_severity VARCHAR,
         aspirational_eb_severity VARCHAR,

         -- Advanced metrics (3 columns)
         burn_rate DOUBLE,
         eb_breached BOOLEAN,
         eb_slo_status VARCHAR,

         -- Metadata (4 columns)
         sort_data DOUBLE,
         data_for VARCHAR,
         timezone VARCHAR,
         sre_product VARCHAR
     );

     CREATE INDEX IF NOT EXISTS idx_service_time ON service_logs(record_time);
     CREATE INDEX IF NOT EXISTS idx_service_name ON service_logs(service_name);
     CREATE INDEX IF NOT EXISTS idx_health_status ON service_logs(eb_health, response_health);
     CREATE INDEX IF NOT EXISTS idx_burn_rate ON service_logs(burn_rate);

     Delete error_logs table methods entirely

     ---
     Phase 4: Analytics Module Updates (4-5 hours)

     4.1 Update analytics/degradation_detector.py

     Update for daily granularity:
     def detect_degrading_services(self, time_window_days=7):
         """Compare last 7 days vs previous 7 days (was 30 minutes)"""

         current_time = pd.Timestamp.now()
         recent_start = current_time - pd.Timedelta(days=time_window_days)
         baseline_start = recent_start - pd.Timedelta(days=time_window_days)

         # Query recent window
         recent_data = self.db_manager.conn.execute(f"""
             SELECT
                 service_name,
                 AVG(error_rate) as avg_error_rate,
                 AVG(response_time_p95) as avg_p95,
                 AVG(response_time_p99) as avg_p99,
                 AVG(burn_rate) as avg_burn_rate,
                 SUM(total_count) as total_requests
             FROM service_logs
             WHERE record_time >= '{recent_start}' AND record_time <= '{current_time}'
             GROUP BY service_name
         """).fetchdf()

         # Query baseline window
         baseline_data = self.db_manager.conn.execute(f"""
             SELECT
                 service_name,
                 AVG(error_rate) as avg_error_rate,
                 AVG(response_time_p95) as avg_p95,
                 AVG(response_time_p99) as avg_p99,
                 AVG(burn_rate) as avg_burn_rate
             FROM service_logs
             WHERE record_time >= '{baseline_start}' AND record_time < '{recent_start}'
             GROUP BY service_name
         """).fetchdf()

         # Compare and detect degradation
         # ... (existing logic)

     Remove get_error_code_distribution() - depends on error_logs
     Remove get_error_details_by_code() - depends on error_logs

     4.2 Update analytics/metrics.py

     Remove:
     - get_top_errors() - depends on error_logs
     - get_error_details_by_code() - depends on error_logs

     Add new methods:

     def get_services_by_burn_rate(self, limit=10):
         """Get services with highest burn rates"""
         query = f"""
             SELECT
                 service_name,
                 AVG(burn_rate) as avg_burn_rate,
                 AVG(eb_actual_consumed_percent) as avg_eb_consumed,
                 AVG(eb_left_percent) as avg_eb_left,
                 AVG(error_rate) as avg_error_rate,
                 MAX(eb_health) as eb_health
             FROM service_logs
             GROUP BY service_name
             HAVING avg_burn_rate > 0
             ORDER BY avg_burn_rate DESC
             LIMIT {limit}
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_aspirational_slo_gap(self):
         """Services meeting standard but failing aspirational SLO"""
         query = """
             SELECT
                 service_name,
                 eb_health,
                 aspirational_eb_health,
                 response_health,
                 aspirational_response_health,
                 AVG(eb_actual_consumed_percent) as std_eb_consumed,
                 AVG(aspirational_eb_actual_consumed_percent) as asp_eb_consumed,
                 AVG(burn_rate) as avg_burn_rate
             FROM service_logs
             WHERE (eb_health = 'HEALTHY' AND aspirational_eb_health = 'UNHEALTHY')
                OR (response_health = 'HEALTHY' AND aspirational_response_health = 'UNHEALTHY')
             GROUP BY service_name, eb_health, aspirational_eb_health,
                      response_health, aspirational_response_health
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_timeliness_issues(self):
         """Services with timeliness problems"""
         query = """
             SELECT
                 service_name,
                 timeliness_health,
                 response_health,
                 AVG(timeliness_consumed_percent) as avg_timeliness_consumed,
                 AVG(response_time_p95) as avg_p95,
                 AVG(error_rate) as avg_error_rate
             FROM service_logs
             WHERE timeliness_health = 'UNHEALTHY'
             GROUP BY service_name, timeliness_health, response_health
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_breach_vs_error_analysis(self, service_name=None):
         """Compare breach rate vs error rate"""
         where_clause = f"WHERE service_name = '{service_name}'" if service_name else ""

         query = f"""
             SELECT
                 service_name,
                 AVG(response_error_rate) as avg_breach_rate,
                 AVG(error_rate) as avg_error_rate,
                 AVG(response_breach_count) as avg_breach_count,
                 AVG(error_count) as avg_error_count,
                 AVG(response_time_p95) as avg_p95,
                 CASE
                     WHEN AVG(response_error_rate) > AVG(error_rate) THEN 'LATENCY_ISSUE'
                     WHEN AVG(error_rate) > AVG(response_error_rate) THEN 'RELIABILITY_ISSUE'
                     ELSE 'BALANCED'
                 END as issue_type
             FROM service_logs
             {where_clause}
             GROUP BY service_name
             ORDER BY avg_breach_rate DESC
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_budget_exhausted_services(self):
         """Services with exhausted error budgets"""
         query = """
             SELECT
                 service_name,
                 eb_actual_consumed_percent,
                 eb_left_count,
                 aspirational_eb_actual_consumed_percent,
                 burn_rate,
                 eb_health,
                 AVG(error_rate) as avg_error_rate
             FROM service_logs
             WHERE eb_actual_consumed_percent >= 100 OR eb_left_count < 0
             GROUP BY service_name, eb_actual_consumed_percent, eb_left_count,
                      aspirational_eb_actual_consumed_percent, burn_rate, eb_health
             ORDER BY eb_actual_consumed_percent DESC
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_composite_health_score(self):
         """Aggregate health score across all dimensions"""
         query = """
             SELECT
                 service_name,
                 -- Count healthy dimensions (0-5)
                 (CASE WHEN eb_health = 'HEALTHY' THEN 1 ELSE 0 END +
                  CASE WHEN response_health = 'HEALTHY' THEN 1 ELSE 0 END +
                  CASE WHEN timeliness_health = 'HEALTHY' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_eb_health = 'HEALTHY' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_response_health = 'HEALTHY' THEN 1 ELSE 0 END) as healthy_dimensions,
                 eb_health,
                 response_health,
                 timeliness_health,
                 aspirational_eb_health,
                 aspirational_response_health,
                 AVG(burn_rate) as avg_burn_rate
             FROM service_logs
             GROUP BY service_name, eb_health, response_health, timeliness_health,
                      aspirational_eb_health, aspirational_response_health
             ORDER BY healthy_dimensions ASC, avg_burn_rate DESC
         """
         result = self.db_manager.conn.execute(query).fetchdf()
         result['health_score'] = (result['healthy_dimensions'] / 5.0) * 100
         return result

     def get_severity_heatmap(self):
         """Count red vs green severity indicators per service"""
         query = """
             SELECT
                 service_name,
                 -- Count red indicators (#FD346E)
                 (CASE WHEN response_severity = '#FD346E' THEN 1 ELSE 0 END +
                  CASE WHEN eb_severity = '#FD346E' THEN 1 ELSE 0 END +
                  CASE WHEN timeliness_severity = '#FD346E' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_response_severity = '#FD346E' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_eb_severity = '#FD346E' THEN 1 ELSE 0 END) as red_count,
                 -- Count green indicators (#07AE86)
                 (CASE WHEN response_severity = '#07AE86' THEN 1 ELSE 0 END +
                  CASE WHEN eb_severity = '#07AE86' THEN 1 ELSE 0 END +
                  CASE WHEN timeliness_severity = '#07AE86' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_response_severity = '#07AE86' THEN 1 ELSE 0 END +
                  CASE WHEN aspirational_eb_severity = '#07AE86' THEN 1 ELSE 0 END) as green_count,
                 response_severity,
                 eb_severity,
                 timeliness_severity,
                 AVG(burn_rate) as avg_burn_rate
             FROM service_logs
             GROUP BY service_name, response_severity, eb_severity, timeliness_severity,
                      aspirational_response_severity, aspirational_eb_severity
             ORDER BY red_count DESC, avg_burn_rate DESC
         """
         return self.db_manager.conn.execute(query).fetchdf()

     def get_slo_governance_status(self):
         """Track SLO approval status"""
         query = """
             SELECT
                 service_name,
                 eb_slo_status,
                 AVG(burn_rate) as avg_burn_rate,
                 eb_health,
                 response_health
             FROM service_logs
             WHERE eb_slo_status = 'UNDER_REVIEW'
             GROUP BY service_name, eb_slo_status, eb_health, response_health
             ORDER BY avg_burn_rate DESC
         """
         return self.db_manager.conn.execute(query).fetchdf()

     4.3 Update analytics/slo_calculator.py

     Enhance with new metrics:
     def get_current_sli(self, service_name=None):
         """Enhanced with burn_rate and health indicators"""
         # ... existing query ...
         # Add: burn_rate, eb_health, response_health, aspirational_eb_health

     4.4 Update analytics/trend_analyzer.py

     Adjust for daily granularity:
     def predict_issues_today(self):
         """Leverage 60 days of history"""
         # Use daily data points for trend analysis
         # Better predictions with more historical context

     ---
     Phase 5: Function Tools Update (2-3 hours)

     5.1 Update agent/function_tools.py

     Remove 3 functions:
     - ❌ get_error_code_distribution
     - ❌ get_top_errors
     - ❌ get_error_details_by_code

     Add 7 new functions:

     # Function 14
     {
         "name": "get_services_by_burn_rate",
         "description": "Get services with highest SLO burn rates. High burn rate indicates rapid error budget
     consumption and SLO breach risk.",
         "input_schema": {
             "type": "object",
             "properties": {
                 "limit": {
                     "type": "integer",
                     "description": "Maximum number of services to return",
                     "default": 10
                 }
             },
             "required": []
         }
     }

     # Function 15
     {
         "name": "get_aspirational_slo_gap",
         "description": "Identify services meeting standard SLO (98%) but failing aspirational SLO (99%). These are
     'at risk' services - one incident away from standard SLO breach.",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     # Function 16
     {
         "name": "get_timeliness_issues",
         "description": "Find services with timeliness/scheduling problems. Cross-correlate with response time to
     identify root cause (performance vs scheduling).",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     # Function 17
     {
         "name": "get_breach_vs_error_analysis",
         "description": "Compare response SLA breach rate vs actual error rate. Identifies latency issues (slow but
     working) vs reliability issues (fast but broken).",
         "input_schema": {
             "type": "object",
             "properties": {
                 "service_name": {
                     "type": "string",
                     "description": "Specific service name (optional). If not provided, analyzes all services."
                 }
             },
             "required": []
         }
     }

     # Function 18
     {
         "name": "get_budget_exhausted_services",
         "description": "Get services that have fully exhausted their error budget (>=100% consumed or negative
     remaining). These services are over budget and need immediate attention.",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     # Function 19
     {
         "name": "get_composite_health_score",
         "description": "Calculate overall health score across all dimensions (error budget, response time,
     timeliness, aspirational). Returns 0-100 score and breakdown by dimension.",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     # Function 20
     {
         "name": "get_severity_heatmap",
         "description": "Visual representation of severity across all dimensions. Counts red vs green health
     indicators per service to identify services with multiple unhealthy dimensions.",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     # Function 21 (bonus)
     {
         "name": "get_slo_governance_status",
         "description": "Track services by SLO approval status. Identifies services with SLOs under review or not
     yet approved, helping prioritize SLO governance workflow.",
         "input_schema": {
             "type": "object",
             "properties": {},
             "required": []
         }
     }

     Update function_map:
     function_map = {
         # Existing (10 functions)
         "get_degrading_services": self._get_degrading_services,
         "get_volume_trends": self._get_volume_trends,
         "get_current_sli": self._get_current_sli,
         "get_slo_violations": self._get_slo_violations,
         "calculate_error_budget": self._calculate_error_budget,
         "get_service_summary": self._get_service_summary,
         "predict_issues_today": self._predict_issues_today,
         "get_historical_patterns": self._get_historical_patterns,
         "get_service_health_overview": self._get_service_health_overview,
         "get_top_services_by_volume": self._get_top_services_by_volume,
         "get_slowest_services": self._get_slowest_services,
         "get_error_prone_services": self._get_error_prone_services,

         # New (8 functions)
         "get_services_by_burn_rate": self._get_services_by_burn_rate,
         "get_aspirational_slo_gap": self._get_aspirational_slo_gap,
         "get_timeliness_issues": self._get_timeliness_issues,
         "get_breach_vs_error_analysis": self._get_breach_vs_error_analysis,
         "get_budget_exhausted_services": self._get_budget_exhausted_services,
         "get_composite_health_score": self._get_composite_health_score,
         "get_severity_heatmap": self._get_severity_heatmap,
         "get_slo_governance_status": self._get_slo_governance_status,
     }

     Total: 20 analytics functions

     ---
     Phase 6: Configuration Update (1 hour)

     6.1 Update utils/config.py

     # Remove OpenSearch config
     # OPENSEARCH_HOST, OPENSEARCH_PORT, etc. - DELETE ALL

     # Add Keycloak Authentication
     KEYCLOAK_URL = get_config("KEYCLOAK_URL",
     "https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token")
     KEYCLOAK_USERNAME = get_config("KEYCLOAK_USERNAME")
     KEYCLOAK_PASSWORD = get_config("KEYCLOAK_PASSWORD")
     KEYCLOAK_CLIENT_ID = get_config("KEYCLOAK_CLIENT_ID", "web_app")
     KEYCLOAK_TOKEN_REFRESH_INTERVAL = 240  # 4 minutes

     # Add Platform API
     PLATFORM_API_URL = get_config("PLATFORM_API_URL",
     "https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/health")
     PLATFORM_API_APPLICATION = get_config("PLATFORM_API_APPLICATION", "WMPlatform")
     PLATFORM_API_PAGE_SIZE = int(get_config("PLATFORM_API_PAGE_SIZE", "200"))
     PLATFORM_API_VERIFY_SSL = False  # Bypass SSL verification

     # Update time windows
     DEFAULT_TIME_WINDOW_DAYS = 5
     MAX_TIME_WINDOW_DAYS = 60
     DEGRADATION_WINDOW_DAYS = 7  # Compare 7 days vs 7 days (was 30 minutes)

     6.2 Update .env.example

     # Keycloak Authentication
     KEYCLOAK_URL=https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token
     KEYCLOAK_USERNAME=your_username
     KEYCLOAK_PASSWORD=your_password
     KEYCLOAK_CLIENT_ID=web_app

     # Platform API
     PLATFORM_API_URL=https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/hea
     lth
     PLATFORM_API_APPLICATION=WMPlatform
     PLATFORM_API_PAGE_SIZE=200

     # AWS Bedrock (unchanged)
     AWS_ACCESS_KEY_ID=...
     AWS_SECRET_ACCESS_KEY=...
     AWS_REGION=ap-south-1
     BEDROCK_MODEL_ID=global.anthropic.claude-sonnet-4-5-20250929-v1:0

     # Logging
     LOG_LEVEL=INFO

     ---
     Phase 7: UI Updates (3-4 hours)

     7.1 Update app.py

     Replace imports:
     from data.ingestion.platform_api_client import PlatformAPIClient
     from data.ingestion.keycloak_auth import KeycloakAuthManager

     Update data loading (lines 383-453):

     # Time range selector - support longer windows
     time_range = st.selectbox(
         "Select Time Range",
         ["Last 5 days", "Last 15 days", "Last 30 days", "Last 60 days", "Custom"],
         index=0
     )

     if time_range == "Last 5 days":
         start_time = datetime.now() - timedelta(days=5)
     elif time_range == "Last 15 days":
         start_time = datetime.now() - timedelta(days=15)
     elif time_range == "Last 30 days":
         start_time = datetime.now() - timedelta(days=30)
     elif time_range == "Last 60 days":
         start_time = datetime.now() - timedelta(days=60)
     else:
         # Custom date picker (no 4-hour restriction!)
         start_time = st.date_input("Start Date", datetime.now() - timedelta(days=7))
         end_time = st.date_input("End Date", datetime.now())

     # Initialize auth manager (cached, auto-refreshes in background)
     @st.cache_resource
     def init_auth_manager():
         return KeycloakAuthManager()

     auth_manager = init_auth_manager()

     # Initialize Platform API client
     @st.cache_resource
     def init_api_client(_auth_manager):
         return PlatformAPIClient(_auth_manager)

     api_client = init_api_client(auth_manager)

     # Load data
     if st.button("🔄 Refresh from Platform API"):
         with st.spinner("Fetching data from Platform API..."):
             try:
                 # Query all services (handles pagination automatically)
                 start_time_ms = int(start_time.timestamp() * 1000)
                 end_time_ms = int(datetime.now().timestamp() * 1000)

                 response = api_client.query_service_health(
                     start_time=start_time_ms,
                     end_time=end_time_ms,
                     application="WMPlatform"
                 )

                 # Load into DuckDB
                 service_data = data_loader.load_service_logs_from_json(response)
                 db_manager.insert_service_logs(service_data)

                 st.success(f"✅ Loaded {len(service_data)} service records from Platform API")

             except Exception as e:
                 st.error(f"❌ Error loading data: {str(e)}")

     Update dashboard (lines 200-300):

     # Add burn rate chart
     st.subheader("🔥 Services by Burn Rate")
     burn_rate_df = metrics.get_services_by_burn_rate(limit=10)
     fig_burn = px.bar(burn_rate_df, x='service_name', y='avg_burn_rate',
                        color='eb_health', title="Top Services by Burn Rate")
     st.plotly_chart(fig_burn)

     # Add aspirational SLO gap
     st.subheader("⚠️ Aspirational SLO Gap")
     gap_df = metrics.get_aspirational_slo_gap()
     if not gap_df.empty:
         st.dataframe(gap_df)
     else:
         st.info("All services meeting aspirational SLOs ✅")

     # Add health heatmap
     st.subheader("🌡️ Service Health Heatmap")
     heatmap_df = metrics.get_severity_heatmap()
     fig_heatmap = px.scatter(heatmap_df, x='green_count', y='red_count',
                               size='avg_burn_rate', color='service_name',
                               hover_data=['service_name', 'avg_burn_rate'],
                               title="Health Indicators (Green vs Red)")
     st.plotly_chart(fig_heatmap)

     # Budget exhaustion alerts
     st.subheader("🚨 Budget Exhausted Services")
     exhausted_df = metrics.get_budget_exhausted_services()
     if not exhausted_df.empty:
         st.error(f"⚠️ {len(exhausted_df)} services have exhausted their error budgets!")
         st.dataframe(exhausted_df)
     else:
         st.success("No services over budget ✅")

     # Remove error-related charts:
     # - Delete "Top Errors" chart
     # - Delete "Error Code Distribution" chart

     ---
     Phase 8: System Prompt Update (1 hour)

     8.1 Update agent/claude_client.py system prompt:

     SYSTEM_PROMPT = """You are an expert SLO monitoring and analysis assistant.

     You have access to 20 analytics functions to help answer questions about service health, SLO compliance, and
     error patterns.

     ## Data Characteristics
     - **Daily aggregated data**: Each data point represents 1 full day of metrics
     - **Historical depth**: Up to 60 days of data available for trend analysis
     - **Multi-dimensional SLO tracking**:
       - Standard SLO (98% target)
       - Aspirational SLO (99% target)
       - Timeliness SLO (scheduling/batch job compliance)
     - **Pre-calculated metrics**: Burn rate, health indicators, percentiles

     ## Key Concepts

     ### Burn Rate
     - Measures rate of error budget consumption
     - burn_rate > 1.0 = consuming budget faster than sustainable
     - burn_rate > 2.0 = high risk of SLO breach

     ### Health Dimensions
     Services are evaluated across 5 dimensions:
     1. **Error Budget Health** (ebHealth): Standard error rate compliance
     2. **Response Time Health** (responseHealth): Latency SLO compliance
     3. **Timeliness Health** (timelinessHealth): Scheduling/batch job completion
     4. **Aspirational EB Health**: Premium error rate compliance (99%)
     5. **Aspirational Response Health**: Premium latency compliance (99%)

     ### Breach vs Error Rate
     - **errorRate**: % of requests with actual errors (4xx, 5xx)
     - **responseErrorRate**: % of requests breaching latency SLO (too slow)
     - Services can be slow but not error (high responseErrorRate, low errorRate)
     - Services can be fast but broken (low responseErrorRate, high errorRate)

     ### Budget Exhaustion
     - **eb_actual_consumed_percent >= 100%**: Error budget fully exhausted
     - **eb_left_count < 0**: Over budget (negative remaining)
     - Services over budget are in SLO violation

     ## Available Functions (20 total)

     ### Standard Performance (3)
     - get_slowest_services: Sort by P99 latency
     - get_error_prone_services: Sort by error rate
     - get_services_by_burn_rate: Sort by burn rate (proactive risk detection)

     ### SLO Analysis (4)
     - get_current_sli: Current service level indicators
     - get_slo_violations: Services breaching SLO
     - calculate_error_budget: Error budget tracking
     - get_service_summary: Comprehensive service analysis

     ### Degradation & Trends (3)
     - get_degrading_services: Compare last 7 days vs previous 7 days
     - get_volume_trends: Request volume patterns
     - predict_issues_today: Forecast issues using historical trends

     ### Multi-Dimensional Analysis (7 NEW)
     - get_aspirational_slo_gap: Services at risk (meeting 98% but failing 99%)
     - get_timeliness_issues: Scheduling/batch job problems
     - get_breach_vs_error_analysis: Latency issues vs reliability issues
     - get_budget_exhausted_services: Services over budget
     - get_composite_health_score: Overall health across all dimensions
     - get_severity_heatmap: Visual severity across dimensions
     - get_slo_governance_status: SLO approval tracking

     ### System Overview (3)
     - get_service_health_overview: System-wide health metrics
     - get_top_services_by_volume: High-traffic services
     - get_historical_patterns: Long-term pattern analysis (up to 60 days)

     ## Example Queries You Can Answer

     1. "Which services are degrading over the past week?"
        → Use: get_degrading_services(time_window_days=7)

     2. "Show services meeting 98% SLO but failing 99% aspirational"
        → Use: get_aspirational_slo_gap()

     3. "Which services are slow but don't error?"
        → Use: get_breach_vs_error_analysis()
        → Look for: high responseErrorRate + low errorRate

     4. "Show services with timeliness issues despite good latency"
        → Use: get_timeliness_issues()
        → Cross-correlate: timelinessHealth vs responseHealth

     5. "Which services have exhausted their error budget?"
        → Use: get_budget_exhausted_services()

     6. "Show me overall health across all dimensions"
        → Use: get_composite_health_score()

     7. "Which services are always unhealthy?" (requires historical analysis)
        → Use: get_historical_patterns() for 30-60 days
        → Analyze: health_status consistency over time

     8. "Visualize service health severity"
        → Use: get_severity_heatmap()

     9. "Which services need SLO approval?"
        → Use: get_slo_governance_status()

     ## Important Notes
     - Daily data = compare day-over-day or week-over-week (not minute-by-minute)
     - Multiple health dimensions = use composite analysis
     - Breach rate ≠ Error rate (distinguish latency from reliability issues)
     - Aspirational SLO gap = early warning of degradation
     - Burn rate = predictive metric (forecast SLO breach before it happens)

     Always provide context-aware insights and explain patterns you detect.
     """

     ---
     Phase 9: Testing (3-4 hours)

     9.1 Create test_platform_api.py

     """Test Platform API integration end-to-end"""

     def test_keycloak_auth():
         """Test token retrieval"""
         auth_manager = KeycloakAuthManager()
         token = auth_manager.get_access_token()
         assert token is not None
         assert len(token) > 100

     def test_platform_api_pagination():
         """Test fetching all services via pagination"""
         auth_manager = KeycloakAuthManager()
         api_client = PlatformAPIClient(auth_manager)

         # Fetch 30 days of data
         end_time = int(datetime.now().timestamp() * 1000)
         start_time = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)

         response = api_client.query_service_health(start_time, end_time)

         assert isinstance(response, list)
         assert len(response) > 0
         print(f"✓ Fetched {len(response)} service records")

     def test_data_loading():
         """Test parsing Platform API response"""
         # Load sample response
         data_loader = DataLoader()
         df = data_loader.load_service_logs_from_json(sample_response)

         # Verify all 90+ columns present
         expected_columns = [
             'service_name', 'burn_rate', 'eb_health',
             'aspirational_eb_health', 'timeliness_health',
             'response_error_rate', 'error_rate'
         ]
         for col in expected_columns:
             assert col in df.columns

         print(f"✓ Parsed {len(df)} records with {len(df.columns)} columns")

     def test_new_analytics_functions():
         """Test all 20 analytics functions"""
         # ... test each new function ...

     def test_claude_integration():
         """Test end-to-end Claude query"""
         # Ask: "Which services are meeting 98% but failing 99%?"
         # Verify: get_aspirational_slo_gap() is called

     9.2 Update test_system.py
     - Remove error_logs tests
     - Add aspirational SLO tests
     - Add timeliness tests
     - Add breach vs error correlation tests

     ---
     Phase 10: Documentation Updates (2 hours)

     10.1 Update CLAUDE.md

     Major sections to update:
     - Architecture Overview: Platform API instead of OpenSearch
     - Database Schema: 90+ columns, no error_logs table
     - Tool Calling Flow: 20 functions (not 15)
     - Configuration: Keycloak auth, Platform API settings
     - Critical Code Patterns: Add Platform API pagination pattern
     - Common Issues: Remove OpenSearch issues, add Keycloak auth troubleshooting

     10.2 Update Data_Flow.md
     - Replace OpenSearch with Platform API
     - Show Keycloak auth flow
     - Show pagination flow
     - Single table architecture

     10.3 Update README.md
     - Update features: Multi-dimensional SLO tracking
     - Update architecture diagram
     - Update time windows: 5 days to 60 days

     ---
     Phase 11: Cleanup (1 hour)

     11.1 Delete obsolete files:
     rm data/ingestion/opensearch_client.py
     rm debug_opensearch.py
     # Keep test JSON files if useful for unit tests

     11.2 Update .gitignore:
     # Platform API
     .keycloak_token_cache

     # Remove OpenSearch-specific entries

     ---
     📈 Migration Benefits Summary

     Solved Problems

     1. ✅ No 10k limit - Unlimited services via pagination
     2. ✅ No 4-hour window - Support 5 days to 60 days
     3. ✅ Better historical analysis - Daily data ideal for trends
     4. ✅ Simpler architecture - Single table, no complex joins

     New Capabilities Unlocked

     1. 🆕 Multi-dimensional SLO tracking - Standard + Aspirational + Timeliness
     2. 🆕 Advanced pattern detection:
       - Services at risk (aspirational gap)
       - Latency vs reliability issues (breach vs error)
       - Budget exhaustion tracking
       - Composite health scoring
     3. 🆕 Proactive monitoring - Burn rate forecasting
     4. 🆕 SLO governance - Track approval status
     5. 🆕 Rich visualizations - Severity heatmaps, health scores

     Questions Now Answerable

     - "Which services are always unhealthy?" (60-day history)
     - "Show services one incident away from SLO breach" (aspirational gap)
     - "Are my slow services broken or just slow?" (breach vs error analysis)
     - "Which services have exhausted their error budget?" (budget tracking)
     - "Overall health across all dimensions?" (composite scoring)

     ---
     ⏱️ Estimated Timeline

     - Phase 1 (API Client): 3-4 hours
     - Phase 2 (Data Loader): 3-4 hours
     - Phase 3 (Database): 2-3 hours
     - Phase 4 (Analytics): 4-5 hours
     - Phase 5 (Functions): 2-3 hours
     - Phase 6 (Config): 1 hour
     - Phase 7 (UI): 3-4 hours
     - Phase 8 (Prompts): 1 hour
     - Phase 9 (Testing): 3-4 hours
     - Phase 10 (Docs): 2 hours
     - Phase 11 (Cleanup): 1 hour

     Total: 25-34 hours (3-4 days of focused work)

     ---
     🎯 Execution Order

     1. Phase 1: Create Platform API client + Keycloak auth
     2. Phase 2: Update data loader with complete field mapping
     3. Phase 3: Migrate database schema (90+ columns)
     4. Phase 6: Update configuration files
     5. Phase 4: Update analytics modules (remove error_logs dependencies)
     6. Phase 5: Update function tools (20 functions)
     7. Phase 7: Update UI (new visualizations)
     8. Phase 8: Update system prompt
     9. Phase 9: End-to-end testing
     10. Phase 10: Documentation
     11. Phase 11: Cleanup

     Ready to proceed?
