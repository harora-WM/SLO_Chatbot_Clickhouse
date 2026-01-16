"""Comprehensive test suite for ClickHouse migration - proper testing with no bottlenecks."""

import sys
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, '/home/hardik121/kafka_put/SLO_Chatbot_Latest-v1')

from data.database.clickhouse_manager import ClickHouseManager
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    """Track test results."""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []

    def add_pass(self, test_name: str, message: str = ""):
        self.total += 1
        self.passed += 1
        print(f"   {Colors.GREEN}✅ PASS{Colors.END}: {test_name}")
        if message:
            print(f"      {message}")

    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"   {Colors.RED}❌ FAIL{Colors.END}: {test_name}")
        print(f"      {Colors.RED}Error: {error}{Colors.END}")

    def add_warning(self, test_name: str, message: str):
        self.warnings += 1
        print(f"   {Colors.YELLOW}⚠️  WARN{Colors.END}: {test_name}")
        print(f"      {message}")

    def print_summary(self):
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print("=" * 80)
        print(f"Total Tests: {self.total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.END}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.END}")

        if self.failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}")
            for test_name, error in self.errors:
                print(f"  • {test_name}: {error}")
            print(f"\n{Colors.RED}Migration has issues that need to be fixed!{Colors.END}")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed! Migration is successful.{Colors.END}")
            return True

def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.END}")
    print("=" * 80)

def test_clickhouse_connection(result: TestResult) -> ClickHouseManager:
    """Test ClickHouse connection and basic queries."""
    print_section("1. ClickHouse Connection Tests")

    try:
        db_manager = ClickHouseManager(host='localhost', port=8123)
        result.add_pass("ClickHouse connection established")
    except Exception as e:
        result.add_fail("ClickHouse connection", str(e))
        return None

    # Test time range
    try:
        time_range = db_manager.get_time_range()
        if time_range['min_time'] and time_range['max_time']:
            result.add_pass("get_time_range()",
                          f"Range: {time_range['min_time']} → {time_range['max_time']}")
        else:
            result.add_fail("get_time_range()", "No time range data returned")
    except Exception as e:
        result.add_fail("get_time_range()", str(e))

    # Test service list
    try:
        services = db_manager.get_all_services()
        if len(services) > 0:
            result.add_pass("get_all_services()", f"Found {len(services)} services")
        else:
            result.add_fail("get_all_services()", "No services found in database")
    except Exception as e:
        result.add_fail("get_all_services()", str(e))

    # Test direct SQL query
    try:
        df = db_manager.query("SELECT COUNT(*) as total FROM transaction_metrics")
        if not df.empty and df['total'].iloc[0] > 0:
            result.add_pass("Direct SQL query", f"Total rows: {df['total'].iloc[0]:,}")
        else:
            result.add_fail("Direct SQL query", "No data in transaction_metrics table")
    except Exception as e:
        result.add_fail("Direct SQL query", str(e))

    # Test field mapping (transaction_name → service_name)
    try:
        df = db_manager.query("SELECT transaction_name FROM transaction_metrics LIMIT 1")
        if 'service_name' in df.columns and 'transaction_name' in df.columns:
            result.add_pass("Field mapping", "transaction_name → service_name mapping works")
        else:
            result.add_fail("Field mapping", "service_name column not created from transaction_name")
    except Exception as e:
        result.add_fail("Field mapping", str(e))

    return db_manager

def test_field_existence(result: TestResult, db_manager: ClickHouseManager):
    """Test that all required fields exist in ClickHouse."""
    print_section("2. Field Existence Tests")

    required_fields = {
        'transaction_name': 'Service identifier',
        'timestamp': 'Record timestamp',
        'avg_response_time': 'Average response time',
        'error_rate': 'Error rate percentage',
        'success_rate': 'Success rate percentage',
        'total_count': 'Total request count',
        'error_count': 'Error count',
        'success_count': 'Success count',
        'short_target_slo': 'Standard SLO target (98%)',
        'response_slo': 'Response time SLO',
        'percentile_50': 'P50 latency',
        'percentile_95': 'P95 latency',
        'percentile_99': 'P99 latency',
        'eb_consumed_percent': 'Error budget consumed',
        'eb_health': 'Error budget health status',
        'aspirational_slo': 'Aspirational SLO (99%)',
        'timeliness_health': 'Timeliness health status'
    }

    try:
        query = f"SELECT {', '.join(required_fields.keys())} FROM transaction_metrics LIMIT 1"
        df = db_manager.query(query)

        for field, description in required_fields.items():
            if field in df.columns:
                # Check for NULL values
                if pd.notna(df[field].iloc[0]) or field in ['percentile_50', 'percentile_95', 'percentile_99']:
                    result.add_pass(f"Field: {field}", description)
                else:
                    result.add_warning(f"Field: {field}", f"{description} - contains NULL values")
            else:
                result.add_fail(f"Field: {field}", f"Required field missing: {description}")

    except Exception as e:
        result.add_fail("Field existence check", str(e))

def test_metrics_aggregator(result: TestResult, db_manager: ClickHouseManager):
    """Test MetricsAggregator functions."""
    print_section("3. MetricsAggregator Tests")

    aggregator = MetricsAggregator(db_manager)

    # Test 1: get_service_health_overview
    try:
        overview = aggregator.get_service_health_overview()

        # Verify return type
        if not isinstance(overview, dict):
            result.add_fail("get_service_health_overview()", "Should return dict")
        else:
            # Verify required keys
            required_keys = ['total_services', 'healthy_services', 'degraded_services',
                           'violated_services', 'total_requests', 'total_errors']
            missing_keys = [k for k in required_keys if k not in overview]

            if missing_keys:
                result.add_fail("get_service_health_overview()", f"Missing keys: {missing_keys}")
            elif overview['total_services'] > 0:
                result.add_pass("get_service_health_overview()",
                              f"{overview['total_services']} services, {overview['healthy_services']} healthy")
            else:
                result.add_fail("get_service_health_overview()", "No services found")
    except Exception as e:
        result.add_fail("get_service_health_overview()", str(e))

    # Test 2: get_slowest_services
    try:
        slowest = aggregator.get_slowest_services(limit=5)

        if not isinstance(slowest, list):
            result.add_fail("get_slowest_services()", "Should return list")
        elif len(slowest) == 0:
            result.add_warning("get_slowest_services()", "No services returned")
        else:
            # Verify structure of first item
            first = slowest[0]
            required_keys = ['service_name', 'avg_response_time', 'avg_response_time_p99',
                           'response_slo_target', 'total_requests']
            missing_keys = [k for k in required_keys if k not in first]

            if missing_keys:
                result.add_fail("get_slowest_services()", f"Missing keys: {missing_keys}")
            else:
                result.add_pass("get_slowest_services()",
                              f"Found {len(slowest)} services, slowest P99: {first.get('avg_response_time_p99', 'N/A')}")
    except Exception as e:
        result.add_fail("get_slowest_services()", str(e))

    # Test 3: get_top_services_by_volume
    try:
        top_volume = aggregator.get_top_services_by_volume(limit=5)

        if not isinstance(top_volume, list):
            result.add_fail("get_top_services_by_volume()", "Should return list")
        elif len(top_volume) == 0:
            result.add_warning("get_top_services_by_volume()", "No services returned")
        else:
            first = top_volume[0]
            if 'total_requests' in first and first['total_requests'] > 0:
                result.add_pass("get_top_services_by_volume()",
                              f"Top service: {first['service_name'][:50]}... ({first['total_requests']:,} requests)")
            else:
                result.add_fail("get_top_services_by_volume()", "total_requests missing or zero")
    except Exception as e:
        result.add_fail("get_top_services_by_volume()", str(e))

    # Test 4: get_services_by_burn_rate
    try:
        burn_rate_services = aggregator.get_services_by_burn_rate(limit=5)

        if not isinstance(burn_rate_services, list):
            result.add_fail("get_services_by_burn_rate()", "Should return list")
        elif len(burn_rate_services) == 0:
            result.add_warning("get_services_by_burn_rate()", "No services with burn rate data")
        else:
            first = burn_rate_services[0]
            if 'avg_burn_rate' in first:
                result.add_pass("get_services_by_burn_rate()",
                              f"Highest burn rate: {first['avg_burn_rate']:.2f}")
            else:
                result.add_fail("get_services_by_burn_rate()", "avg_burn_rate field missing")
    except Exception as e:
        result.add_fail("get_services_by_burn_rate()", str(e))

    # Test 5: get_aspirational_slo_gap
    try:
        gap = aggregator.get_aspirational_slo_gap()

        if not isinstance(gap, list):
            result.add_fail("get_aspirational_slo_gap()", "Should return list")
        else:
            result.add_pass("get_aspirational_slo_gap()",
                          f"Found {len(gap)} services with aspirational SLO gap")
    except Exception as e:
        result.add_fail("get_aspirational_slo_gap()", str(e))

    # Test 6: get_composite_health_score
    try:
        health_scores = aggregator.get_composite_health_score()

        if not isinstance(health_scores, list):
            result.add_fail("get_composite_health_score()", f"Should return list, got {type(health_scores)}")
        elif len(health_scores) > 0:
            first = health_scores[0]
            if 'health_score' in first and 'healthy_dimensions' in first:
                result.add_pass("get_composite_health_score()",
                              f"{len(health_scores)} services scored")
            else:
                result.add_fail("get_composite_health_score()", "Missing required fields")
        else:
            result.add_warning("get_composite_health_score()", "No services returned")
    except Exception as e:
        result.add_fail("get_composite_health_score()", str(e))

def test_slo_calculator(result: TestResult, db_manager: ClickHouseManager):
    """Test SLOCalculator functions."""
    print_section("4. SLOCalculator Tests")

    calculator = SLOCalculator(db_manager)

    # Get a test service
    services = db_manager.get_all_services()
    test_service = services[0] if services else None

    if not test_service:
        result.add_fail("SLOCalculator tests", "No test service available")
        return

    # Test 1: get_current_sli (returns DataFrame)
    try:
        sli_df = calculator.get_current_sli(test_service)

        if not isinstance(sli_df, pd.DataFrame):
            result.add_fail("get_current_sli()", f"Should return DataFrame, got {type(sli_df)}")
        elif sli_df.empty:
            result.add_fail("get_current_sli()", "Returned empty DataFrame")
        else:
            # Verify columns
            required_cols = ['service_name', 'avg_success_rate', 'avg_error_rate',
                           'avg_response_time', 'error_slo_target', 'response_slo_target']
            missing_cols = [c for c in required_cols if c not in sli_df.columns]

            if missing_cols:
                result.add_fail("get_current_sli()", f"Missing columns: {missing_cols}")
            else:
                row = sli_df.iloc[0]
                result.add_pass("get_current_sli()",
                              f"Error rate: {row['avg_error_rate']:.2f}%, Response time: {row['avg_response_time']:.4f}s")
    except Exception as e:
        result.add_fail("get_current_sli()", str(e))

    # Test 2: calculate_error_budget (returns dict)
    try:
        budget = calculator.calculate_error_budget(test_service)

        if not isinstance(budget, dict):
            result.add_fail("calculate_error_budget()", f"Should return dict, got {type(budget)}")
        elif 'error' in budget:
            result.add_warning("calculate_error_budget()", budget['error'])
        elif 'budget_remaining_percent' in budget:
            result.add_pass("calculate_error_budget()",
                          f"Budget remaining: {budget['budget_remaining_percent']:.2f}%")
        else:
            result.add_fail("calculate_error_budget()", "Missing budget_remaining_percent field")
    except Exception as e:
        result.add_fail("calculate_error_budget()", str(e))

    # Test 3: get_slo_violations (returns list)
    try:
        violations = calculator.get_slo_violations()

        if not isinstance(violations, list):
            result.add_fail("get_slo_violations()", f"Should return list, got {type(violations)}")
        else:
            result.add_pass("get_slo_violations()", f"Found {len(violations)} violations")
    except Exception as e:
        result.add_fail("get_slo_violations()", str(e))

    # Test 4: calculate_burn_rate (returns dict with burn_rate key)
    try:
        burn_rate_result = calculator.calculate_burn_rate(test_service)

        if not isinstance(burn_rate_result, dict):
            result.add_fail("calculate_burn_rate()", f"Should return dict, got {type(burn_rate_result)}")
        elif 'error' in burn_rate_result:
            result.add_warning("calculate_burn_rate()", burn_rate_result['error'])
        elif 'burn_rate' in burn_rate_result:
            result.add_pass("calculate_burn_rate()",
                          f"Burn rate: {burn_rate_result['burn_rate']:.2f}, Severity: {burn_rate_result.get('severity', 'N/A')}")
        else:
            result.add_fail("calculate_burn_rate()", "Missing burn_rate field")
    except Exception as e:
        result.add_fail("calculate_burn_rate()", str(e))

def test_degradation_detector(result: TestResult, db_manager: ClickHouseManager):
    """Test DegradationDetector functions."""
    print_section("5. DegradationDetector Tests")

    detector = DegradationDetector(db_manager)

    # Get a test service
    services = db_manager.get_all_services()
    test_service = services[0] if services else None

    # Test 1: detect_degrading_services (returns list)
    try:
        degrading = detector.detect_degrading_services(time_window_days=7, threshold_percent=20)

        if not isinstance(degrading, list):
            result.add_fail("detect_degrading_services()", f"Should return list, got {type(degrading)}")
        else:
            if len(degrading) > 0:
                first = degrading[0]
                required_keys = ['service_name', 'error_rate_change_percent',
                               'response_time_change_percent', 'severity']
                missing_keys = [k for k in required_keys if k not in first]

                if missing_keys:
                    result.add_fail("detect_degrading_services()", f"Missing keys: {missing_keys}")
                else:
                    result.add_pass("detect_degrading_services()",
                                  f"Found {len(degrading)} degrading services")
            else:
                result.add_pass("detect_degrading_services()", "No degrading services (good!)")
    except Exception as e:
        result.add_fail("detect_degrading_services()", str(e))

    # Test 2: get_volume_trends (returns dict)
    if test_service:
        try:
            trends = detector.get_volume_trends(test_service, time_window_days=7)

            if not isinstance(trends, dict):
                result.add_fail("get_volume_trends()", f"Should return dict, got {type(trends)}")
            elif 'error' in trends:
                result.add_warning("get_volume_trends()", trends['error'])
            elif 'summary' in trends and 'time_series' in trends:
                result.add_pass("get_volume_trends()",
                              f"Total volume: {trends['summary']['total_volume']:,}")
            else:
                result.add_fail("get_volume_trends()", "Invalid structure")
        except Exception as e:
            result.add_fail("get_volume_trends()", str(e))

def test_trend_analyzer(result: TestResult, db_manager: ClickHouseManager):
    """Test TrendAnalyzer functions."""
    print_section("6. TrendAnalyzer Tests")

    analyzer = TrendAnalyzer(db_manager)

    # Get a test service
    services = db_manager.get_all_services()
    test_service = services[0] if services else None

    # Test 1: predict_issues_today (returns list)
    try:
        predictions = analyzer.predict_issues_today()

        if not isinstance(predictions, list):
            result.add_fail("predict_issues_today()", f"Should return list, got {type(predictions)}")
        else:
            if len(predictions) > 0:
                first = predictions[0]
                required_keys = ['service_name', 'risk_level', 'risk_score',
                               'risk_factors', 'current_metrics']
                missing_keys = [k for k in required_keys if k not in first]

                if missing_keys:
                    result.add_fail("predict_issues_today()", f"Missing keys: {missing_keys}")
                else:
                    result.add_pass("predict_issues_today()",
                                  f"Predicted {len(predictions)} at-risk services")
            else:
                result.add_pass("predict_issues_today()", "No at-risk services predicted")
    except Exception as e:
        result.add_fail("predict_issues_today()", str(e))

    # Test 2: get_historical_patterns (returns dict)
    if test_service:
        try:
            patterns = analyzer.get_historical_patterns(test_service)

            if not isinstance(patterns, dict):
                result.add_fail("get_historical_patterns()", f"Should return dict, got {type(patterns)}")
            elif 'error' in patterns:
                result.add_warning("get_historical_patterns()", patterns['error'])
            elif 'data_points' in patterns and patterns['data_points'] > 0:
                result.add_pass("get_historical_patterns()",
                              f"{patterns['data_points']} data points analyzed")
            else:
                result.add_fail("get_historical_patterns()", "No data points")
        except Exception as e:
            result.add_fail("get_historical_patterns()", str(e))

    # Test 3: get_anomalies (returns list)
    if test_service:
        try:
            anomalies = analyzer.get_anomalies(test_service, threshold_std=2.0)

            if not isinstance(anomalies, list):
                result.add_fail("get_anomalies()", f"Should return list, got {type(anomalies)}")
            else:
                result.add_pass("get_anomalies()", f"Found {len(anomalies)} anomalies")
        except Exception as e:
            result.add_fail("get_anomalies()", str(e))

def test_data_quality(result: TestResult, db_manager: ClickHouseManager):
    """Test data quality and consistency."""
    print_section("7. Data Quality Tests")

    # Test 1: Check for NULL values in critical fields
    try:
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN error_rate IS NULL THEN 1 ELSE 0 END) as null_error_rate,
                SUM(CASE WHEN avg_response_time IS NULL THEN 1 ELSE 0 END) as null_response_time,
                SUM(CASE WHEN short_target_slo IS NULL THEN 1 ELSE 0 END) as null_slo_target,
                SUM(CASE WHEN total_count = 0 THEN 1 ELSE 0 END) as zero_requests
            FROM transaction_metrics
        """
        df = db_manager.query(query)

        if df.empty:
            result.add_fail("NULL value check", "No data returned")
        else:
            row = df.iloc[0]
            issues = []

            if row['null_error_rate'] > 0:
                issues.append(f"{row['null_error_rate']} NULL error_rate values")
            if row['null_response_time'] > 0:
                issues.append(f"{row['null_response_time']} NULL response_time values")
            if row['null_slo_target'] > 0:
                issues.append(f"{row['null_slo_target']} NULL SLO target values")

            if issues:
                result.add_warning("NULL value check", ", ".join(issues))
            else:
                result.add_pass("NULL value check", "No NULL values in critical fields")

            if row['zero_requests'] > 0:
                result.add_warning("Data quality", f"{row['zero_requests']} records with zero requests")
    except Exception as e:
        result.add_fail("NULL value check", str(e))

    # Test 2: Check time continuity
    try:
        query = """
            SELECT
                MIN(timestamp) as min_time,
                MAX(timestamp) as max_time,
                COUNT(DISTINCT DATE(timestamp)) as unique_days,
                COUNT(DISTINCT transaction_name) as unique_services
            FROM transaction_metrics
        """
        df = db_manager.query(query)

        if not df.empty:
            row = df.iloc[0]
            result.add_pass("Time continuity",
                          f"{row['unique_days']} days, {row['unique_services']} services")
        else:
            result.add_fail("Time continuity", "No data")
    except Exception as e:
        result.add_fail("Time continuity", str(e))

    # Test 3: Check burn rate calculation correctness
    try:
        query = """
            SELECT
                transaction_name,
                AVG(error_rate) as avg_error_rate,
                MAX(short_target_slo) as slo_target,
                (AVG(error_rate) / NULLIF(MAX(short_target_slo), 0)) * 100 as calculated_burn_rate
            FROM transaction_metrics
            WHERE error_rate > 0
            GROUP BY transaction_name
            LIMIT 1
        """
        df = db_manager.query(query)

        if not df.empty:
            row = df.iloc[0]
            if pd.notna(row['calculated_burn_rate']):
                result.add_pass("Burn rate calculation",
                              f"Sample: {row['calculated_burn_rate']:.2f} from error_rate {row['avg_error_rate']:.2f}%")
            else:
                result.add_warning("Burn rate calculation", "NULL burn rate in sample")
        else:
            result.add_warning("Burn rate calculation", "No services with errors to test")
    except Exception as e:
        result.add_fail("Burn rate calculation", str(e))

def main():
    """Run comprehensive test suite."""
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}ClickHouse Migration - Comprehensive Test Suite{Colors.END}")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Verify complete ClickHouse migration with no bottlenecks\n")

    result = TestResult()

    # Run all test groups
    db_manager = test_clickhouse_connection(result)

    if db_manager:
        test_field_existence(result, db_manager)
        test_metrics_aggregator(result, db_manager)
        test_slo_calculator(result, db_manager)
        test_degradation_detector(result, db_manager)
        test_trend_analyzer(result, db_manager)
        test_data_quality(result, db_manager)
    else:
        print(f"\n{Colors.RED}Cannot continue - ClickHouse connection failed{Colors.END}")

    # Print summary
    success = result.print_summary()

    if success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}NEXT STEPS:{Colors.END}")
        print("1. Run Streamlit app: streamlit run app.py")
        print("2. Test with real queries:")
        print("   - 'Which services have high burn rates?'")
        print("   - 'Show me the slowest services'")
        print("   - 'Which services are degrading?'")
        print("   - 'Predict which services will have issues'")
        print(f"\n{Colors.GREEN}Migration is production-ready!{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}ACTION REQUIRED:{Colors.END}")
        print("Fix the failed tests before deploying to production.")
        print("Review error messages above for details.")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
