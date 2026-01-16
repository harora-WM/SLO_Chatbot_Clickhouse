"""Test script to verify SLO chatbot system."""

import sys
from pathlib import Path

# Import components
from data.database.duckdb_manager import DuckDBManager
from data.ingestion.data_loader import DataLoader
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator
from utils.logger import setup_logger
from utils.config import PROJECT_ROOT

logger = setup_logger(__name__)


def test_data_loading():
    """Test data loading from JSON files."""
    print("\n" + "="*60)
    print("TEST 1: Data Loading")
    print("="*60)

    try:
        # Initialize database
        db_manager = DuckDBManager()
        data_loader = DataLoader(db_manager)

        # Load data
        service_logs_path = PROJECT_ROOT / "ServiceLogs7Amto11Am31Dec2025.json"
        error_logs_path = PROJECT_ROOT / "ErrorLogs7Amto11Am31Dec2025.json"

        if not service_logs_path.exists():
            print(f"❌ Service logs not found at {service_logs_path}")
            return False

        if not error_logs_path.exists():
            print(f"❌ Error logs not found at {error_logs_path}")
            return False

        print(f"Loading data from:")
        print(f"  - {service_logs_path}")
        print(f"  - {error_logs_path}")

        data_loader.load_and_store_all(str(service_logs_path), str(error_logs_path))

        # Verify data
        time_range = db_manager.get_time_range()
        all_services = db_manager.get_all_services()

        print(f"\n✅ Data loaded successfully!")
        print(f"  - Time range: {time_range['min_time']} to {time_range['max_time']}")
        print(f"  - Total services: {len(all_services)}")

        return True

    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        logger.error(f"Data loading test failed: {e}", exc_info=True)
        return False


def test_slo_calculator():
    """Test SLO calculator."""
    print("\n" + "="*60)
    print("TEST 2: SLO Calculator")
    print("="*60)

    try:
        db_manager = DuckDBManager()
        slo_calculator = SLOCalculator(db_manager)

        # Get current SLI
        print("Getting current SLI for all services...")
        sli_df = slo_calculator.get_current_sli()

        print(f"\n✅ SLI retrieved for {len(sli_df)} services")
        print(f"\nTop 5 services by request volume:")
        print(sli_df.head()[['service_name', 'avg_success_rate', 'avg_error_rate', 'total_requests']])

        # Get SLO violations
        print("\nChecking SLO violations...")
        violations = slo_calculator.get_slo_violations()

        if violations:
            print(f"\n⚠️  Found {len(violations)} SLO violations:")
            for v in violations[:3]:
                print(f"  - {v['service_name']}: {', '.join(v['violations'])}")
        else:
            print("✅ No SLO violations found")

        return True

    except Exception as e:
        print(f"❌ SLO calculator test failed: {e}")
        logger.error(f"SLO calculator test failed: {e}", exc_info=True)
        return False


def test_degradation_detector():
    """Test degradation detector."""
    print("\n" + "="*60)
    print("TEST 3: Degradation Detector")
    print("="*60)

    try:
        db_manager = DuckDBManager()
        degradation_detector = DegradationDetector(db_manager)

        # Detect degrading services
        print("Detecting degrading services (30-min window)...")
        degrading = degradation_detector.detect_degrading_services(time_window_minutes=30)

        if degrading:
            print(f"\n⚠️  Found {len(degrading)} degrading services:")
            for service in degrading[:3]:
                print(f"  - {service['service_name']}")
                print(f"    Error rate change: {service['error_rate_change_percent']:.2f}%")
                print(f"    Response time change: {service['response_time_change_percent']:.2f}%")
                print(f"    Severity: {service['severity']}")
        else:
            print("✅ No degrading services detected")

        return True

    except Exception as e:
        print(f"❌ Degradation detector test failed: {e}")
        logger.error(f"Degradation detector test failed: {e}", exc_info=True)
        return False


def test_trend_analyzer():
    """Test trend analyzer."""
    print("\n" + "="*60)
    print("TEST 4: Trend Analyzer")
    print("="*60)

    try:
        db_manager = DuckDBManager()
        trend_analyzer = TrendAnalyzer(db_manager)

        # Predict issues
        print("Predicting services with potential issues...")
        predictions = trend_analyzer.predict_issues_today()

        if predictions:
            print(f"\n⚠️  Found {len(predictions)} services predicted to have issues:")
            for pred in predictions[:3]:
                print(f"  - {pred['service_name']}")
                print(f"    Risk level: {pred['risk_level']}")
                print(f"    Risk score: {pred['risk_score']}")
                print(f"    Risk factors: {len(pred['risk_factors'])}")
        else:
            print("✅ No predicted issues")

        return True

    except Exception as e:
        print(f"❌ Trend analyzer test failed: {e}")
        logger.error(f"Trend analyzer test failed: {e}", exc_info=True)
        return False


def test_metrics_aggregator():
    """Test metrics aggregator."""
    print("\n" + "="*60)
    print("TEST 5: Metrics Aggregator")
    print("="*60)

    try:
        db_manager = DuckDBManager()
        metrics_aggregator = MetricsAggregator(db_manager)

        # Get health overview
        print("Getting service health overview...")
        health = metrics_aggregator.get_service_health_overview()

        print(f"\n✅ Health Overview:")
        print(f"  - Total services: {health['total_services']}")
        print(f"  - Healthy: {health['healthy_services']}")
        print(f"  - Degraded: {health['degraded_services']}")
        print(f"  - Violated: {health['violated_services']}")
        print(f"  - Overall error rate: {health['overall_error_rate']:.2f}%")

        # Get top services
        print("\nTop 3 services by volume:")
        top_services = metrics_aggregator.get_top_services_by_volume(limit=3)
        for i, service in enumerate(top_services, 1):
            print(f"  {i}. {service['service_name']}: {service['total_requests']:,} requests")

        return True

    except Exception as e:
        print(f"❌ Metrics aggregator test failed: {e}")
        logger.error(f"Metrics aggregator test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SLO CHATBOT SYSTEM TEST")
    print("="*60)

    tests = [
        ("Data Loading", test_data_loading),
        ("SLO Calculator", test_slo_calculator),
        ("Degradation Detector", test_degradation_detector),
        ("Trend Analyzer", test_trend_analyzer),
        ("Metrics Aggregator", test_metrics_aggregator)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name} test crashed: {e}")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nTo start the chatbot, run:")
        print("  streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Please check the logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
