"""DuckDB manager for storing and querying SLO data."""

import duckdb
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from utils.logger import setup_logger
from utils.config import DUCKDB_PATH

logger = setup_logger(__name__)


class DuckDBManager:
    """Manager for DuckDB operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize DuckDB connection.

        Args:
            db_path: Path to DuckDB file. Defaults to config value.
        """
        self.db_path = db_path or DUCKDB_PATH
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Establish connection to DuckDB."""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to DuckDB at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    def _create_tables(self):
        """Create tables for service and error logs.

        The service_logs table schema now includes 90+ columns to support
        Platform API data including burn rate, health indicators, aspirational SLO
        metrics, timeliness tracking, and severity indicators.
        """
        # Service logs table - Extended schema for Platform API
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS service_logs (
                -- Core identifiers (5 columns)
                id VARCHAR PRIMARY KEY,
                app_id INTEGER,
                sid INTEGER,
                service_name VARCHAR,
                record_time TIMESTAMP,

                -- Request volume & success metrics (6 columns)
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

                -- Standard error budget metrics (7 columns)
                eb_allocated_percent DOUBLE,
                eb_allocated_count INTEGER,
                eb_consumed_percent DOUBLE,
                eb_consumed_count INTEGER,
                eb_actual_consumed_percent DOUBLE,
                eb_left_percent DOUBLE,
                eb_left_count INTEGER,

                -- Standard response budget metrics (7 columns)
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

                -- Aspirational SLO metrics (15 columns)
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
                aspirational_response_allocated_count INTEGER,
                aspirational_response_consumed_percent DOUBLE,
                aspirational_response_actual_consumed_percent DOUBLE,
                aspirational_response_left_percent DOUBLE,
                aspirational_response_left_count INTEGER,

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
            )
        """)

        # Error logs table
        self.conn.execute("""
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
        """)

        # Create indexes for faster queries
        # Core indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_service_time ON service_logs(record_time)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_service_name ON service_logs(service_name)")

        # Health and performance indexes (NEW for Platform API)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_burn_rate ON service_logs(burn_rate)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_eb_health ON service_logs(eb_health)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_response_health ON service_logs(response_health)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_eb_breached ON service_logs(eb_breached)")

        # Error logs indexes (kept for backwards compatibility with OpenSearch)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_error_time ON error_logs(record_time)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_error_codes ON error_logs(error_codes)")

        logger.info("Database tables created/verified with extended Platform API schema (90+ columns)")

    def insert_service_logs(self, df: pd.DataFrame):
        """Insert service logs into the database.

        Args:
            df: DataFrame with service log data
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided, skipping insert")
                return

            # Convert to proper format
            df = df.copy()

            # Handle timestamp conversion with error handling
            try:
                df['record_time'] = pd.to_datetime(df['record_time'], unit='ms', errors='coerce')
            except Exception as e:
                logger.warning(f"Some timestamps could not be converted: {e}")
                df['record_time'] = pd.to_datetime(df['record_time'], unit='ms', errors='coerce')

            # Drop rows with invalid timestamps
            invalid_rows = df['record_time'].isna().sum()
            if invalid_rows > 0:
                logger.warning(f"Dropping {invalid_rows} rows with invalid timestamps")
                df = df.dropna(subset=['record_time'])

            # Ensure id is not null
            df = df.dropna(subset=['id'])

            if df.empty:
                logger.error("All rows were invalid after cleaning")
                return

            # Reset index to avoid DuckDB index out of bounds errors
            df = df.reset_index(drop=True)

            # Clear existing data and insert fresh
            self.conn.execute("DELETE FROM service_logs")

            # Register DataFrame explicitly with DuckDB to avoid index issues
            self.conn.register('temp_service_df', df)
            self.conn.execute("INSERT INTO service_logs SELECT * FROM temp_service_df")
            self.conn.unregister('temp_service_df')

            logger.info(f"Inserted {len(df)} service log records")
        except Exception as e:
            logger.error(f"Failed to insert service logs: {e}", exc_info=True)
            raise

    def insert_error_logs(self, df: pd.DataFrame):
        """Insert error logs into the database.

        Args:
            df: DataFrame with error log data
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided, skipping insert")
                return

            # Convert to proper format
            df = df.copy()

            # Handle timestamp conversion with error handling
            try:
                df['record_time'] = pd.to_datetime(df['record_time'], unit='ms', errors='coerce')
            except Exception as e:
                logger.warning(f"Some timestamps could not be converted: {e}")
                df['record_time'] = pd.to_datetime(df['record_time'], unit='ms', errors='coerce')

            # Drop rows with invalid timestamps
            invalid_rows = df['record_time'].isna().sum()
            if invalid_rows > 0:
                logger.warning(f"Dropping {invalid_rows} rows with invalid timestamps")
                df = df.dropna(subset=['record_time'])

            # Ensure id is not null
            df = df.dropna(subset=['id'])

            if df.empty:
                logger.error("All rows were invalid after cleaning")
                return

            # Reset index to avoid DuckDB index out of bounds errors
            df = df.reset_index(drop=True)

            # Clear existing data and insert fresh
            self.conn.execute("DELETE FROM error_logs")

            # Register DataFrame explicitly with DuckDB to avoid index issues
            self.conn.register('temp_error_df', df)
            self.conn.execute("INSERT INTO error_logs SELECT * FROM temp_error_df")
            self.conn.unregister('temp_error_df')

            logger.info(f"Inserted {len(df)} error log records")
        except Exception as e:
            logger.error(f"Failed to insert error logs: {e}", exc_info=True)
            raise

    def query(self, sql: str) -> pd.DataFrame:
        """Execute a SQL query and return results as DataFrame.

        Args:
            sql: SQL query string

        Returns:
            Query results as DataFrame
        """
        try:
            result = self.conn.execute(sql).fetchdf()
            return result
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
            service_name: Filter by service name
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Limit number of results

        Returns:
            Filtered service logs
        """
        where_clauses = []

        if service_name:
            where_clauses.append(f"service_name = '{service_name}'")
        if start_time:
            where_clauses.append(f"record_time >= '{start_time}'")
        if end_time:
            where_clauses.append(f"record_time <= '{end_time}'")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit_sql = f"LIMIT {limit}" if limit else ""

        sql = f"""
            SELECT * FROM service_logs
            WHERE {where_sql}
            ORDER BY record_time DESC
            {limit_sql}
        """

        return self.query(sql)

    def get_error_logs(self,
                      error_code: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: Optional[int] = None) -> pd.DataFrame:
        """Get error logs with optional filters.

        Args:
            error_code: Filter by error code
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Limit number of results

        Returns:
            Filtered error logs
        """
        where_clauses = []

        if error_code:
            where_clauses.append(f"error_codes = '{error_code}'")
        if start_time:
            where_clauses.append(f"record_time >= '{start_time}'")
        if end_time:
            where_clauses.append(f"record_time <= '{end_time}'")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit_sql = f"LIMIT {limit}" if limit else ""

        sql = f"""
            SELECT * FROM error_logs
            WHERE {where_sql}
            ORDER BY record_time DESC
            {limit_sql}
        """

        return self.query(sql)

    def get_all_services(self) -> List[str]:
        """Get list of all unique service names.

        Returns:
            List of service names
        """
        sql = "SELECT DISTINCT service_name FROM service_logs ORDER BY service_name"
        result = self.query(sql)
        return result['service_name'].tolist()

    def get_time_range(self) -> Dict[str, datetime]:
        """Get the time range of data in the database.

        Returns:
            Dictionary with min_time and max_time
        """
        sql = """
            SELECT
                MIN(record_time) as min_time,
                MAX(record_time) as max_time
            FROM service_logs
        """
        result = self.query(sql)
        return {
            'min_time': result['min_time'].iloc[0],
            'max_time': result['max_time'].iloc[0]
        }

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
