"""Test script to verify ClickHouse migration."""

import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '/home/hardik121/kafka_put/SLO_Chatbot_Latest-v1')

from data.database.clickhouse_manager import ClickHouseManager
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator

def print_section(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_clickhouse_connection():
    """Test ClickHouse connection."""
    print_section("1. Testing ClickHouse Connection")
    try:
        db_manager = ClickHouseManager(host='localhost', port=8123)

        # Test basic query
        time_range = db_manager.get_time_range()
        print(f"✅ Connected to ClickHouse")
        print(f"   Time range: {time_range['min_time']} → {time_range['max_time']}")

        # Test service count
        services = db_manager.get_all_services()
        print(f"   Total services: {len(services)}")

        return db_manager
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return None

def test_analytics_modules(db_manager):
    """Test all analytics modules."""
    print_section("2. Testing Analytics Modules")

    # Initialize modules
    slo_calculator = SLOCalculator(db_manager)
    degradation_detector = DegradationDetector(db_manager)
    trend_analyzer = TrendAnalyzer(db_manager)
    metrics_aggregator = MetricsAggregator(db_manager)

    print("\n📊 MetricsAggregator Tests:")

    # Test health overview
    try:
        overview = metrics_aggregator.get_service_health_overview()
        print(f"   ✅ get_service_health_overview(): {overview['total_services']} services, {overview['healthy_services']} healthy")
    except Exception as e:
        print(f"   ❌ get_service_health_overview() failed: {e}")

    # Test slowest services
    try:
        slowest = metrics_aggregator.get_slowest_services(limit=3)
        print(f"   ✅ get_slowest_services(): Found {len(slowest)} services")
        if slowest:
            print(f"      Slowest: {slowest[0]['service_name']} ({slowest[0]['avg_response_time_p99']:.4f}s P99)")
    except Exception as e:
        print(f"   ❌ get_slowest_services() failed: {e}")

    # Test top services by volume
    try:
        top_volume = metrics_aggregator.get_top_services_by_volume(limit=3)
        print(f"   ✅ get_top_services_by_volume(): Found {len(top_volume)} services")
        if top_volume:
            print(f"      Highest: {top_volume[0]['service_name']} ({top_volume[0]['total_requests']:,} requests)")
    except Exception as e:
        print(f"   ❌ get_top_services_by_volume() failed: {e}")

    # Test services by burn rate
    try:
        burn_rate_services = metrics_aggregator.get_services_by_burn_rate(limit=5)
        print(f"   ✅ get_services_by_burn_rate(): Found {len(burn_rate_services)} services")
        if burn_rate_services:
            print(f"      Highest: {burn_rate_services[0]['service_name']} (burn rate: {burn_rate_services[0]['avg_burn_rate']:.2f})")
    except Exception as e:
        print(f"   ❌ get_services_by_burn_rate() failed: {e}")

    print("\n📈 SLOCalculator Tests:")

    # Get a test service
    services = db_manager.get_all_services()
    test_service = services[0] if services else None

    if test_service:
        # Test current SLI
        try:
            sli = slo_calculator.get_current_sli(test_service)
            print(f"   ✅ get_current_sli('{test_service}'): Error rate {sli['current_error_rate']:.2f}%")
        except Exception as e:
            print(f"   ❌ get_current_sli() failed: {e}")

        # Test error budget
        try:
            budget = slo_calculator.calculate_error_budget(test_service)
            print(f"   ✅ calculate_error_budget('{test_service}'): {budget['budget_remaining_percent']:.2f}% remaining")
        except Exception as e:
            print(f"   ❌ calculate_error_budget() failed: {e}")

        # Test SLO violations
        try:
            violations = slo_calculator.get_slo_violations()
            print(f"   ✅ get_slo_violations(): Found {len(violations)} violations")
        except Exception as e:
            print(f"   ❌ get_slo_violations() failed: {e}")

    print("\n🔍 DegradationDetector Tests:")

    # Test degrading services
    try:
        degrading = degradation_detector.detect_degrading_services(time_window_days=7)
        print(f"   ✅ detect_degrading_services(): Found {len(degrading)} degrading services")
        if degrading:
            print(f"      Top: {degrading[0]['service_name']} (error rate change: {degrading[0]['error_rate_change_percent']:.1f}%)")
    except Exception as e:
        print(f"   ❌ detect_degrading_services() failed: {e}")

    # Test volume trends
    if test_service:
        try:
            trends = degradation_detector.get_volume_trends(test_service, time_window_days=7)
            print(f"   ✅ get_volume_trends('{test_service}'): {trends['summary']['total_volume']:,} total requests")
        except Exception as e:
            print(f"   ❌ get_volume_trends() failed: {e}")

    print("\n🎯 TrendAnalyzer Tests:")

    # Test predictions
    try:
        predictions = trend_analyzer.predict_issues_today()
        print(f"   ✅ predict_issues_today(): Found {len(predictions)} at-risk services")
        if predictions:
            print(f"      Top risk: {predictions[0]['service_name']} (risk level: {predictions[0]['risk_level']})")
    except Exception as e:
        print(f"   ❌ predict_issues_today() failed: {e}")

    # Test historical patterns
    if test_service:
        try:
            patterns = trend_analyzer.get_historical_patterns(test_service)
            print(f"   ✅ get_historical_patterns('{test_service}'): {patterns['data_points']} data points")
        except Exception as e:
            print(f"   ❌ get_historical_patterns() failed: {e}")

def test_field_mappings(db_manager):
    """Test that field mappings work correctly."""
    print_section("3. Testing Field Mappings")

    # Query ClickHouse directly
    query = """
        SELECT
            transaction_name,
            avg_response_time,
            error_rate,
            short_target_slo,
            percentile_95,
            percentile_99
        FROM transaction_metrics
        LIMIT 1
    """

    try:
        df = db_manager.query(query)
        print("✅ Field mapping test:")
        print(f"   - transaction_name → service_name: {'service_name' in df.columns}")
        print(f"   - avg_response_time exists: {'avg_response_time' in df.columns}")
        print(f"   - error_rate exists: {'error_rate' in df.columns}")
        print(f"   - short_target_slo exists: {'short_target_slo' in df.columns}")
        print(f"   - percentile_95 exists: {'percentile_95' in df.columns}")
        print(f"   - percentile_99 exists: {'percentile_99' in df.columns}")

        if not df.empty:
            print(f"\n   Sample service: {df['service_name'].iloc[0]}")
            print(f"   Avg response time: {df['avg_response_time'].iloc[0]:.4f}s")
            print(f"   Error rate: {df['error_rate'].iloc[0]:.2f}%")
            print(f"   SLO target: {df['short_target_slo'].iloc[0]:.0f}%")
    except Exception as e:
        print(f"❌ Field mapping test failed: {e}")

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  ClickHouse Migration Test Suite")
    print("=" * 80)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test connection
    db_manager = test_clickhouse_connection()
    if not db_manager:
        print("\n❌ Cannot continue without ClickHouse connection")
        return

    # Test analytics
    test_analytics_modules(db_manager)

    # Test field mappings
    test_field_mappings(db_manager)

    print_section("Summary")
    print("✅ Migration test completed!")
    print("\nNext steps:")
    print("1. Run the Streamlit app: streamlit run app.py")
    print("2. Try asking questions like:")
    print("   - 'Which services have high burn rates?'")
    print("   - 'Show me the slowest services by P99 latency'")
    print("   - 'Which services are degrading?'")
    print("   - 'Predict which services will have issues'")

if __name__ == "__main__":
    main()
