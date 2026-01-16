"""Configuration management for the SLO chatbot."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Helper function to get config values from Streamlit secrets or environment variables
def get_config(key: str, default: str = "") -> str:
    """Get configuration value from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        # Try Streamlit secrets first (for cloud deployment)
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, Exception):
        # Catch any Streamlit errors (including when secrets aren't configured)
        pass
    # Fall back to environment variables (for local development)
    return os.getenv(key, default)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

# Database configuration (DEPRECATED - using ClickHouse)
DUCKDB_PATH = DATABASE_DIR / "slo_analytics.duckdb"

# ClickHouse configuration
CLICKHOUSE_HOST = get_config("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(get_config("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = get_config("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = get_config("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_TABLE = "transaction_metrics"

# AWS Bedrock configuration
AWS_ACCESS_KEY_ID = get_config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_config("AWS_SECRET_ACCESS_KEY")
AWS_REGION = get_config("AWS_REGION", "ap-south-1")
BEDROCK_MODEL_ID = get_config("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0")

# OpenSearch configuration (DEPRECATED - kept for backwards compatibility)
OPENSEARCH_HOST = get_config("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(get_config("OPENSEARCH_PORT", "9200"))
OPENSEARCH_USERNAME = get_config("OPENSEARCH_USERNAME", "admin")
OPENSEARCH_PASSWORD = get_config("OPENSEARCH_PASSWORD", "")
OPENSEARCH_USE_SSL = get_config("OPENSEARCH_USE_SSL", "False").lower() == "true"
OPENSEARCH_INDEX_SERVICE = get_config("OPENSEARCH_INDEX_SERVICE", "hourly_wm_wmplatform_31854")
OPENSEARCH_INDEX_ERROR = get_config("OPENSEARCH_INDEX_ERROR", "hourly_wm_wmplatform_31854_error")

# Keycloak Authentication (for Platform API)
KEYCLOAK_URL = get_config(
    "KEYCLOAK_URL",
    "https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token"
)
KEYCLOAK_USERNAME = get_config("KEYCLOAK_USERNAME", "wmadmin")
KEYCLOAK_PASSWORD = get_config("KEYCLOAK_PASSWORD", "")
KEYCLOAK_CLIENT_ID = get_config("KEYCLOAK_CLIENT_ID", "web_app")
KEYCLOAK_TOKEN_REFRESH_INTERVAL = 240  # 4 minutes in seconds

# Platform API configuration
PLATFORM_API_URL = get_config(
    "PLATFORM_API_URL",
    "https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/v1/services/health"
)
PLATFORM_API_APPLICATION = get_config("PLATFORM_API_APPLICATION", "WMPlatform")
PLATFORM_API_PAGE_SIZE = int(get_config("PLATFORM_API_PAGE_SIZE", "200"))
PLATFORM_API_VERIFY_SSL = get_config("PLATFORM_API_VERIFY_SSL", "False").lower() == "true"

# SLO Thresholds (configurable)
DEFAULT_ERROR_SLO_THRESHOLD = 1.0  # 1% error rate
DEFAULT_RESPONSE_TIME_SLO = 1.0    # 1 second
DEFAULT_SLO_TARGET_PERCENT = 98    # 98% of requests must meet SLO
ASPIRATIONAL_SLO_TARGET_PERCENT = 99  # 99% aspirational target

# Analytics configuration
# Updated for daily data granularity (Platform API provides daily aggregations)
DEGRADATION_WINDOW_DAYS = 7  # Compare last 7 days vs previous 7 days (was 30 minutes for OpenSearch)
DEGRADATION_WINDOW_MINUTES = 30  # Kept for backwards compatibility with OpenSearch
DEGRADATION_THRESHOLD_PERCENT = 20  # 20% increase is considered degradation

# Time window configuration for ClickHouse (fixed 12-day dataset)
DEFAULT_TIME_WINDOW_DAYS = 12  # Fixed 12-day window in ClickHouse
MAX_TIME_WINDOW_DAYS = 12  # Limited by ClickHouse dataset (Dec 31, 2025 - Jan 12, 2026)

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
