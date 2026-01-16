"""Debug script for OpenSearch data fetching issues."""

import sys
import json
from datetime import datetime, timedelta
from data.ingestion.opensearch_client import OpenSearchClient
from data.ingestion.data_loader import DataLoader
from data.database.duckdb_manager import DuckDBManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_opensearch_connection():
    """Test basic OpenSearch connection."""
    print("\n" + "="*60)
    print("TEST 1: OpenSearch Connection")
    print("="*60)

    try:
        client = OpenSearchClient()
        if client.test_connection():
            print("✅ OpenSearch connection successful")
            return True
        else:
            print("❌ OpenSearch connection failed")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


def test_small_query():
    """Test fetching a small dataset."""
    print("\n" + "="*60)
    print("TEST 2: Small Query (Last 4 hours, 100 results)")
    print("="*60)

    try:
        client = OpenSearchClient()
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=4)

        print(f"Fetching from {start_time} to {end_time}")

        service_logs = client.query_service_logs(
            start_time=start_time,
            end_time=end_time,
            size=100,
            use_scroll=False
        )

        error_logs = client.query_error_logs(
            start_time=start_time,
            end_time=end_time,
            size=100,
            use_scroll=False
        )

        service_count = len(service_logs.get('hits', {}).get('hits', []))
        error_count = len(error_logs.get('hits', {}).get('hits', []))

        print(f"✅ Fetched {service_count} service logs")
        print(f"✅ Fetched {error_count} error logs")

        return service_logs, error_logs

    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_data_parsing(service_logs, error_logs):
    """Test parsing the fetched data."""
    print("\n" + "="*60)
    print("TEST 3: Data Parsing")
    print("="*60)

    if not service_logs or not error_logs:
        print("⚠️  Skipping - no data to parse")
        return False

    try:
        import tempfile
        import os

        # Save to temp files
        with tempfile.NamedTemporaryFile(mode='w', suffix='_service.json', delete=False) as f:
            json.dump(service_logs, f)
            service_temp_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_error.json', delete=False) as f:
            json.dump(error_logs, f)
            error_temp_path = f.name

        try:
            # Test parsing
            db_manager = DuckDBManager()
            data_loader = DataLoader(db_manager)

            print("Parsing service logs...")
            service_df = data_loader.load_service_logs_from_json(service_temp_path)
            print(f"✅ Parsed {len(service_df)} service log records")
            print(f"   Columns: {list(service_df.columns)}")
            print(f"   Sample IDs: {service_df['id'].head(3).tolist()}")

            print("\nParsing error logs...")
            error_df = data_loader.load_error_logs_from_json(error_temp_path)
            print(f"✅ Parsed {len(error_df)} error log records")
            print(f"   Columns: {list(error_df.columns)}")
            print(f"   Sample IDs: {error_df['id'].head(3).tolist()}")

            return True

        finally:
            os.unlink(service_temp_path)
            os.unlink(error_temp_path)

    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_large_query():
    """Test fetching a large dataset with scroll API."""
    print("\n" + "="*60)
    print("TEST 4: Large Query with Scroll API (Last 30 days)")
    print("="*60)
    print("⚠️  This may take a while...")

    try:
        client = OpenSearchClient()
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        print(f"Fetching from {start_time} to {end_time}")
        print("Using scroll API for unlimited results...")

        service_logs = client.query_service_logs(
            start_time=start_time,
            end_time=end_time,
            size=1000,
            use_scroll=True
        )

        service_count = len(service_logs.get('hits', {}).get('hits', []))
        print(f"✅ Fetched {service_count:,} service logs")

        if service_count > 10000:
            print("   Testing data structure...")
            hits = service_logs.get('hits', {}).get('hits', [])
            print(f"   First record ID: {hits[0].get('_id')}")
            print(f"   Last record ID: {hits[-1].get('_id')}")
            print(f"   Record at index 10000: {hits[10000].get('_id')}")

        return True

    except Exception as e:
        print(f"❌ Large query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all debug tests."""
    print("\n" + "="*60)
    print("OPENSEARCH DEBUG TOOL")
    print("="*60)
    print("This will help identify issues with OpenSearch data fetching\n")

    # Test 1: Connection
    if not test_opensearch_connection():
        print("\n❌ Cannot proceed without OpenSearch connection")
        sys.exit(1)

    # Test 2: Small query
    service_logs, error_logs = test_small_query()

    # Test 3: Data parsing
    if service_logs and error_logs:
        test_data_parsing(service_logs, error_logs)

    # Test 4: Large query (optional)
    print("\n" + "="*60)
    response = input("Run large query test (30 days)? This may take several minutes. (y/n): ")
    if response.lower() == 'y':
        test_large_query()
    else:
        print("⚠️  Skipping large query test")

    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
    print("\nIf all tests passed, the issue may be specific to the UI interaction.")
    print("Check the logs and error details in the Streamlit interface.")


if __name__ == "__main__":
    main()
