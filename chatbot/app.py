"""Streamlit web UI for SLO chatbot."""

import streamlit as st
from datetime import datetime

# Import our modules
from data.database.clickhouse_manager import ClickHouseManager
# Platform API ingestion removed - using ClickHouse from kafka_put pipeline
# from data.ingestion.data_loader import DataLoader
# from data.ingestion.keycloak_auth import KeycloakAuthManager
# from data.ingestion.platform_api_client import PlatformAPIClient
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator
from agent.claude_client import ClaudeClient
from agent.function_tools import FunctionExecutor, TOOLS
from utils.logger import setup_logger
from utils.config import DEFAULT_TIME_WINDOW_DAYS, MAX_TIME_WINDOW_DAYS

logger = setup_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="SLO Chatbot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_system():
    """Initialize all system components."""
    logger.info("Initializing SLO chatbot system")

    # Initialize ClickHouse database manager (read-only, data from kafka_put pipeline)
    from utils.config import CLICKHOUSE_HOST, CLICKHOUSE_PORT
    db_manager = ClickHouseManager(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)

    # Initialize analytics components
    slo_calculator = SLOCalculator(db_manager)
    degradation_detector = DegradationDetector(db_manager)
    trend_analyzer = TrendAnalyzer(db_manager)
    metrics_aggregator = MetricsAggregator(db_manager)

    # Initialize function executor
    function_executor = FunctionExecutor(
        slo_calculator=slo_calculator,
        degradation_detector=degradation_detector,
        trend_analyzer=trend_analyzer,
        metrics_aggregator=metrics_aggregator
    )

    # Initialize Claude client
    claude_client = ClaudeClient()

    logger.info("System initialization complete")

    return {
        'db_manager': db_manager,
        'slo_calculator': slo_calculator,
        'degradation_detector': degradation_detector,
        'trend_analyzer': trend_analyzer,
        'metrics_aggregator': metrics_aggregator,
        'function_executor': function_executor,
        'claude_client': claude_client
    }


# JSON file loading removed - data now only comes from OpenSearch
# def load_initial_data(data_loader):
#     """Load initial data from JSON files."""
#     service_logs_path = PROJECT_ROOT / "ServiceLogs7Amto11Am31Dec2025.json"
#     error_logs_path = PROJECT_ROOT / "ErrorLogs7Amto11Am31Dec2025.json"
#
#     if service_logs_path.exists() and error_logs_path.exists():
#         with st.spinner("Loading service and error logs..."):
#             data_loader.load_and_store_all(str(service_logs_path), str(error_logs_path))
#         st.success("Data loaded successfully!")
#         return True
#     else:
#         st.error("Log files not found!")
#         return False



def display_chat(components):
    """Display chat interface."""
    st.markdown("<h2>💬 SLO Assistant</h2>", unsafe_allow_html=True)

    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        # Also clear Claude's internal history when session starts
        components['claude_client'].clear_history()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # System prompt for Claude
    system_prompt = """You are a Conversational SLO & Reliability Analysis Assistant.

Your role is to analyze SLO metrics from ClickHouse and provide clear, actionable insights on service health, error budgets, and burn rates.

You operate ONLY on the data provided. Do not assume missing values.

DATA UNDERSTANDING:
The ClickHouse database contains **hourly transaction metrics** (12 days: Dec 31, 2025 - Jan 12, 2026) with 80+ fields per service including:

**Core Metrics:**
- transaction_name (service_name), total_count, error_count, error_rate, success_rate
- avg_response_time, percentile_25/50/75/80/85/90/95/99

**Multi-Tier SLO Tracking:**
- **Standard SLO** (98% target): short_target_slo, response_slo, response_target_percent
- **Aspirational SLO** (99% target): aspirational_slo, aspirational_response_target_percent

**Error Budget Metrics (Standard):**
- eb_allocated_percent, eb_consumed_percent, eb_actual_consumed_percent
- eb_left_percent, eb_left_count, eb_breached, eb_health (HEALTHY/UNHEALTHY)

**Error Budget Metrics (Aspirational):**
- aspirational_eb_allocated_percent, aspirational_eb_consumed_percent
- aspirational_eb_left_percent, aspirational_eb_health

**Response Budget Metrics:**
- response_allocated_percent, response_consumed_percent, response_left_percent
- response_breached, response_health, aspirational_response_health

**Advanced Indicators:**
- **burn_rate**: Calculated as (error_rate / short_target_slo) * 100 (>2.0 = high risk, >5.0 = critical)
- **timeliness_consumed_percent**: Batch job/scheduling performance
- **timeliness_health**: HEALTHY/UNHEALTHY status for timeliness
- **severity colors**: eb_severity, response_severity (#07AE86 = green, #FD346E = red)

**Time Windows:**
- Data is **hourly** (one data point per hour per service)
- Fixed 12-day dataset (Dec 31, 2025 - Jan 12, 2026)
- Compare weeks (7 days vs previous 7 days) for trend analysis

ANALYSIS RESPONSIBILITIES:

1) **Identify At-Risk Services**:
   - High burn rate (>2.0) = rapid error budget consumption
   - Budget exhaustion (eb_actual_consumed_percent >= 100%)
   - Aspirational SLO gap (meeting 98% but failing 99%)

2) **Multi-Dimensional Health Analysis**:
   - Error budget health (eb_health)
   - Response time health (response_health)
   - Aspirational health (aspirational_eb_health, aspirational_response_health)
   - Timeliness health (batch jobs, scheduled tasks)
   - Composite score (0-100 across all 5 dimensions)

3) **Breach vs Error Distinction**:
   - response_breached = latency SLO violations
   - error_rate = availability issues
   - These are independent! Use get_breach_vs_error_analysis() to diagnose

4) **Trend Detection**:
   - Hourly data enables precise trend analysis
   - Detect 7-day degradation patterns
   - Predict issues using historical patterns

AVAILABLE TOOLS:

**Standard Analysis:**
- get_service_health_overview() - System-wide health summary
- get_degrading_services(time_window_days) - Week-over-week degradation
- get_slo_violations() - Services currently violating SLO
- get_slowest_services(limit) - Ranked by P99 latency
- get_top_services_by_volume(limit) - High-traffic services
- get_service_summary(service_name) - Comprehensive single-service analysis
- get_current_sli(service_name) - Current service level indicators
- calculate_error_budget(service_name) - Error budget tracking
- predict_issues_today() - Predictions using historical patterns

**Advanced Functions:**
- get_services_by_burn_rate(limit) - Proactive SLO risk monitoring
- get_aspirational_slo_gap() - At-risk services (meeting 98%, failing 99%)
- get_timeliness_issues() - Batch job/scheduling problems
- get_breach_vs_error_analysis(service_name) - Latency vs reliability issues
- get_budget_exhausted_services() - Services over budget (>100%)
- get_composite_health_score() - Overall health (0-100) across 5 dimensions
- get_severity_heatmap() - Red vs green indicator visualization

**Performance Patterns:**
- get_volume_trends(service_name, time_window_days) - Traffic patterns
- get_historical_patterns(service_name) - Statistical analysis

**DEPRECATED (error_logs table not available in ClickHouse):**
- get_error_code_distribution() - Not available
- get_top_errors() - Not available
- get_error_details_by_code() - Not available

OUTPUT FORMAT (STRICT):

------------------------
SERVICE HEALTH SUMMARY
------------------------
Service Name:
Time Window: (e.g., "Last 7 days" or "Jan 1-7, 2025")

**Volume & Reliability:**
- Total Requests:
- Error Count:
- Error Rate:
- Success Rate:

**Latency (Percentiles):**
- P50 Response Time: (median)
- P95 Response Time: (95th percentile)
- P99 Response Time: (99th percentile - most critical)
- Avg Response Time: (for context)

------------------------
SLO COMPLIANCE
------------------------
**Standard SLO (98% target):**
- Availability SLO: 98%
- Observed Availability:
- Latency SLO: [target] sec
- Observed P99 Latency:
- Error Budget Left: X% (Y requests)
- EB Health: HEALTHY / UNHEALTHY
- Response Health: HEALTHY / UNHEALTHY

**Aspirational SLO (99% target):**
- Aspirational SLO: 99%
- Aspirational EB Left: X%
- Aspirational EB Health: HEALTHY / UNHEALTHY

**Risk Indicators:**
- Burn Rate: X.XX (>2.0 = high risk, >5.0 = critical)
- Budget Exhausted: Yes/No
- SLO Status: COMPLIANT / BREACHED / AT RISK / DEGRADING

------------------------
HEALTH DIMENSIONS
------------------------
1. Error Budget: HEALTHY / UNHEALTHY (severity: green/red)
2. Response Time: HEALTHY / UNHEALTHY
3. Timeliness: HEALTHY / UNHEALTHY
4. Aspirational EB: HEALTHY / UNHEALTHY
5. Aspirational Response: HEALTHY / UNHEALTHY

**Composite Health Score:** XX/100

------------------------
TRENDS & PATTERNS
------------------------
- Burn Rate Trend: (increasing/stable/decreasing)
- Week-over-Week Change: (error rate, latency, volume)
- Predicted Issues: (based on historical patterns)

------------------------
ACTIONABLE INSIGHTS
------------------------
- Key Observations:
- Root Cause Hypothesis: (data-driven, not hallucinated)
- Recommended Actions:

IMPORTANT BEHAVIOR RULES:
- **Prioritize P95/P99** over averages for latency analysis
- **Use burn rate** as primary early warning signal
- **Distinguish breach vs error**: response_breached (latency) vs error_rate (availability)
- **Multi-tier analysis**: Check both standard (98%) and aspirational (99%) SLOs
- **Time-aware**: Data is **hourly** with fixed 12-day window (Dec 31, 2025 - Jan 12, 2026)
- Keep responses concise and professional (bullet points, no emojis)
- Never hallucinate metrics - use only available data
- If data is insufficient, explicitly state limitations

DEFAULT TONE:
Professional SRE / Reliability Engineer
Clear, calm, data-driven
No emojis, no casual language

EXAMPLES OF GOOD ANALYSIS:

GOOD: "Service X has burn rate 3.5 (high risk). EB health is HEALTHY but 70% consumed. At this rate, budget will exhaust in 3 days."

BAD: "Service X looks fine, error rate is low" (WRONG - ignores burn rate!)

GOOD: "Service Y meets standard SLO (98%) but fails aspirational (99%). This is an at-risk service."

BAD: "Service Y is compliant" (WRONG - misses aspirational SLO gap!)

GOOD: "Service Z has response_breached=True but error_rate=0.5%. This is a latency issue, not an availability issue."

BAD: "Service Z has errors causing slow response" (WRONG - confuses breach with errors!)

"""

    # Chat input
    if prompt := st.chat_input("Ask about service health, SLOs, or degradation..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get Claude response with streaming
        with st.chat_message("assistant"):
            try:
                # Use streaming for real-time response generation
                response_placeholder = st.empty()
                full_response = ""

                for chunk in components['claude_client'].chat_stream(
                    user_message=prompt,
                    tools=TOOLS,
                    tool_executor=components['function_executor'],
                    system_prompt=system_prompt
                ):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")

                # Final update without cursor
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                logger.error(f"Chat error: {e}")


def main():
    """Main application."""
    # Title
    st.markdown("<div class='main-header'>📊 SLO Chatbot</div>", unsafe_allow_html=True)
    st.markdown("**AI-powered Service Level Objective monitoring and analysis**")

    # Initialize system
    components = initialize_system()

    # Sidebar
    with st.sidebar:
        st.markdown("## 🔧 Configuration")

        # Data source info
        st.markdown("### Data Source")
        st.info("📊 Data is loaded from ClickHouse (read-only)\n\n"
                "Source: kafka_put pipeline\n\n"
                "Granularity: Hourly metrics\n\n"
                "Fixed 12-day dataset")

        # Data info
        try:
            time_range = components['db_manager'].get_time_range()
            if time_range['min_time'] and time_range['max_time']:
                st.markdown("### 📅 Data Time Range")
                st.write(f"**From:** {time_range['min_time']}")
                st.write(f"**To:** {time_range['max_time']}")

            all_services = components['db_manager'].get_all_services()
            st.markdown(f"### 📊 Total Services: {len(all_services)}")

        except Exception as e:
            st.warning("No data loaded yet. Please load data first.")

        # Clear chat
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            components['claude_client'].clear_history()
            st.success("Chat history cleared!")

        # Sample questions
        st.markdown("### 💡 Sample Questions")
        st.markdown("""
        **Proactive Monitoring:**
        - Which services have high burn rates?
        - Show services with exhausted error budgets
        - Which services are at risk (meeting 98% but failing 99%)?
        - Predict which services will have issues today

        **Health Analysis:**
        - Show composite health scores for all services
        - Which services have timeliness issues?
        - Show the severity heatmap
        - Get service health overview

        **SLO Compliance:**
        - Show services violating their SLO
        - Calculate error budget for [service name]
        - What's the current SLI for [service name]?

        **Performance:**
        - What are the slowest services by P99 latency?
        - Show volume trends for [service name]
        - Which services are degrading over the past week?
        - Show historical patterns for [service name]
        """)

    # Main content - Chat interface
    display_chat(components)


if __name__ == "__main__":
    main()
