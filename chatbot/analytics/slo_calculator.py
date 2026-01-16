"""SLO calculator for computing SLI, error budgets, and burn rates."""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from data.database.clickhouse_manager import ClickHouseManager
from utils.logger import setup_logger
from utils.config import DEFAULT_ERROR_SLO_THRESHOLD, DEFAULT_RESPONSE_TIME_SLO

logger = setup_logger(__name__)


class SLOCalculator:
    """Calculator for SLO metrics and analysis."""

    def __init__(self, db_manager: ClickHouseManager):
        """Initialize SLO calculator.

        Args:
            db_manager: ClickHouse manager instance
        """
        self.db_manager = db_manager

    def get_current_sli(self, service_name: Optional[str] = None) -> pd.DataFrame:
        """Get current SLI (Service Level Indicator) for services.

        Args:
            service_name: Optional service name filter

        Returns:
            DataFrame with current SLI metrics for each service
        """
        where_clause = f"WHERE transaction_name = '{service_name}'" if service_name else ""

        sql = f"""
            SELECT
                transaction_name as service_name,
                MAX(timestamp) as last_update,
                AVG(success_rate) as avg_success_rate,
                AVG(error_rate) as avg_error_rate,
                AVG(avg_response_time) as avg_response_time,
                AVG(percentile_50) as avg_response_time_p50,
                AVG(percentile_95) as avg_response_time_p95,
                AVG(percentile_99) as avg_response_time_p99,
                SUM(total_count) as total_requests,
                SUM(error_count) as total_errors,
                MAX(short_target_slo) as error_slo_target,
                MAX(response_slo) as response_slo_target
            FROM transaction_metrics
            {where_clause}
            GROUP BY transaction_name
            ORDER BY total_requests DESC
        """

        df = self.db_manager.query(sql)

        # Add SLO compliance flags
        df['error_slo_met'] = df['avg_error_rate'] <= df['error_slo_target']
        df['response_slo_met'] = df['avg_response_time'] <= df['response_slo_target']
        df['overall_slo_met'] = df['error_slo_met'] & df['response_slo_met']

        return df

    def calculate_error_budget(self, service_name: str, time_window_hours: int = 4) -> Dict[str, Any]:
        """Calculate error budget for a service.

        Error budget = (1 - SLO target) * total requests

        Args:
            service_name: Name of the service
            time_window_hours: Time window in hours

        Returns:
            Dictionary with error budget metrics
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)

        df = self.db_manager.get_service_logs(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time
        )

        if df.empty:
            return {
                'service_name': service_name,
                'error': 'No data found for this service'
            }

        total_requests = df['total_count'].sum()
        total_errors = df['error_count'].sum()
        error_slo_target = df['target_error_slo_perc'].iloc[0] if 'target_error_slo_perc' in df.columns and not df.empty else DEFAULT_ERROR_SLO_THRESHOLD

        # Error budget calculation
        error_budget = (error_slo_target / 100) * total_requests
        errors_consumed = total_errors
        budget_remaining = error_budget - errors_consumed
        budget_consumed_percent = (errors_consumed / error_budget * 100) if error_budget > 0 else 0

        # Handle NaN values safely
        return {
            'service_name': service_name,
            'time_window_hours': time_window_hours,
            'total_requests': int(total_requests) if pd.notna(total_requests) else 0,
            'total_errors': int(total_errors) if pd.notna(total_errors) else 0,
            'error_slo_target_percent': error_slo_target,
            'error_budget': error_budget,
            'errors_consumed': int(errors_consumed) if pd.notna(errors_consumed) else 0,
            'budget_remaining': budget_remaining,
            'budget_consumed_percent': budget_consumed_percent,
            'status': 'healthy' if budget_remaining > 0 else 'budget_exceeded'
        }

    def calculate_burn_rate(self, service_name: str, time_window_minutes: int = 30) -> Dict[str, Any]:
        """Calculate error budget burn rate.

        Burn rate = (actual error rate) / (error budget rate)

        Args:
            service_name: Name of the service
            time_window_minutes: Time window in minutes

        Returns:
            Dictionary with burn rate metrics
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_window_minutes)

        df = self.db_manager.get_service_logs(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time
        )

        if df.empty:
            return {
                'service_name': service_name,
                'error': 'No data found for this service'
            }

        total_requests = df['total_count'].sum()
        total_errors = df['error_count'].sum()
        actual_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        error_slo_target = df['target_error_slo_perc'].iloc[0] if 'target_error_slo_perc' in df.columns and not df.empty else DEFAULT_ERROR_SLO_THRESHOLD

        # Burn rate = actual error rate / SLO target
        burn_rate = actual_error_rate / error_slo_target if error_slo_target > 0 else 0

        # Classify burn rate severity
        if burn_rate < 1:
            severity = 'healthy'
        elif burn_rate < 2:
            severity = 'warning'
        elif burn_rate < 10:
            severity = 'critical'
        else:
            severity = 'emergency'

        # Handle NaN values safely
        return {
            'service_name': service_name,
            'time_window_minutes': time_window_minutes,
            'actual_error_rate': actual_error_rate,
            'error_slo_target': error_slo_target,
            'burn_rate': burn_rate,
            'severity': severity,
            'total_requests': int(total_requests) if pd.notna(total_requests) else 0,
            'total_errors': int(total_errors) if pd.notna(total_errors) else 0
        }

    def get_slo_violations(self) -> List[Dict[str, Any]]:
        """Get all services currently violating their SLO.

        Returns:
            List of services with SLO violations
        """
        sli_df = self.get_current_sli()

        # Filter services violating SLO
        violations = sli_df[~sli_df['overall_slo_met']].copy()

        violations_list = []
        for _, row in violations.iterrows():
            violation_reasons = []
            if not row['error_slo_met']:
                violation_reasons.append(f"Error rate {row['avg_error_rate']:.2f}% exceeds target {row['error_slo_target']:.2f}%")
            if not row['response_slo_met']:
                violation_reasons.append(f"Response time {row['avg_response_time']:.3f}s exceeds target {row['response_slo_target']:.3f}s")

            violations_list.append({
                'service_name': row['service_name'],
                'violations': violation_reasons,
                'error_rate': row['avg_error_rate'],
                'response_time': row['avg_response_time'],
                'total_requests': row['total_requests']
            })

        return violations_list

    def get_service_summary(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive summary for a service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary with service metrics summary
        """
        # Get current SLI
        sli_df = self.get_current_sli(service_name)

        if sli_df.empty:
            return {'error': f'Service {service_name} not found'}

        sli = sli_df.iloc[0].to_dict()

        # Get error budget
        error_budget = self.calculate_error_budget(service_name)

        # Get burn rate
        burn_rate = self.calculate_burn_rate(service_name)

        return {
            'service_name': service_name,
            'sli': {
                'success_rate': sli['avg_success_rate'],
                'error_rate': sli['avg_error_rate'],
                'response_time_avg': sli['avg_response_time'],
                'response_time_p50': sli.get('avg_response_time_p50') if pd.notna(sli.get('avg_response_time_p50')) else None,
                'response_time_p95': sli.get('avg_response_time_p95') if pd.notna(sli.get('avg_response_time_p95')) else None,
                'response_time_p99': sli.get('avg_response_time_p99') if pd.notna(sli.get('avg_response_time_p99')) else None,
                'total_requests': sli['total_requests']
            },
            'slo_targets': {
                'error_rate_target': sli['error_slo_target'],
                'response_time_target': sli['response_slo_target']
            },
            'slo_compliance': {
                'error_slo_met': sli['error_slo_met'],
                'response_slo_met': sli['response_slo_met'],
                'overall_slo_met': sli['overall_slo_met']
            },
            'error_budget': error_budget,
            'burn_rate': burn_rate
        }
