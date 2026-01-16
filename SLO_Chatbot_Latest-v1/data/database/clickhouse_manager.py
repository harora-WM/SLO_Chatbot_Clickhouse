"""ClickHouse manager for querying SLO data from kafka_put pipeline."""

import clickhouse_connect
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ClickHouseManager:
    """Manager for ClickHouse operations - read-only access to transaction_metrics table."""

    def __init__(self, host: str = 'localhost', port: int = 8123):
        """Initialize ClickHouse connection.

        Args:
            host: ClickHouse server host
            port: ClickHouse HTTP port
        """
        self.host = host
        self.port = port
        self.client = None
        self._connect()
        self._verify_table()

    def _connect(self):
        """Establish connection to ClickHouse."""
        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username='default',
                password=''
            )
            logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise

    def _verify_table(self):
        """Verify transaction_metrics table exists."""
        try:
            result = self.client.query("SHOW TABLES LIKE 'transaction_metrics'")
            if not result.result_rows:
                raise ValueError("transaction_metrics table not found in ClickHouse")
            logger.info("Verified transaction_metrics table exists")
        except Exception as e:
            logger.error(f"Failed to verify table: {e}")
            raise

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame.

        Args:
            sql: SQL query string

        Returns:
            Query results as DataFrame with service_name field (mapped from transaction_name)
        """
        try:
            # Execute query and get DataFrame
            df = self.client.query_df(sql)

            # Map transaction_name to service_name for compatibility with analytics modules
            if 'transaction_name' in df.columns and 'service_name' not in df.columns:
                df['service_name'] = df['transaction_name']

            return df
        except Exception as e:
            logger.error(f"Query failed: {e}\nSQL: {sql}")
            raise

    def get_service_logs(self,
                        service_name: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: Optional[int] = None) -> pd.DataFrame:
        """Get service logs with optional filters.

        Args:
            service_name: Filter by service name (matches transaction_name in ClickHouse)
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Limit number of results

        Returns:
            Filtered service logs with service_name field
        """
        where_clauses = []

        if service_name:
            # Escape single quotes in service name
            escaped_name = service_name.replace("'", "\\'")
            where_clauses.append(f"transaction_name = '{escaped_name}'")
        if start_time:
            where_clauses.append(f"timestamp >= '{start_time}'")
        if end_time:
            where_clauses.append(f"timestamp <= '{end_time}'")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit_sql = f"LIMIT {limit}" if limit else ""

        sql = f"""
            SELECT
                transaction_name as service_name,
                transaction_id,
                application_id,
                application_name,
                timestamp as record_time,
                avg_response_time as response_time_avg,
                percentile_50 as response_time_p50,
                percentile_95 as response_time_p95,
                percentile_99 as response_time_p99,
                error_rate,
                success_rate,
                total_count,
                error_count,
                success_count,
                short_target_slo as target_error_slo_perc,
                response_slo as target_response_slo_sec,
                eb_consumed_percent,
                eb_allocated_percent,
                eb_left_percent,
                eb_health,
                response_health,
                timeliness_health,
                eb_breached,
                response_breached
            FROM transaction_metrics
            WHERE {where_sql}
            ORDER BY timestamp DESC
            {limit_sql}
        """

        return self.query(sql)

    def get_all_services(self) -> List[str]:
        """Get list of all unique service names.

        Returns:
            List of service names
        """
        sql = "SELECT DISTINCT transaction_name as service_name FROM transaction_metrics ORDER BY service_name"
        result = self.query(sql)
        return result['service_name'].tolist()

    def get_time_range(self) -> Dict[str, datetime]:
        """Get the time range of data in ClickHouse.

        Returns:
            Dictionary with min_time and max_time
        """
        sql = """
            SELECT
                MIN(timestamp) as min_time,
                MAX(timestamp) as max_time
            FROM transaction_metrics
        """
        result = self.query(sql)
        return {
            'min_time': result['min_time'].iloc[0],
            'max_time': result['max_time'].iloc[0]
        }

    def get_service_count(self) -> int:
        """Get total number of unique services.

        Returns:
            Count of unique services
        """
        sql = "SELECT COUNT(DISTINCT transaction_name) as count FROM transaction_metrics"
        result = self.query(sql)
        return int(result['count'].iloc[0])

    def get_total_records(self) -> int:
        """Get total number of hourly records.

        Returns:
            Total record count
        """
        sql = "SELECT COUNT(*) as count FROM transaction_metrics"
        result = self.query(sql)
        return int(result['count'].iloc[0])

    def close(self):
        """Close the ClickHouse connection."""
        if self.client:
            self.client.close()
            logger.info("ClickHouse connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
