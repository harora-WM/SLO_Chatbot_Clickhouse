"""
Kafka to ClickHouse Consumer
Reads transaction metrics from Kafka topic and loads into ClickHouse with flattened schema.
Each message's transactionSeries array is flattened into individual time-series rows.
"""
import json
import clickhouse_connect
from kafka import KafkaConsumer
from typing import List, Dict, Any, Tuple
from datetime import datetime
import sys


class KafkaClickHouseConsumer:
    """Consumer that reads from Kafka and writes flattened time-series data to ClickHouse."""

    def __init__(
        self,
        kafka_bootstrap_servers: List[str],
        kafka_topic: str,
        kafka_group_id: str,
        clickhouse_host: str,
        clickhouse_port: int = 8123,
        clickhouse_user: str = 'default',
        clickhouse_password: str = ''
    ):
        """
        Initialize Kafka consumer and ClickHouse client.

        Args:
            kafka_bootstrap_servers: List of Kafka broker addresses
            kafka_topic: Kafka topic name to consume from
            kafka_group_id: Consumer group ID for offset management
            clickhouse_host: ClickHouse server hostname
            clickhouse_port: ClickHouse HTTP port (default 8123)
            clickhouse_user: ClickHouse username
            clickhouse_password: ClickHouse password
        """
        self.kafka_topic = kafka_topic

        print(f"Connecting to Kafka...")
        print(f"  Brokers: {kafka_bootstrap_servers}")
        print(f"  Topic: {kafka_topic}")
        print(f"  Group ID: {kafka_group_id}")

        # Create Kafka consumer
        self.consumer = KafkaConsumer(
            kafka_topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=kafka_group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',  # Start from beginning if no offset
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            max_poll_records=50
        )

        print("✓ Connected to Kafka\n")

        print(f"Connecting to ClickHouse...")
        print(f"  Host: {clickhouse_host}:{clickhouse_port}")
        print(f"  User: {clickhouse_user}")

        # Create ClickHouse client
        try:
            self.ch_client = clickhouse_connect.get_client(
                host=clickhouse_host,
                port=clickhouse_port,
                username=clickhouse_user,
                password=clickhouse_password
            )
            print("✓ Connected to ClickHouse\n")
        except Exception as e:
            print(f"✗ Failed to connect to ClickHouse: {e}")
            print("\nMake sure ClickHouse is running. Run: ./clickhouse_setup.sh")
            sys.exit(1)

    def create_table_if_not_exists(self):
        """Create ClickHouse table with flattened schema if it doesn't exist."""
        print("Creating table 'transaction_metrics' if not exists...")

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS transaction_metrics (
            -- Transaction identifiers
            transaction_name String,
            transaction_id UInt32,
            application_id UInt32,
            application_name String,

            -- Timestamp fields
            timestamp DateTime64(3),
            timestamp_str String,
            key String,

            -- Performance metrics
            sum_response_time Float64,
            avg_response_time Float64,
            total_count Float64,
            success_count Float64,
            error_count Float64,
            success_rate Float64,
            error_rate Float64,

            -- SLO (Service Level Objective) metrics
            short_target_slo Float64,
            eb_allocated_percent Float64,
            eb_consumed_percent Float64,
            eb_left_percent Float64,

            -- Response metrics
            response_breach_count Float64,
            response_error_rate Float64,
            response_success_rate Float64,

            -- Health indicators
            timeliness_health String,
            response_health String,
            eb_health String,

            -- Breach flags
            eb_breached Bool,
            response_breached Bool,

            -- Response time percentiles
            percentile_25 Float64,
            percentile_50 Float64,
            percentile_75 Float64,
            percentile_90 Float64,
            percentile_95 Float64,
            percentile_99 Float64,

            -- Metadata
            timezone String,
            index_type String,
            sre_product String,

            -- Ingestion tracking
            ingestion_time DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (transaction_name, timestamp)
        SETTINGS index_granularity = 8192
        """

        try:
            self.ch_client.command(create_table_sql)
            print("✓ Table 'transaction_metrics' is ready\n")

            # Show table info
            row_count = self.ch_client.command('SELECT COUNT(*) FROM transaction_metrics')
            print(f"  Current row count: {row_count:,}")
        except Exception as e:
            print(f"✗ Failed to create table: {e}")
            sys.exit(1)

    def flatten_transaction_series(self, message: Dict[str, Any]) -> Tuple[List[List[Any]], int]:
        """
        Flatten nested transaction series into rows for ClickHouse insertion.

        Args:
            message: Kafka message containing transactionName and transactionSeries

        Returns:
            Tuple of (list of rows ready for ClickHouse, number of series items)
        """
        rows = []
        transaction_name = message.get('transactionName', '')
        transaction_series = message.get('transactionSeries', [])

        for series_item in transaction_series:
            # Parse timestamp (milliseconds since epoch)
            timestamp_str = series_item.get('timestampStr', '0')
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str) / 1000.0)
            except (ValueError, OSError):
                timestamp = datetime.fromtimestamp(0)

            # Extract percentiles (nested object)
            percentiles = series_item.get('avgPercentiles', {})

            # Build row with all 35 columns (matching table schema order)
            row = [
                transaction_name,
                series_item.get('transactionId', 0),
                series_item.get('applicationId', 0),
                series_item.get('applicationName', ''),

                timestamp,
                timestamp_str,
                series_item.get('key', ''),

                series_item.get('sumResponseTime', 0.0),
                series_item.get('avgResponseTime', 0.0),
                series_item.get('totalCount', 0.0),
                series_item.get('successCount', 0.0),
                series_item.get('errorCount', 0.0),
                series_item.get('successRate', 0.0),
                series_item.get('errorRate', 0.0),

                series_item.get('shortTargetSLO', 0.0),
                series_item.get('eBAllocatedPercent', 0.0),
                series_item.get('eBConsumedPercent', 0.0),
                series_item.get('eBLeftPercent', 0.0),

                series_item.get('responseBreachCount', 0.0),
                series_item.get('responseErrorRate', 0.0),
                series_item.get('responseSuccessRate', 0.0),

                series_item.get('timelinessHealth', ''),
                series_item.get('responseHealth', ''),
                series_item.get('ebHealth', ''),

                series_item.get('ebBreached', False),
                series_item.get('responseBreached', False),

                percentiles.get('25.0', 0.0),
                percentiles.get('50.0', 0.0),
                percentiles.get('75.0', 0.0),
                percentiles.get('90.0', 0.0),
                percentiles.get('95.0', 0.0),
                percentiles.get('99.0', 0.0),

                series_item.get('timezone', ''),
                series_item.get('index', ''),
                series_item.get('sre_product', '')
            ]
            rows.append(row)

        return rows, len(transaction_series)

    def insert_batch(self, rows: List[List[Any]]) -> bool:
        """
        Insert batch of rows into ClickHouse.

        Args:
            rows: List of row data to insert

        Returns:
            True if successful, False otherwise
        """
        if not rows:
            return True

        try:
            self.ch_client.insert(
                'transaction_metrics',
                rows,
                column_names=[
                    'transaction_name', 'transaction_id', 'application_id', 'application_name',
                    'timestamp', 'timestamp_str', 'key',
                    'sum_response_time', 'avg_response_time', 'total_count', 'success_count',
                    'error_count', 'success_rate', 'error_rate',
                    'short_target_slo', 'eb_allocated_percent', 'eb_consumed_percent', 'eb_left_percent',
                    'response_breach_count', 'response_error_rate', 'response_success_rate',
                    'timeliness_health', 'response_health', 'eb_health',
                    'eb_breached', 'response_breached',
                    'percentile_25', 'percentile_50', 'percentile_75', 'percentile_90',
                    'percentile_95', 'percentile_99',
                    'timezone', 'index_type', 'sre_product'
                ]
            )
            return True
        except Exception as e:
            print(f"  ✗ Insert failed: {e}")
            return False

    def consume_and_load(self, batch_size: int = 5000):
        """
        Consume messages from Kafka and load into ClickHouse.

        Args:
            batch_size: Number of rows to batch before inserting into ClickHouse
        """
        print("=" * 70)
        print(f"Starting Kafka → ClickHouse data pipeline")
        print(f"Topic: {self.kafka_topic}")
        print(f"Batch size: {batch_size:,} rows")
        print("=" * 70)
        print("\nPress Ctrl+C to stop\n")

        batch_rows = []
        messages_processed = 0
        total_rows_inserted = 0
        total_series_items = 0

        try:
            for message in self.consumer:
                messages_processed += 1

                # Flatten the message (one Kafka message → multiple ClickHouse rows)
                rows, series_count = self.flatten_transaction_series(message.value)
                batch_rows.extend(rows)
                total_series_items += series_count

                transaction_name = message.value.get('transactionName', 'Unknown')
                print(f"[{messages_processed}] {transaction_name[:60]}")
                print(f"     → {series_count} time-series records extracted")

                # Insert batch when threshold reached
                if len(batch_rows) >= batch_size:
                    print(f"\n  Inserting batch of {len(batch_rows):,} rows...")
                    if self.insert_batch(batch_rows):
                        print(f"  ✓ Batch inserted successfully\n")
                        total_rows_inserted += len(batch_rows)
                    batch_rows = []

        except KeyboardInterrupt:
            print("\n\n⚠ Stopping consumer (Ctrl+C detected)...")

        finally:
            # Insert remaining rows
            if batch_rows:
                print(f"\nInserting final batch of {len(batch_rows):,} rows...")
                if self.insert_batch(batch_rows):
                    print("✓ Final batch inserted successfully")
                    total_rows_inserted += len(batch_rows)

            # Close connections
            self.consumer.close()
            self.ch_client.close()

            # Summary
            print("\n" + "=" * 70)
            print("Pipeline Summary")
            print("=" * 70)
            print(f"Kafka messages processed:    {messages_processed:,}")
            print(f"Time-series records:         {total_series_items:,}")
            print(f"ClickHouse rows inserted:    {total_rows_inserted:,}")
            print("=" * 70)
            print("\nConnections closed. Pipeline complete.")


def main():
    """Main execution flow."""
    print("=" * 70)
    print("Kafka → ClickHouse Data Pipeline")
    print("=" * 70)
    print()

    # Configuration
    KAFKA_BOOTSTRAP_SERVERS = ['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']
    KAFKA_TOPIC = 'services_series_12days'
    KAFKA_GROUP_ID = 'clickhouse_consumer_group'

    CLICKHOUSE_HOST = 'localhost'
    CLICKHOUSE_PORT = 8123
    CLICKHOUSE_USER = 'default'
    CLICKHOUSE_PASSWORD = ''

    # Create consumer instance
    consumer = KafkaClickHouseConsumer(
        kafka_bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        kafka_topic=KAFKA_TOPIC,
        kafka_group_id=KAFKA_GROUP_ID,
        clickhouse_host=CLICKHOUSE_HOST,
        clickhouse_port=CLICKHOUSE_PORT,
        clickhouse_user=CLICKHOUSE_USER,
        clickhouse_password=CLICKHOUSE_PASSWORD
    )

    # Create table schema
    consumer.create_table_if_not_exists()

    # Start consuming and loading data
    consumer.consume_and_load(batch_size=5000)


if __name__ == "__main__":
    main()
