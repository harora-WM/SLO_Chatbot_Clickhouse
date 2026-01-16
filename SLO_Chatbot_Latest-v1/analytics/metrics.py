"""Metrics aggregation and utilities."""

import pandas as pd
from typing import Dict, Any, List, Optional
from data.database.clickhouse_manager import ClickHouseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsAggregator:
    """Aggregator for service metrics."""

    def __init__(self, db_manager: ClickHouseManager):
        """Initialize metrics aggregator.

        Args:
            db_manager: ClickHouse manager instance
        """
        self.db_manager = db_manager

    def get_top_services_by_volume(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top services by request volume.

        Args:
            limit: Number of top services to return

        Returns:
            List of top services
        """
        sql = f"""
            SELECT
                transaction_name as service_name,
                SUM(total_count) as total_requests,
                AVG(error_rate) as avg_error_rate,
                AVG(avg_response_time) as avg_response_time
            FROM transaction_metrics
            GROUP BY transaction_name
            ORDER BY total_requests DESC
            LIMIT {limit}
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            # Handle NaN values safely
            total_req = row['total_requests']
            results.append({
                'service_name': row['service_name'],
                'total_requests': int(total_req) if pd.notna(total_req) else 0,
                'avg_error_rate': row['avg_error_rate'] if pd.notna(row['avg_error_rate']) else 0.0,
                'avg_response_time': row['avg_response_time'] if pd.notna(row['avg_response_time']) else 0.0
            })

        return results

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top error codes by frequency.

        NOTE: This function is deprecated in ClickHouse migration as error_logs table
        doesn't exist. Keeping for backward compatibility but returns empty list.

        Args:
            limit: Number of top errors to return

        Returns:
            Empty list (error_logs table not available in ClickHouse)
        """
        logger.warning("get_top_errors is deprecated - error_logs table not available in ClickHouse")
        return []

    def get_service_health_overview(self) -> Dict[str, Any]:
        """Get overall service health overview.

        Returns:
            Dictionary with health metrics
        """
        # Total services
        total_services = len(self.db_manager.get_all_services())

        # Services meeting SLO
        slo_sql = """
            SELECT
                transaction_name as service_name,
                AVG(error_rate) as avg_error_rate,
                AVG(avg_response_time) as avg_response_time,
                MAX(short_target_slo) as error_slo_target,
                MAX(response_slo) as response_slo_target
            FROM transaction_metrics
            GROUP BY transaction_name
        """

        df = self.db_manager.query(slo_sql)

        healthy_count = 0
        degraded_count = 0
        violated_count = 0

        for _, row in df.iterrows():
            error_slo_met = row['avg_error_rate'] <= row['error_slo_target']
            response_slo_met = row['avg_response_time'] <= row['response_slo_target']

            if error_slo_met and response_slo_met:
                healthy_count += 1
            elif not error_slo_met or not response_slo_met:
                if row['avg_error_rate'] > row['error_slo_target'] * 0.8 or \
                   row['avg_response_time'] > row['response_slo_target'] * 0.8:
                    degraded_count += 1
                else:
                    violated_count += 1

        # Total requests and errors
        totals_sql = """
            SELECT
                SUM(total_count) as total_requests,
                SUM(error_count) as total_errors
            FROM transaction_metrics
        """

        totals_df = self.db_manager.query(totals_sql)

        # Handle NaN values from empty table
        if not totals_df.empty and pd.notna(totals_df['total_requests'].iloc[0]):
            total_requests = int(totals_df['total_requests'].iloc[0])
            total_errors = int(totals_df['total_errors'].iloc[0])
        else:
            total_requests = 0
            total_errors = 0

        overall_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        return {
            'total_services': total_services,
            'healthy_services': healthy_count,
            'degraded_services': degraded_count,
            'violated_services': violated_count,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'overall_error_rate': overall_error_rate,
            'health_percentage': (healthy_count / total_services * 100) if total_services > 0 else 0
        }

    def get_slowest_services(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest services by P99 latency (or average if P99 unavailable).

        Args:
            limit: Number of slowest services to return

        Returns:
            List of slowest services
        """
        sql = f"""
            SELECT
                transaction_name as service_name,
                AVG(avg_response_time) as avg_response_time,
                AVG(percentile_50) as avg_p50,
                AVG(percentile_95) as avg_p95,
                AVG(percentile_99) as avg_p99,
                MAX(response_slo) as response_slo_target,
                SUM(total_count) as total_requests
            FROM transaction_metrics
            GROUP BY transaction_name
            ORDER BY COALESCE(avg_p99, avg_response_time) DESC
            LIMIT {limit}
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            # Handle NaN values safely
            total_req = row['total_requests']
            avg_rt = row['avg_response_time']
            avg_p99 = row['avg_p99']
            avg_p95 = row['avg_p95']
            avg_p50 = row['avg_p50']
            slo_target = row['response_slo_target']

            # Use P99 for SLO check if available, otherwise use average
            check_value = avg_p99 if pd.notna(avg_p99) else avg_rt

            results.append({
                'service_name': row['service_name'],
                'avg_response_time': avg_rt if pd.notna(avg_rt) else 0.0,
                'avg_response_time_p50': avg_p50 if pd.notna(avg_p50) else None,
                'avg_response_time_p95': avg_p95 if pd.notna(avg_p95) else None,
                'avg_response_time_p99': avg_p99 if pd.notna(avg_p99) else None,
                'response_slo_target': slo_target if pd.notna(slo_target) else 1.0,
                'total_requests': int(total_req) if pd.notna(total_req) else 0,
                'slo_met': (check_value <= slo_target) if (pd.notna(check_value) and pd.notna(slo_target)) else True
            })

        return results

    def get_error_prone_services(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get services with highest error rates.

        Args:
            limit: Number of services to return

        Returns:
            List of error-prone services
        """
        sql = f"""
            SELECT
                transaction_name as service_name,
                AVG(error_rate) as avg_error_rate,
                SUM(error_count) as total_errors,
                SUM(total_count) as total_requests,
                MAX(short_target_slo) as error_slo_target
            FROM transaction_metrics
            GROUP BY transaction_name
            HAVING avg_error_rate > 0
            ORDER BY avg_error_rate DESC
            LIMIT {limit}
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            # Handle NaN values safely
            total_errors = row['total_errors']
            total_requests = row['total_requests']
            avg_err_rate = row['avg_error_rate']
            slo_target = row['error_slo_target']
            results.append({
                'service_name': row['service_name'],
                'avg_error_rate': avg_err_rate if pd.notna(avg_err_rate) else 0.0,
                'total_errors': int(total_errors) if pd.notna(total_errors) else 0,
                'total_requests': int(total_requests) if pd.notna(total_requests) else 0,
                'error_slo_target': slo_target if pd.notna(slo_target) else 0.0,
                'slo_met': (avg_err_rate <= slo_target) if (pd.notna(avg_err_rate) and pd.notna(slo_target)) else True
            })

        return results

    def get_error_details_by_code(self, error_code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get detailed error logs for a specific error code.

        NOTE: This function is deprecated in ClickHouse migration as error_logs table
        doesn't exist. Keeping for backward compatibility but returns empty list.

        Args:
            error_code: Error code to search for
            limit: Number of error details to return

        Returns:
            Empty list (error_logs table not available in ClickHouse)
        """
        logger.warning("get_error_details_by_code is deprecated - error_logs table not available in ClickHouse")
        return []

    # ==================== CLICKHOUSE ANALYTICS FUNCTIONS ====================
    # The following functions query ClickHouse transaction_metrics table with
    # burn rate, health indicators, aspirational SLO metrics, and timeliness tracking

    def get_services_by_burn_rate(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get services with highest SLO burn rates.

        High burn rate indicates rapid error budget consumption and SLO breach risk.

        Args:
            limit: Number of services to return

        Returns:
            List of services sorted by burn rate (descending)
        """
        sql = f"""
            SELECT
                transaction_name as service_name,
                AVG(eb_actual_consumed_percent) as avg_eb_consumed,
                AVG(eb_left_percent) as avg_eb_left,
                AVG(error_rate) as avg_error_rate,
                any(eb_health) as eb_health,
                -- Calculate burn rate: (error_rate / SLO_target) * 100
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as avg_burn_rate
            FROM transaction_metrics
            GROUP BY transaction_name
            HAVING avg_burn_rate > 0
            ORDER BY avg_burn_rate DESC
            LIMIT {limit}
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            results.append({
                'service_name': row['service_name'],
                'avg_burn_rate': row['avg_burn_rate'] if pd.notna(row['avg_burn_rate']) else 0.0,
                'avg_eb_consumed': row['avg_eb_consumed'] if pd.notna(row['avg_eb_consumed']) else 0.0,
                'avg_eb_left': row['avg_eb_left'] if pd.notna(row['avg_eb_left']) else 0.0,
                'avg_error_rate': row['avg_error_rate'] if pd.notna(row['avg_error_rate']) else 0.0,
                'eb_health': row['eb_health'] if pd.notna(row['eb_health']) else 'UNKNOWN'
            })

        return results

    def get_aspirational_slo_gap(self) -> List[Dict[str, Any]]:
        """Identify services meeting standard SLO (98%) but failing aspirational SLO (99%).

        These are 'at risk' services - one incident away from standard SLO breach.

        Returns:
            List of services with aspirational SLO gaps
        """
        sql = """
            SELECT
                transaction_name as service_name,
                any(eb_health) as eb_health_status,
                any(aspirational_eb_health) as aspirational_eb_health_status,
                any(response_health) as response_health_status,
                any(aspirational_response_health) as aspirational_response_health_status,
                AVG(eb_actual_consumed_percent) as std_eb_consumed,
                AVG(aspirational_eb_actual_consumed_percent) as asp_eb_consumed,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as avg_burn_rate
            FROM transaction_metrics
            WHERE (eb_health = 'HEALTHY' AND aspirational_eb_health = 'UNHEALTHY')
               OR (response_health = 'HEALTHY' AND aspirational_response_health = 'UNHEALTHY')
            GROUP BY transaction_name
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            results.append({
                'service_name': row['service_name'],
                'eb_health': row['eb_health_status'],
                'aspirational_eb_health': row['aspirational_eb_health_status'],
                'response_health': row['response_health_status'],
                'aspirational_response_health': row['aspirational_response_health_status'],
                'std_eb_consumed': row['std_eb_consumed'] if pd.notna(row['std_eb_consumed']) else 0.0,
                'asp_eb_consumed': row['asp_eb_consumed'] if pd.notna(row['asp_eb_consumed']) else 0.0,
                'avg_burn_rate': row['avg_burn_rate'] if pd.notna(row['avg_burn_rate']) else 0.0
            })

        return results

    def get_timeliness_issues(self) -> List[Dict[str, Any]]:
        """Find services with timeliness/scheduling problems.

        Cross-correlates with response time to identify root cause (performance vs scheduling).

        Returns:
            List of services with timeliness issues
        """
        sql = """
            SELECT
                transaction_name as service_name,
                any(timeliness_health) as timeliness_health,
                any(response_health) as response_health,
                AVG(timeliness_consumed_percent) as avg_timeliness_consumed,
                AVG(percentile_95) as avg_p95,
                AVG(error_rate) as avg_error_rate
            FROM transaction_metrics
            WHERE timeliness_health = 'UNHEALTHY'
            GROUP BY transaction_name
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            results.append({
                'service_name': row['service_name'],
                'timeliness_health': row['timeliness_health'],
                'response_health': row['response_health'],
                'avg_timeliness_consumed': row['avg_timeliness_consumed'] if pd.notna(row['avg_timeliness_consumed']) else 0.0,
                'avg_p95': row['avg_p95'] if pd.notna(row['avg_p95']) else 0.0,
                'avg_error_rate': row['avg_error_rate'] if pd.notna(row['avg_error_rate']) else 0.0
            })

        return results

    def get_breach_vs_error_analysis(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Compare response SLA breach rate vs actual error rate.

        Identifies:
        - High responseErrorRate + Low errorRate = Latency issues (slow but working)
        - Low responseErrorRate + High errorRate = Reliability issues (fast but broken)

        Args:
            service_name: Specific service name (optional). If not provided, analyzes all services.

        Returns:
            List of services with breach vs error analysis
        """
        where_clause = f"WHERE transaction_name = '{service_name}'" if service_name else ""

        sql = f"""
            SELECT
                transaction_name as service_name,
                AVG(response_error_rate) as avg_breach_rate,
                AVG(error_rate) as avg_error_rate,
                AVG(response_breach_count) as avg_breach_count,
                AVG(error_count) as avg_error_count,
                AVG(percentile_95) as avg_p95,
                CASE
                    WHEN AVG(response_error_rate) > AVG(error_rate) THEN 'LATENCY_ISSUE'
                    WHEN AVG(error_rate) > AVG(response_error_rate) THEN 'RELIABILITY_ISSUE'
                    ELSE 'BALANCED'
                END as issue_type
            FROM transaction_metrics
            {where_clause}
            GROUP BY transaction_name
            ORDER BY avg_breach_rate DESC
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            breach_count = row['avg_breach_count']
            error_count = row['avg_error_count']
            results.append({
                'service_name': row['service_name'],
                'avg_breach_rate': row['avg_breach_rate'] if pd.notna(row['avg_breach_rate']) else 0.0,
                'avg_error_rate': row['avg_error_rate'] if pd.notna(row['avg_error_rate']) else 0.0,
                'avg_breach_count': int(breach_count) if pd.notna(breach_count) else 0,
                'avg_error_count': int(error_count) if pd.notna(error_count) else 0,
                'avg_p95': row['avg_p95'] if pd.notna(row['avg_p95']) else 0.0,
                'issue_type': row['issue_type']
            })

        return results

    def get_budget_exhausted_services(self) -> List[Dict[str, Any]]:
        """Get services that have fully exhausted their error budget.

        Services with eb_actual_consumed_percent >= 100 or eb_left_count < 0
        are over budget and need immediate attention.

        Returns:
            List of services with exhausted budgets
        """
        sql = """
            SELECT
                transaction_name as service_name,
                AVG(eb_actual_consumed_percent) as avg_eb_actual_consumed_percent,
                AVG(eb_left_count) as avg_eb_left_count,
                AVG(aspirational_eb_actual_consumed_percent) as avg_aspirational_eb_actual_consumed_percent,
                any(eb_health) as eb_health,
                AVG(error_rate) as avg_error_rate,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as burn_rate,
                SUM(total_count) as total_requests
            FROM transaction_metrics
            WHERE eb_actual_consumed_percent >= 100 OR eb_left_count < 0
            GROUP BY transaction_name
            ORDER BY burn_rate DESC
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            eb_left = row['avg_eb_left_count']
            total_req = row['total_requests']
            results.append({
                'service_name': row['service_name'],
                'eb_actual_consumed_percent': row['avg_eb_actual_consumed_percent'] if pd.notna(row['avg_eb_actual_consumed_percent']) else 0.0,
                'eb_left_count': int(eb_left) if pd.notna(eb_left) else 0,
                'aspirational_eb_actual_consumed_percent': row['avg_aspirational_eb_actual_consumed_percent'] if pd.notna(row['avg_aspirational_eb_actual_consumed_percent']) else 0.0,
                'burn_rate': row['burn_rate'] if pd.notna(row['burn_rate']) else 0.0,
                'eb_health': row['eb_health'] if pd.notna(row['eb_health']) else 'UNKNOWN',
                'avg_error_rate': row['avg_error_rate'] if pd.notna(row['avg_error_rate']) else 0.0,
                'total_requests': int(total_req) if pd.notna(total_req) else 0
            })

        return results

    def get_composite_health_score(self) -> List[Dict[str, Any]]:
        """Calculate overall health score across all dimensions.

        Aggregates: error budget, response time, timeliness, aspirational error budget,
        and aspirational response health.

        Returns:
            List of services with composite health scores (0-100)
        """
        sql = """
            SELECT
                transaction_name as service_name,
                -- Take any health status per service (representative sample)
                any(eb_health) as eb_health_status,
                any(response_health) as response_health_status,
                any(timeliness_health) as timeliness_health_status,
                any(aspirational_eb_health) as aspirational_eb_health_status,
                any(aspirational_response_health) as aspirational_response_health_status,
                -- Count healthy dimensions (calculate after aggregation)
                SUM(CASE WHEN eb_health = 'HEALTHY' THEN 1 ELSE 0 END) as eb_healthy_count,
                SUM(CASE WHEN response_health = 'HEALTHY' THEN 1 ELSE 0 END) as response_healthy_count,
                SUM(CASE WHEN timeliness_health = 'HEALTHY' THEN 1 ELSE 0 END) as timeliness_healthy_count,
                SUM(CASE WHEN aspirational_eb_health = 'HEALTHY' THEN 1 ELSE 0 END) as asp_eb_healthy_count,
                SUM(CASE WHEN aspirational_response_health = 'HEALTHY' THEN 1 ELSE 0 END) as asp_resp_healthy_count,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as avg_burn_rate
            FROM transaction_metrics
            GROUP BY transaction_name
            ORDER BY avg_burn_rate DESC
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            # Calculate total healthy dimensions from individual counts
            # Each count represents how many hourly records had that dimension as HEALTHY
            # We take the maximum across all hours (if any hour was healthy, count it)
            eb_count = row['eb_healthy_count'] if pd.notna(row['eb_healthy_count']) else 0
            resp_count = row['response_healthy_count'] if pd.notna(row['response_healthy_count']) else 0
            time_count = row['timeliness_healthy_count'] if pd.notna(row['timeliness_healthy_count']) else 0
            asp_eb_count = row['asp_eb_healthy_count'] if pd.notna(row['asp_eb_healthy_count']) else 0
            asp_resp_count = row['asp_resp_healthy_count'] if pd.notna(row['asp_resp_healthy_count']) else 0

            # Count how many dimensions were healthy at least once
            healthy_dims = (
                (1 if eb_count > 0 else 0) +
                (1 if resp_count > 0 else 0) +
                (1 if time_count > 0 else 0) +
                (1 if asp_eb_count > 0 else 0) +
                (1 if asp_resp_count > 0 else 0)
            )

            health_score = (healthy_dims / 5.0) * 100

            results.append({
                'service_name': row['service_name'],
                'healthy_dimensions': healthy_dims,
                'health_score': health_score,
                'eb_health': row['eb_health_status'],
                'response_health': row['response_health_status'],
                'timeliness_health': row['timeliness_health_status'],
                'aspirational_eb_health': row['aspirational_eb_health_status'],
                'aspirational_response_health': row['aspirational_response_health_status'],
                'avg_burn_rate': row['avg_burn_rate'] if pd.notna(row['avg_burn_rate']) else 0.0
            })

        return results

    def get_severity_heatmap(self) -> List[Dict[str, Any]]:
        """Visual representation of severity across all dimensions.

        Counts red (#FD346E) vs green (#07AE86) health indicators per service
        to identify services with multiple unhealthy dimensions.

        Returns:
            List of services with severity counts
        """
        sql = """
            SELECT
                transaction_name as service_name,
                -- Count how many hours had red indicators (#FD346E) for each dimension
                SUM(CASE WHEN response_severity = '#FD346E' THEN 1 ELSE 0 END) as response_red_count,
                SUM(CASE WHEN eb_severity = '#FD346E' THEN 1 ELSE 0 END) as eb_red_count,
                SUM(CASE WHEN timeliness_severity = '#FD346E' THEN 1 ELSE 0 END) as timeliness_red_count,
                SUM(CASE WHEN aspirational_response_severity = '#FD346E' THEN 1 ELSE 0 END) as asp_resp_red_count,
                SUM(CASE WHEN aspirational_eb_severity = '#FD346E' THEN 1 ELSE 0 END) as asp_eb_red_count,
                -- Count how many hours had green indicators (#07AE86) for each dimension
                SUM(CASE WHEN response_severity = '#07AE86' THEN 1 ELSE 0 END) as response_green_count,
                SUM(CASE WHEN eb_severity = '#07AE86' THEN 1 ELSE 0 END) as eb_green_count,
                SUM(CASE WHEN timeliness_severity = '#07AE86' THEN 1 ELSE 0 END) as timeliness_green_count,
                SUM(CASE WHEN aspirational_response_severity = '#07AE86' THEN 1 ELSE 0 END) as asp_resp_green_count,
                SUM(CASE WHEN aspirational_eb_severity = '#07AE86' THEN 1 ELSE 0 END) as asp_eb_green_count,
                -- Take most common severity status per service
                any(response_severity) as response_severity,
                any(eb_severity) as eb_severity,
                any(timeliness_severity) as timeliness_severity,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as avg_burn_rate
            FROM transaction_metrics
            GROUP BY transaction_name
            ORDER BY avg_burn_rate DESC
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            # Count how many dimensions are currently red (at least one red hour counts as red)
            red_count = (
                (1 if row['response_red_count'] > 0 else 0) +
                (1 if row['eb_red_count'] > 0 else 0) +
                (1 if row['timeliness_red_count'] > 0 else 0) +
                (1 if row['asp_resp_red_count'] > 0 else 0) +
                (1 if row['asp_eb_red_count'] > 0 else 0)
            )

            # Count how many dimensions are currently green (at least one green hour counts as green)
            green_count = (
                (1 if row['response_green_count'] > 0 else 0) +
                (1 if row['eb_green_count'] > 0 else 0) +
                (1 if row['timeliness_green_count'] > 0 else 0) +
                (1 if row['asp_resp_green_count'] > 0 else 0) +
                (1 if row['asp_eb_green_count'] > 0 else 0)
            )

            results.append({
                'service_name': row['service_name'],
                'red_count': red_count,
                'green_count': green_count,
                'response_severity': row['response_severity'],
                'eb_severity': row['eb_severity'],
                'timeliness_severity': row['timeliness_severity'],
                'avg_burn_rate': row['avg_burn_rate'] if pd.notna(row['avg_burn_rate']) else 0.0
            })

        return results

    def get_slo_governance_status(self) -> List[Dict[str, Any]]:
        """Track services by SLO approval status.

        Identifies services with SLOs under review or not yet approved,
        helping prioritize SLO governance workflow.

        Returns:
            List of services needing SLO governance attention
        """
        sql = """
            SELECT
                transaction_name as service_name,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as avg_burn_rate,
                any(eb_health) as eb_health,
                MAX(response_health) as response_health
            FROM transaction_metrics
            GROUP BY transaction_name
            ORDER BY avg_burn_rate DESC
        """

        df = self.db_manager.query(sql)

        results = []
        for _, row in df.iterrows():
            results.append({
                'service_name': row['service_name'],
                'avg_burn_rate': row['avg_burn_rate'] if pd.notna(row['avg_burn_rate']) else 0.0,
                'eb_health': row['eb_health'] if pd.notna(row['eb_health']) else 'UNKNOWN',
                'response_health': row['response_health'] if pd.notna(row['response_health']) else 'UNKNOWN'
            })

        return results
