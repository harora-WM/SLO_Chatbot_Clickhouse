"""Trend analyzer for predicting service issues."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from data.database.clickhouse_manager import ClickHouseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TrendAnalyzer:
    """Analyzer for service trends and predictions."""

    def __init__(self, db_manager: ClickHouseManager):
        """Initialize trend analyzer.

        Args:
            db_manager: DuckDB manager instance
        """
        self.db_manager = db_manager

    def predict_issues_today(self) -> List[Dict[str, Any]]:
        """Predict which services are expected to have issues today.

        Uses trend analysis and burn rate to predict issues.

        Returns:
            List of services predicted to have issues
        """
        # Get time range
        time_range = self.db_manager.get_time_range()
        if not time_range['max_time']:
            logger.warning("No data available")
            return []

        current_time = time_range['max_time']

        # Analyze all services
        services = self.db_manager.get_all_services()
        predictions = []

        for service in services:
            prediction = self._analyze_service_trend(service, current_time)
            if prediction and prediction.get('risk_level') in ['high', 'critical']:
                predictions.append(prediction)

        # Sort by risk score
        predictions.sort(key=lambda x: x.get('risk_score', 0), reverse=True)

        logger.info(f"Predicted {len(predictions)} services with potential issues")
        return predictions

    def _analyze_service_trend(self, service_name: str, current_time: datetime) -> Optional[Dict[str, Any]]:
        """Analyze trend for a single service.

        Args:
            service_name: Service name
            current_time: Current timestamp

        Returns:
            Dictionary with prediction results or None
        """
        # Get service data for trend analysis (full time range)
        df = self.db_manager.get_service_logs(service_name=service_name)

        if df.empty or len(df) < 3:
            return None

        # Sort by time
        df = df.sort_values('record_time')

        # Calculate trends
        error_rate_trend = self._calculate_linear_trend(df['error_rate'].values)
        response_time_trend = self._calculate_linear_trend(df['response_time_avg'].values)

        # Get current metrics
        latest = df.iloc[-1]
        current_error_rate = latest['error_rate']
        current_response_time = latest['response_time_avg']
        error_slo_target = latest['target_error_slo_perc'] if 'target_error_slo_perc' in latest else 98.0
        response_slo_target = latest['target_response_slo_sec'] if 'target_response_slo_sec' in latest else 1.0

        # Calculate risk factors
        risk_factors = []
        risk_score = 0

        # Error rate trending up
        if error_rate_trend > 0.1:  # Positive slope
            risk_factors.append(f"Error rate trending upward (slope: {error_rate_trend:.3f})")
            risk_score += 30

        # Response time trending up
        if response_time_trend > 0.001:  # Positive slope
            risk_factors.append(f"Response time trending upward (slope: {response_time_trend:.3f})")
            risk_score += 20

        # Current error rate approaching SLO
        if current_error_rate > error_slo_target * 0.7:  # 70% of target
            risk_factors.append(f"Error rate at {current_error_rate:.2f}% (target: {error_slo_target:.2f}%)")
            risk_score += 25

        # Current response time approaching SLO
        if current_response_time > response_slo_target * 0.7:
            risk_factors.append(f"Response time at {current_response_time:.3f}s (target: {response_slo_target:.3f}s)")
            risk_score += 25

        # Volatility in error rate
        error_rate_std = df['error_rate'].std()
        if error_rate_std > 5:  # High volatility
            risk_factors.append(f"High error rate volatility (std: {error_rate_std:.2f})")
            risk_score += 15

        # Already violating SLO
        if current_error_rate > error_slo_target:
            risk_factors.append("Currently violating error rate SLO")
            risk_score += 40

        if current_response_time > response_slo_target:
            risk_factors.append("Currently violating response time SLO")
            risk_score += 40

        # Classify risk level
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        # Only return if there are risk factors
        if not risk_factors:
            return None

        # Handle NaN values safely
        total_cnt = latest['total_count']
        return {
            'service_name': service_name,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'current_metrics': {
                'error_rate': current_error_rate,
                'response_time': current_response_time,
                'total_requests': int(total_cnt) if pd.notna(total_cnt) else 0
            },
            'slo_targets': {
                'error_rate_target': error_slo_target,
                'response_time_target': response_slo_target
            },
            'trends': {
                'error_rate_slope': error_rate_trend,
                'response_time_slope': response_time_trend
            }
        }

    def get_historical_patterns(self, service_name: str) -> Dict[str, Any]:
        """Get historical patterns for a service.

        Args:
            service_name: Service name

        Returns:
            Dictionary with historical pattern analysis
        """
        df = self.db_manager.get_service_logs(service_name=service_name)

        if df.empty:
            return {'error': f'No data found for service {service_name}'}

        df = df.sort_values('record_time')

        # Calculate statistics
        error_rate_stats = {
            'mean': df['error_rate'].mean(),
            'std': df['error_rate'].std(),
            'min': df['error_rate'].min(),
            'max': df['error_rate'].max(),
            'p50': df['error_rate'].median(),
            'p95': df['error_rate'].quantile(0.95),
            'p99': df['error_rate'].quantile(0.99)
        }

        response_time_stats = {
            'mean': df['response_time_avg'].mean(),
            'std': df['response_time_avg'].std(),
            'min': df['response_time_avg'].min(),
            'max': df['response_time_avg'].max(),
            'p50': df['response_time_avg'].median(),
            'p95': df['response_time_avg'].quantile(0.95),
            'p99': df['response_time_avg'].quantile(0.99)
        }

        # Traffic patterns (handle NaN values safely)
        total_req_sum = df['total_count'].sum()
        peak_req = df['total_count'].max()
        min_req = df['total_count'].min()
        traffic_stats = {
            'total_requests': int(total_req_sum) if pd.notna(total_req_sum) else 0,
            'avg_requests_per_period': df['total_count'].mean() if pd.notna(df['total_count'].mean()) else 0.0,
            'peak_requests': int(peak_req) if pd.notna(peak_req) else 0,
            'min_requests': int(min_req) if pd.notna(min_req) else 0
        }

        # Time-based patterns
        df['hour'] = pd.to_datetime(df['record_time']).dt.hour
        hourly_patterns = df.groupby('hour').agg({
            'error_rate': 'mean',
            'response_time_avg': 'mean',
            'total_count': 'sum'
        }).to_dict('index')

        return {
            'service_name': service_name,
            'data_points': len(df),
            'time_range': {
                'start': str(df['record_time'].min()),
                'end': str(df['record_time'].max())
            },
            'error_rate_stats': error_rate_stats,
            'response_time_stats': response_time_stats,
            'traffic_stats': traffic_stats,
            'hourly_patterns': hourly_patterns
        }

    def compare_services(self, service_names: List[str]) -> Dict[str, Any]:
        """Compare multiple services.

        Args:
            service_names: List of service names to compare

        Returns:
            Dictionary with comparison data
        """
        comparisons = []

        for service in service_names:
            df = self.db_manager.get_service_logs(service_name=service)

            if df.empty:
                continue

            # Handle NaN values safely
            total_req = df['total_count'].sum()
            total_err = df['error_count'].sum()
            comparisons.append({
                'service_name': service,
                'avg_error_rate': df['error_rate'].mean(),
                'avg_response_time': df['response_time_avg'].mean(),
                'total_requests': int(total_req) if pd.notna(total_req) else 0,
                'total_errors': int(total_err) if pd.notna(total_err) else 0,
                'slo_compliance': {
                    'error_rate_target': df['target_error_slo_perc'].iloc[0] if 'target_error_slo_perc' in df.columns else 98.0,
                    'response_time_target': df['target_response_slo_sec'].iloc[0] if 'target_response_slo_sec' in df.columns else 1.0
                }
            })

        return {
            'services': comparisons,
            'comparison_count': len(comparisons)
        }

    @staticmethod
    def _calculate_linear_trend(values: np.ndarray) -> float:
        """Calculate linear trend (slope) for a series of values.

        Args:
            values: Array of values

        Returns:
            Slope of the linear trend
        """
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        # Simple linear regression
        slope = np.polyfit(x, values, 1)[0]
        return float(slope)

    def get_anomalies(self, service_name: str, threshold_std: float = 2.0) -> List[Dict[str, Any]]:
        """Detect anomalies in service metrics.

        Args:
            service_name: Service name
            threshold_std: Standard deviation threshold for anomaly detection

        Returns:
            List of detected anomalies
        """
        df = self.db_manager.get_service_logs(service_name=service_name)

        if df.empty:
            return []

        df = df.sort_values('record_time')

        # Calculate statistics
        error_rate_mean = df['error_rate'].mean()
        error_rate_std = df['error_rate'].std()
        response_time_mean = df['response_time_avg'].mean()
        response_time_std = df['response_time_avg'].std()

        anomalies = []

        for _, row in df.iterrows():
            # Check for error rate anomalies
            error_rate_zscore = abs(row['error_rate'] - error_rate_mean) / error_rate_std if error_rate_std > 0 else 0
            response_time_zscore = abs(row['response_time_avg'] - response_time_mean) / response_time_std if response_time_std > 0 else 0

            if error_rate_zscore > threshold_std or response_time_zscore > threshold_std:
                anomaly_type = []
                if error_rate_zscore > threshold_std:
                    anomaly_type.append('error_rate')
                if response_time_zscore > threshold_std:
                    anomaly_type.append('response_time')

                anomalies.append({
                    'timestamp': str(row['record_time']),
                    'anomaly_type': anomaly_type,
                    'error_rate': row['error_rate'],
                    'error_rate_zscore': error_rate_zscore,
                    'response_time': row['response_time_avg'],
                    'response_time_zscore': response_time_zscore
                })

        return anomalies
