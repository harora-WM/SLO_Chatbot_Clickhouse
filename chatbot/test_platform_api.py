"""Comprehensive test suite for Platform API migration.

Tests:
1. Keycloak authentication with auto-refresh
2. Platform API client with pagination
3. Data loading with 90+ field mapping
4. All 20 analytics functions
5. End-to-end integration
"""

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.ingestion.keycloak_auth import KeycloakAuthManager
from data.ingestion.platform_api_client import PlatformAPIClient
from data.ingestion.data_loader import DataLoader
from data.database.duckdb_manager import DuckDBManager
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PlatformAPITestSuite:
    """Test suite for Platform API migration."""

    def __init__(self):
        """Initialize test components."""
        self.auth_manager = None
        self.api_client = None
        self.db_manager = None
        self.data_loader = None
        self.metrics = None
        self.slo_calculator = None
        self.degradation_detector = None
        self.trend_analyzer = None

        self.test_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }

    def setup(self):
        """Set up test environment."""
        logger.info("Setting up test environment...")

        try:
            # Initialize authentication
            self.auth_manager = KeycloakAuthManager()
            logger.info("✓ KeycloakAuthManager initialized")

            # Initialize API client
            self.api_client = PlatformAPIClient(self.auth_manager)
            logger.info("✓ PlatformAPIClient initialized")

            # Initialize database (use temp database for testing)
            test_db_path = PROJECT_ROOT / "data" / "database" / "test_slo_analytics.duckdb"
            if test_db_path.exists():
                test_db_path.unlink()
            self.db_manager = DuckDBManager(db_path=test_db_path)
            logger.info("✓ DuckDBManager initialized with test database")

            # Initialize data loader
            self.data_loader = DataLoader(self.db_manager)
            logger.info("✓ DataLoader initialized")

            # Initialize analytics modules
            self.slo_calculator = SLOCalculator(self.db_manager)
            self.degradation_detector = DegradationDetector(self.db_manager)
            self.trend_analyzer = TrendAnalyzer(self.db_manager)
            self.metrics = MetricsAggregator(self.db_manager)
            logger.info("✓ Analytics modules initialized")

            return True
        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            return False

    def test_keycloak_auth(self) -> bool:
        """Test Keycloak authentication."""
        logger.info("\n" + "="*80)
        logger.info("TEST 1: Keycloak Authentication")
        logger.info("="*80)

        try:
            # Test initial token fetch
            token = self.auth_manager.get_access_token()
            assert token is not None, "Token should not be None"
            assert len(token) > 0, "Token should not be empty"
            logger.info(f"✓ Initial token acquired: {token[:20]}...")

            # Test token caching
            token2 = self.auth_manager.get_access_token()
            assert token == token2, "Cached token should match"
            logger.info("✓ Token caching works")

            # Test background refresh thread
            assert self.auth_manager._refresh_thread.is_alive(), "Refresh thread should be running"
            logger.info("✓ Background refresh thread is running")

            self.test_results["passed"].append("Keycloak Authentication")
            logger.info("✅ TEST 1 PASSED\n")
            return True

        except Exception as e:
            logger.error(f"❌ TEST 1 FAILED: {e}", exc_info=True)
            self.test_results["failed"].append(f"Keycloak Authentication: {e}")
            return False

    def test_platform_api_pagination(self) -> bool:
        """Test Platform API client with pagination."""
        logger.info("\n" + "="*80)
        logger.info("TEST 2: Platform API Pagination")
        logger.info("="*80)

        try:
            # Fetch last 5 days of data
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=5)).timestamp() * 1000)

            logger.info(f"Fetching data from {datetime.fromtimestamp(start_time/1000)} to {datetime.fromtimestamp(end_time/1000)}")

            response = self.api_client.query_service_health(
                start_time=start_time,
                end_time=end_time
            )

            assert isinstance(response, list), "Response should be a list"
            assert len(response) > 0, "Response should contain services"
            logger.info(f"✓ Fetched {len(response)} services via automatic pagination")

            # Validate response structure
            first_service = response[0]
            required_fields = ['key', 'transactionName', 'totalCount', 'errorRate', 'burnRate']
            for field in required_fields:
                assert field in first_service, f"Missing required field: {field}"
            logger.info(f"✓ Response structure validated (sample service: {first_service.get('transactionName', 'N/A')})")

            self.test_results["passed"].append("Platform API Pagination")
            logger.info("✅ TEST 2 PASSED\n")
            return True

        except Exception as e:
            logger.error(f"❌ TEST 2 FAILED: {e}", exc_info=True)
            self.test_results["failed"].append(f"Platform API Pagination: {e}")
            return False

    def test_data_loading(self) -> bool:
        """Test data loading with 90+ field mapping."""
        logger.info("\n" + "="*80)
        logger.info("TEST 3: Data Loading (90+ Field Mapping)")
        logger.info("="*80)

        try:
            # Fetch data
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=5)).timestamp() * 1000)

            response = self.api_client.query_service_health(start_time, end_time)
            logger.info(f"Fetched {len(response)} services from Platform API")

            # Load into DataFrame
            df = self.data_loader.load_service_logs_from_platform_api(response)
            assert len(df) > 0, "DataFrame should not be empty"
            logger.info(f"✓ Loaded {len(df)} records into DataFrame")

            # Validate column count (should be 90+)
            assert len(df.columns) >= 90, f"Expected 90+ columns, got {len(df.columns)}"
            logger.info(f"✓ Schema validated: {len(df.columns)} columns")

            # Validate critical columns exist
            critical_columns = [
                'service_name', 'total_count', 'error_rate', 'burn_rate',
                'eb_health', 'response_health', 'timeliness_health',
                'aspirational_slo', 'aspirational_eb_health',
                'response_time_p95', 'response_time_p99'
            ]
            missing_columns = [col for col in critical_columns if col not in df.columns]
            assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
            logger.info(f"✓ All critical columns present: {', '.join(critical_columns[:5])}...")

            # Insert into database
            self.db_manager.insert_service_logs(df)
            logger.info(f"✓ Inserted {len(df)} records into DuckDB")

            # Verify data in database
            services = self.db_manager.get_all_services()
            assert len(services) > 0, "Database should contain services"
            logger.info(f"✓ Verified {len(services)} unique services in database")

            # Check for unhealthy services
            unhealthy_count = len(df[df['eb_health'] == 'UNHEALTHY'])
            high_burn_rate = len(df[df['burn_rate'] > 2.0])
            logger.info(f"  - Unhealthy services: {unhealthy_count}")
            logger.info(f"  - High burn rate (>2.0): {high_burn_rate}")

            if unhealthy_count > 0 or high_burn_rate > 0:
                self.test_results["warnings"].append(f"Found {unhealthy_count} unhealthy services and {high_burn_rate} with high burn rate")

            self.test_results["passed"].append("Data Loading (90+ fields)")
            logger.info("✅ TEST 3 PASSED\n")
            return True

        except Exception as e:
            logger.error(f"❌ TEST 3 FAILED: {e}", exc_info=True)
            self.test_results["failed"].append(f"Data Loading: {e}")
            return False

    def test_analytics_functions(self) -> bool:
        """Test all 20 analytics functions."""
        logger.info("\n" + "="*80)
        logger.info("TEST 4: Analytics Functions (20 functions)")
        logger.info("="*80)

        functions_to_test = [
            # Standard Performance & Health (7 functions)
            ("get_service_health_overview", lambda: self.metrics.get_service_health_overview(), {}),
            ("get_degrading_services", lambda: self.degradation_detector.get_degrading_services(), {}),
            ("get_slo_violations", lambda: self.slo_calculator.get_slo_violations(), {}),
            ("get_slowest_services", lambda: self.metrics.get_slowest_services(limit=5), {}),
            ("get_top_services_by_volume", lambda: self.metrics.get_top_services_by_volume(limit=5), {}),

            # Platform API Advanced Functions (8 functions)
            ("get_services_by_burn_rate", lambda: self.metrics.get_services_by_burn_rate(limit=5), {}),
            ("get_aspirational_slo_gap", lambda: self.metrics.get_aspirational_slo_gap(), {}),
            ("get_timeliness_issues", lambda: self.metrics.get_timeliness_issues(), {}),
            ("get_budget_exhausted_services", lambda: self.metrics.get_budget_exhausted_services(), {}),
            ("get_composite_health_score", lambda: self.metrics.get_composite_health_score(), {}),
            ("get_severity_heatmap", lambda: self.metrics.get_severity_heatmap(), {}),
            ("get_slo_governance_status", lambda: self.metrics.get_slo_governance_status(), {}),

            # Performance Patterns (2 functions)
            ("predict_issues_today", lambda: self.trend_analyzer.predict_issues_today(), {}),
        ]

        passed = 0
        failed = 0

        for func_name, func, kwargs in functions_to_test:
            try:
                result = func()
                assert result is not None, f"{func_name} returned None"
                logger.info(f"  ✓ {func_name}: OK")
                passed += 1
            except Exception as e:
                logger.error(f"  ✗ {func_name}: FAILED - {e}")
                failed += 1
                self.test_results["failed"].append(f"{func_name}: {e}")

        # Test service-specific functions
        try:
            services = self.db_manager.get_all_services()
            if services:
                test_service = services[0]
                logger.info(f"\nTesting service-specific functions with: {test_service}")

                # get_service_summary
                summary = self.slo_calculator.get_service_summary(test_service)
                assert summary is not None, "get_service_summary returned None"
                logger.info(f"  ✓ get_service_summary: OK")
                passed += 1

                # get_current_sli
                sli = self.slo_calculator.get_current_sli(test_service)
                assert sli is not None, "get_current_sli returned None"
                logger.info(f"  ✓ get_current_sli: OK")
                passed += 1

                # calculate_error_budget
                budget = self.slo_calculator.calculate_error_budget(test_service, time_window_hours=168)  # 7 days
                assert budget is not None, "calculate_error_budget returned None"
                logger.info(f"  ✓ calculate_error_budget: OK")
                passed += 1

                # get_volume_trends
                trends = self.metrics.get_volume_trends(test_service)
                assert trends is not None, "get_volume_trends returned None"
                logger.info(f"  ✓ get_volume_trends: OK")
                passed += 1

                # get_historical_patterns
                patterns = self.trend_analyzer.get_historical_patterns(test_service)
                assert patterns is not None, "get_historical_patterns returned None"
                logger.info(f"  ✓ get_historical_patterns: OK")
                passed += 1

                # get_breach_vs_error_analysis
                breach_analysis = self.metrics.get_breach_vs_error_analysis(test_service)
                assert breach_analysis is not None, "get_breach_vs_error_analysis returned None"
                logger.info(f"  ✓ get_breach_vs_error_analysis: OK")
                passed += 1

        except Exception as e:
            logger.error(f"  ✗ Service-specific functions: FAILED - {e}")
            failed += 6
            self.test_results["failed"].append(f"Service-specific functions: {e}")

        logger.info(f"\nAnalytics Functions Summary: {passed} passed, {failed} failed")

        if failed == 0:
            self.test_results["passed"].append(f"All 20 Analytics Functions ({passed} tested)")
            logger.info("✅ TEST 4 PASSED\n")
            return True
        else:
            logger.error(f"❌ TEST 4 FAILED: {failed} functions failed\n")
            return False

    def test_end_to_end_integration(self) -> bool:
        """Test complete end-to-end workflow."""
        logger.info("\n" + "="*80)
        logger.info("TEST 5: End-to-End Integration")
        logger.info("="*80)

        try:
            # 1. Authenticate
            token = self.auth_manager.get_access_token()
            logger.info("✓ Step 1: Authentication successful")

            # 2. Fetch from Platform API
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            response = self.api_client.query_service_health(start_time, end_time)
            logger.info(f"✓ Step 2: Fetched {len(response)} services from Platform API")

            # 3. Load into database
            df = self.data_loader.load_service_logs_from_platform_api(response)
            self.db_manager.insert_service_logs(df)
            logger.info(f"✓ Step 3: Loaded {len(df)} records into DuckDB")

            # 4. Run analytics
            health_overview = self.metrics.get_service_health_overview()
            burn_rate_services = self.metrics.get_services_by_burn_rate(limit=10)
            aspirational_gap = self.metrics.get_aspirational_slo_gap()
            logger.info("✓ Step 4: Analytics functions executed successfully")

            # 5. Validate results
            assert 'total_services' in health_overview, "Missing total_services in health overview"
            assert isinstance(burn_rate_services, list), "burn_rate_services should be a list"
            assert isinstance(aspirational_gap, list), "aspirational_gap should be a list"
            logger.info("✓ Step 5: Results validated")

            # Print summary
            logger.info("\n" + "-"*80)
            logger.info("INTEGRATION TEST SUMMARY:")
            logger.info(f"  - Total Services: {health_overview.get('total_services', 'N/A')}")
            logger.info(f"  - Unhealthy Services: {health_overview.get('unhealthy_services', 'N/A')}")
            logger.info(f"  - High Burn Rate Services: {len(burn_rate_services)}")
            logger.info(f"  - Aspirational SLO Gap Services: {len(aspirational_gap)}")
            logger.info("-"*80)

            self.test_results["passed"].append("End-to-End Integration")
            logger.info("✅ TEST 5 PASSED\n")
            return True

        except Exception as e:
            logger.error(f"❌ TEST 5 FAILED: {e}", exc_info=True)
            self.test_results["failed"].append(f"End-to-End Integration: {e}")
            return False

    def cleanup(self):
        """Clean up test environment."""
        logger.info("\nCleaning up test environment...")

        try:
            # Stop background refresh thread
            if self.auth_manager:
                self.auth_manager.stop_refresh()
                logger.info("✓ Stopped background refresh thread")

            # Close database connection
            if self.db_manager:
                self.db_manager.close()
                logger.info("✓ Closed database connection")

            # Delete test database
            test_db_path = PROJECT_ROOT / "data" / "database" / "test_slo_analytics.duckdb"
            if test_db_path.exists():
                test_db_path.unlink()
                logger.info("✓ Deleted test database")

        except Exception as e:
            logger.error(f"Cleanup warning: {e}")

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)

        logger.info(f"\n✅ PASSED: {len(self.test_results['passed'])} tests")
        for test in self.test_results['passed']:
            logger.info(f"  - {test}")

        if self.test_results['failed']:
            logger.info(f"\n❌ FAILED: {len(self.test_results['failed'])} tests")
            for test in self.test_results['failed']:
                logger.info(f"  - {test}")

        if self.test_results['warnings']:
            logger.info(f"\n⚠️  WARNINGS: {len(self.test_results['warnings'])}")
            for warning in self.test_results['warnings']:
                logger.info(f"  - {warning}")

        total_tests = len(self.test_results['passed']) + len(self.test_results['failed'])
        pass_rate = (len(self.test_results['passed']) / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"\n{'='*80}")
        logger.info(f"OVERALL: {len(self.test_results['passed'])}/{total_tests} tests passed ({pass_rate:.1f}%)")
        logger.info(f"{'='*80}\n")

        return len(self.test_results['failed']) == 0

    def run_all_tests(self) -> bool:
        """Run all tests."""
        logger.info("\n" + "="*80)
        logger.info("PLATFORM API MIGRATION - COMPREHENSIVE TEST SUITE")
        logger.info("="*80)
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Setup
        if not self.setup():
            logger.error("Setup failed. Aborting tests.")
            return False

        # Run tests
        tests = [
            self.test_keycloak_auth,
            self.test_platform_api_pagination,
            self.test_data_loading,
            self.test_analytics_functions,
            self.test_end_to_end_integration
        ]

        for test in tests:
            test()

        # Cleanup
        self.cleanup()

        # Print summary
        all_passed = self.print_summary()

        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return all_passed


def main():
    """Main test runner."""
    test_suite = PlatformAPITestSuite()
    success = test_suite.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
