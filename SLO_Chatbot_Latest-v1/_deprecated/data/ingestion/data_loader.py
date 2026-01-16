"""Data loader for parsing and loading JSON logs into DuckDB."""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from utils.logger import setup_logger
from data.database.duckdb_manager import DuckDBManager

logger = setup_logger(__name__)


class DataLoader:
    """Loader for service and error logs."""

    def __init__(self, db_manager: DuckDBManager):
        """Initialize data loader.

        Args:
            db_manager: DuckDB manager instance
        """
        self.db_manager = db_manager

    def load_service_logs_from_json(self, json_path: str) -> pd.DataFrame:
        """Load service logs from JSON file.

        Args:
            json_path: Path to service logs JSON file

        Returns:
            DataFrame with parsed service logs
        """
        logger.info(f"Loading service logs from {json_path}")

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Extract hits from Elasticsearch response
            hits = data.get('hits', {}).get('hits', [])
            logger.info(f"Found {len(hits)} service log entries")

            # Parse each entry
            records = []
            for idx, hit in enumerate(hits):
                try:
                    source = hit.get('_source', {})
                    fields = hit.get('fields', {})

                    # Check if data is in scripted_metric (from OpenSearch) or fields (from JSON export)
                    scripted_metric = source.get('scripted_metric', {})

                    # Extract percentiles from the nested structure
                    percentiles = source.get('percentiles_response_time_max', {})

                    # Extract and flatten the data - prefer scripted_metric, fallback to fields
                    record = {
                        'id': hit.get('_id'),
                        'app_id': source.get('app_id'),
                        'sid': source.get('sid'),
                        'service_name': scripted_metric.get('service_name') or self._extract_first(fields.get('service_name')),
                        'record_time': source.get('record_time'),
                        'total_count': scripted_metric.get('total_count') or self._extract_first(fields.get('total_count')),
                        'success_count': scripted_metric.get('success_count') or self._extract_first(fields.get('success_count')),
                        'error_count': scripted_metric.get('error_count') or self._extract_first(fields.get('error_count')),
                        'na_error_count': scripted_metric.get('na_error_count') or self._extract_first(fields.get('na_error_count')),
                        'success_rate': scripted_metric.get('success_rate') or self._extract_first(fields.get('success_rate')),
                        'error_rate': scripted_metric.get('error_rate') or self._extract_first(fields.get('error_rate')),
                        'response_time_avg': source.get('response_time_avg'),
                        'response_time_min': source.get('response_time_min'),
                        'response_time_max': source.get('response_time_max'),
                        'response_time_p25': percentiles.get('25.0'),
                        'response_time_p50': percentiles.get('50.0'),
                        'response_time_p75': percentiles.get('75.0'),
                        'response_time_p80': percentiles.get('80.0'),
                        'response_time_p85': percentiles.get('85.0'),
                        'response_time_p90': percentiles.get('90.0'),
                        'response_time_p95': percentiles.get('95.0'),
                        'response_time_p99': percentiles.get('99.0'),
                        'target_error_slo_perc': scripted_metric.get('target_error_slo_perc') or self._extract_first(fields.get('target_error_slo_perc')),
                        'target_response_slo_sec': scripted_metric.get('target_response_slo_sec') or self._extract_first(fields.get('target_response_slo_sec')),
                        'response_target_percent': scripted_metric.get('response_target_percent') or self._extract_first(fields.get('response_target_percent'))
                    }
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping service log entry {idx} due to error: {e}")
                    continue

            df = pd.DataFrame(records)
            # Ensure continuous index for DuckDB compatibility
            df = df.reset_index(drop=True)
            logger.info(f"Parsed {len(df)} service log records")
            return df

        except Exception as e:
            logger.error(f"Failed to load service logs: {e}")
            raise

    def load_error_logs_from_json(self, json_path: str) -> pd.DataFrame:
        """Load error logs from JSON file.

        Args:
            json_path: Path to error logs JSON file

        Returns:
            DataFrame with parsed error logs
        """
        logger.info(f"Loading error logs from {json_path}")

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Extract hits from Elasticsearch response
            hits = data.get('hits', {}).get('hits', [])
            logger.info(f"Found {len(hits)} error log entries")

            # Parse each entry
            records = []
            for idx, hit in enumerate(hits):
                try:
                    source = hit.get('_source', {})
                    fields = hit.get('fields', {})

                    # Check if data is in scripted_metric (from OpenSearch) or fields (from JSON export)
                    scripted_metric = source.get('scripted_metric', {})

                    # Extract and flatten the data - prefer scripted_metric, fallback to fields
                    record = {
                        'id': hit.get('_id'),
                        'wm_application_id': source.get('wmApplicationId'),
                        'wm_application_name': source.get('wmApplicationName'),
                        'wm_transaction_id': source.get('wmTransactionId'),
                        'wm_transaction_name': scripted_metric.get('wmTransactionName') or self._extract_first(fields.get('wmTransactionName')),
                        'error_codes': source.get('errorCodes'),
                        'error_count': scripted_metric.get('error_count') or source.get('error_count'),
                        'total_count': source.get('total_count'),
                        'technical_error_count': scripted_metric.get('technical_error_count') or self._extract_first(fields.get('technical_error_count')),
                        'business_error_count': scripted_metric.get('business_error_count') or self._extract_first(fields.get('business_error_count')),
                        'response_time_avg': source.get('responseTime_avg'),
                        'response_time_min': source.get('responseTime_min'),
                        'response_time_max': source.get('responseTime_max'),
                        'error_details': scripted_metric.get('error_details') or self._extract_first(fields.get('error_details')),
                        'record_time': source.get('record_time')
                    }
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping error log entry {idx} due to error: {e}")
                    continue

            df = pd.DataFrame(records)
            # Ensure continuous index for DuckDB compatibility
            df = df.reset_index(drop=True)
            logger.info(f"Parsed {len(df)} error log records")
            return df

        except Exception as e:
            logger.error(f"Failed to load error logs: {e}")
            raise

    def load_and_store_all(self, service_logs_path: str, error_logs_path: str):
        """Load and store both service and error logs.

        Args:
            service_logs_path: Path to service logs JSON
            error_logs_path: Path to error logs JSON
        """
        # Load service logs
        service_df = self.load_service_logs_from_json(service_logs_path)
        self.db_manager.insert_service_logs(service_df)

        # Load error logs
        error_df = self.load_error_logs_from_json(error_logs_path)
        self.db_manager.insert_error_logs(error_df)

        logger.info("All logs loaded successfully")

        # Print summary
        time_range = self.db_manager.get_time_range()
        all_services = self.db_manager.get_all_services()

        logger.info(f"Data time range: {time_range['min_time']} to {time_range['max_time']}")
        logger.info(f"Total unique services: {len(all_services)}")

    def load_service_logs_from_platform_api(self, api_response: List[Dict[str, Any]]) -> pd.DataFrame:
        """Load service logs from Platform API response.

        This method handles the Platform API response format which is completely different
        from OpenSearch format. Platform API returns pre-calculated metrics including
        burn rate, health indicators, aspirational SLO metrics, and timeliness tracking.

        Args:
            api_response: List of service health dicts from Platform API

        Returns:
            DataFrame with parsed service logs (90+ columns)
        """
        logger.info(f"Loading {len(api_response)} service records from Platform API")

        records = []
        for idx, item in enumerate(api_response):
            try:
                # Skip if noDataFound flag is set
                if item.get('noDataFound') == True:
                    logger.debug(f"Skipping record {idx}: noDataFound=True")
                    continue

                # Extract avgPercentiles nested dict
                percentiles = item.get('avgPercentiles', {})

                # Build comprehensive record with all 90+ fields
                record = {
                    # Core identifiers (5 columns)
                    'id': str(item.get('key', f"platform_{item.get('transactionId', idx)}")),
                    'app_id': None,  # Not provided by Platform API
                    'sid': item.get('transactionId'),
                    'service_name': item.get('transactionName', 'Unknown'),
                    'record_time': pd.Timestamp.now(),  # Platform API doesn't return per-record timestamp

                    # Request volume & success metrics (6 columns)
                    'total_count': int(item.get('totalCount', 0)),
                    'success_count': int(item.get('successCount', 0)),
                    'error_count': int(item.get('errorCount', 0)),
                    'success_rate': float(item.get('successRate', 0.0)),
                    'error_rate': float(item.get('errorRate', 0.0)),
                    'total_data_points': float(item.get('totalDataPoints', 0.0)),

                    # Response time metrics (11 columns)
                    'response_time_avg': float(item.get('avgResponseTime', 0.0)),
                    'response_time_min': float(percentiles.get('25.0', 0.0)),  # Use P25 as proxy for min
                    'response_time_max': float(item.get('sumResponseTime', 0.0) / max(item.get('totalCount', 1), 1)),
                    'response_time_p25': float(percentiles.get('25.0', 0.0)),
                    'response_time_p50': float(percentiles.get('50.0', 0.0)),
                    'response_time_p75': float(percentiles.get('75.0', 0.0)),
                    'response_time_p80': float(percentiles.get('80.0', 0.0)),
                    'response_time_p85': float(percentiles.get('85.0', 0.0)),
                    'response_time_p90': float(percentiles.get('90.0', 0.0)),
                    'response_time_p95': float(percentiles.get('95.0', 0.0)),
                    'response_time_p99': float(percentiles.get('99.0', 0.0)),

                    # Standard SLO targets (3 columns)
                    'target_error_slo_perc': float(item.get('shortTargetSLO', 98.0)),
                    'target_response_slo_sec': float(item.get('responseSlo', 1.0)),
                    'response_target_percent': float(item.get('responseTargetPercent', 98.0)),

                    # Standard error budget metrics (7 columns)
                    'eb_allocated_percent': float(item.get('eBAllocatedPercent', 0.0)),
                    'eb_allocated_count': int(item.get('eBAllocatedCount', 0)),
                    'eb_consumed_percent': float(item.get('eBConsumedPercent', 0.0)),
                    'eb_consumed_count': int(item.get('eBConsumedCount', 0)),
                    'eb_actual_consumed_percent': float(item.get('eBActualConsumedPercent', 0.0)),
                    'eb_left_percent': float(item.get('eBLeftPercent', 0.0)),
                    'eb_left_count': int(item.get('eBLeftCount', 0)),

                    # Standard response budget metrics (7 columns)
                    'response_allocated_percent': float(item.get('responseAllocatedPercent', 0.0)),
                    'response_allocated_count': int(item.get('responseAllocatedCount', 0)),
                    'response_consumed_percent': float(item.get('responseConsumedPercent', 0.0)),
                    'response_consumed_count': int(item.get('responseConsumedCount', 0)),
                    'response_actual_consumed_percent': float(item.get('responseActualConsumedPercent', 0.0)),
                    'response_left_percent': float(item.get('responseLeftPercent', 0.0)),
                    'response_left_count': int(item.get('responseLeftCount', 0)),

                    # Response breach tracking (4 columns)
                    'response_breached': bool(item.get('responseBreached', False)),
                    'response_breach_count': int(item.get('responseBreachCount', 0)),
                    'response_error_rate': float(item.get('responseErrorRate', 0.0)),
                    'response_success_rate': float(item.get('responseSuccessRate', 100.0)),

                    # Aspirational SLO metrics (13 columns)
                    'aspirational_slo': float(item.get('aspirationalSLO', 99.0)),
                    'aspirational_eb_allocated_percent': float(item.get('aspirationalEBAllocatedPercent', 0.0)),
                    'aspirational_eb_allocated_count': int(item.get('aspirationalEBAllocatedCount', 0)),
                    'aspirational_eb_consumed_percent': float(item.get('aspirationalEBConsumedPercent', 0.0)),
                    'aspirational_eb_consumed_count': int(item.get('aspirationalEBConsumedCount', 0)),
                    'aspirational_eb_actual_consumed_percent': float(item.get('aspirationalEBActualConsumedPercent', 0.0)),
                    'aspirational_eb_left_percent': float(item.get('aspirationalEBLeftPercent', 0.0)),
                    'aspirational_eb_left_count': int(item.get('aspirationalEBLeftCount', 0)),
                    'aspirational_response_target_percent': float(item.get('aspirationalResponseTargetPercent', 99.0)),
                    'aspirational_response_allocated_percent': float(item.get('aspirationalResponseAllocatedPercent', 0.0)),
                    'aspirational_response_allocated_count': int(item.get('aspirationalResponseAllocatedCount', 0)),
                    'aspirational_response_consumed_percent': float(item.get('aspirationalResponseConsumedPercent', 0.0)),
                    'aspirational_response_actual_consumed_percent': float(item.get('aspirationalResponseActualConsumedPercent', 0.0)),
                    'aspirational_response_left_percent': float(item.get('aspirationalResponseLeftPercent', 0.0)),
                    'aspirational_response_left_count': int(item.get('aspirationalResponseLeftCount', 0)),

                    # Timeliness tracking (3 columns)
                    'timeliness_consumed_percent': float(item.get('timelinessConsumedPercent', 0.0)),
                    'aspirational_timeliness_consumed_percent': float(item.get('aspirationalTimelinessConsumedPercent', 0.0)),
                    'timeliness_health': str(item.get('timelinessHealth', 'HEALTHY')),

                    # Health indicators (6 columns)
                    'eb_health': str(item.get('ebHealth', 'HEALTHY')),
                    'response_health': str(item.get('responseHealth', 'HEALTHY')),
                    'aspirational_eb_health': str(item.get('aspirationalEBHealth', 'HEALTHY')),
                    'aspirational_response_health': str(item.get('aspirationalResponseHealth', 'HEALTHY')),
                    'timeliness_severity': str(item.get('timelinessSeverity', '#07AE86')),
                    'eb_or_response_breached': bool(item.get('ebOrResponseBreached', False)),

                    # Severity color codes (4 columns)
                    'response_severity': str(item.get('responseSeverity', '#07AE86')),
                    'eb_severity': str(item.get('ebSeverity', '#07AE86')),
                    'aspirational_response_severity': str(item.get('aspirationalResponseSeverity', '#07AE86')),
                    'aspirational_eb_severity': str(item.get('aspirationalEBSeverity', '#07AE86')),

                    # Advanced metrics (3 columns)
                    'burn_rate': float(item.get('burnRate', 0.0)),
                    'eb_breached': bool(item.get('ebBreached', False)),
                    'eb_slo_status': str(item.get('eBSloStatus', 'APPROVED')),

                    # Metadata (4 columns)
                    'sort_data': float(item.get('sortData', 0.0)),
                    'data_for': str(item.get('dataFor', 'TRANSACTION')),
                    'timezone': str(item.get('timezone', 'UTC')),
                    'sre_product': str(item.get('sre_product', ''))
                }

                records.append(record)

            except Exception as e:
                logger.warning(f"Skipping Platform API record {idx} due to error: {e} | Record: {item.get('transactionName', 'unknown')}")
                continue

        df = pd.DataFrame(records)

        # Ensure continuous index for DuckDB compatibility
        df = df.reset_index(drop=True)

        logger.info(f"✓ Parsed {len(df)} service records from Platform API with {len(df.columns)} columns")

        # Log some statistics
        if len(df) > 0:
            unhealthy_count = len(df[(df['eb_health'] == 'UNHEALTHY') | (df['response_health'] == 'UNHEALTHY')])
            high_burn_rate_count = len(df[df['burn_rate'] > 2.0])
            logger.info(f"  - Unhealthy services: {unhealthy_count}")
            logger.info(f"  - High burn rate (>2.0): {high_burn_rate_count}")

        return df

    @staticmethod
    def _extract_first(value):
        """Extract first element from list or return value as-is.

        Args:
            value: Value to extract from

        Returns:
            First element if list, otherwise value itself
        """
        if isinstance(value, list) and len(value) > 0:
            return value[0]
        return value
