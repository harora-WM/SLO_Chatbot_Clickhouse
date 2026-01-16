"""Function tools for Claude to analyze SLO data."""

import json
from typing import Dict, List, Any
from analytics.slo_calculator import SLOCalculator
from analytics.degradation_detector import DegradationDetector
from analytics.trend_analyzer import TrendAnalyzer
from analytics.metrics import MetricsAggregator
from utils.logger import setup_logger

logger = setup_logger(__name__)


class FunctionExecutor:
    """Executor for analytics functions called by Claude."""

    def __init__(self,
                 slo_calculator: SLOCalculator,
                 degradation_detector: DegradationDetector,
                 trend_analyzer: TrendAnalyzer,
                 metrics_aggregator: MetricsAggregator):
        """Initialize function executor.

        Args:
            slo_calculator: SLO calculator instance
            degradation_detector: Degradation detector instance
            trend_analyzer: Trend analyzer instance
            metrics_aggregator: Metrics aggregator instance
        """
        self.slo_calculator = slo_calculator
        self.degradation_detector = degradation_detector
        self.trend_analyzer = trend_analyzer
        self.metrics_aggregator = metrics_aggregator

    def execute(self, function_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a function by name.

        Args:
            function_name: Name of the function to execute
            parameters: Function parameters

        Returns:
            Function result
        """
        function_map = {
            # Standard Performance & Health (6 functions)
            "get_degrading_services": self._get_degrading_services,
            "get_current_sli": self._get_current_sli,
            "get_slo_violations": self._get_slo_violations,
            "get_service_health_overview": self._get_service_health_overview,
            "get_top_services_by_volume": self._get_top_services_by_volume,
            "get_slowest_services": self._get_slowest_services,
            "get_error_prone_services": self._get_error_prone_services,

            # SLO & Budget Tracking (2 functions)
            "calculate_error_budget": self._calculate_error_budget,
            "get_service_summary": self._get_service_summary,

            # Trend Analysis (3 functions)
            "predict_issues_today": self._predict_issues_today,
            "get_volume_trends": self._get_volume_trends,
            "get_historical_patterns": self._get_historical_patterns,

            # NEW: Platform API Functions (8 functions)
            "get_services_by_burn_rate": self._get_services_by_burn_rate,
            "get_aspirational_slo_gap": self._get_aspirational_slo_gap,
            "get_timeliness_issues": self._get_timeliness_issues,
            "get_breach_vs_error_analysis": self._get_breach_vs_error_analysis,
            "get_budget_exhausted_services": self._get_budget_exhausted_services,
            "get_composite_health_score": self._get_composite_health_score,
            "get_severity_heatmap": self._get_severity_heatmap,
            "get_slo_governance_status": self._get_slo_governance_status,

            # Total: 20 functions
        }

        if function_name not in function_map:
            return {"error": f"Unknown function: {function_name}"}

        return function_map[function_name](**parameters)

    def _get_degrading_services(self, time_window_minutes: int = 30) -> Dict[str, Any]:
        """Get services degrading over time window."""
        result = self.degradation_detector.detect_degrading_services(time_window_minutes)
        return {"degrading_services": result, "count": len(result)}

    def _get_error_code_distribution(self,
                                    service_name: str = None,
                                    time_window_minutes: int = 30) -> Dict[str, Any]:
        """Get error code distribution."""
        return self.degradation_detector.get_error_code_distribution(service_name, time_window_minutes)

    def _get_current_sli(self, service_name: str = None) -> Dict[str, Any]:
        """Get current SLI for services."""
        df = self.slo_calculator.get_current_sli(service_name)
        return {"services": df.to_dict('records'), "count": len(df)}

    def _predict_issues_today(self) -> Dict[str, Any]:
        """Predict services with potential issues."""
        result = self.trend_analyzer.predict_issues_today()
        return {"predictions": result, "count": len(result)}

    def _get_service_summary(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive service summary."""
        return self.slo_calculator.get_service_summary(service_name)

    def _get_slo_violations(self) -> Dict[str, Any]:
        """Get all SLO violations."""
        result = self.slo_calculator.get_slo_violations()
        return {"violations": result, "count": len(result)}

    def _calculate_error_budget(self, service_name: str, time_window_hours: int = 4) -> Dict[str, Any]:
        """Calculate error budget for service."""
        return self.slo_calculator.calculate_error_budget(service_name, time_window_hours)

    def _get_volume_trends(self, service_name: str, time_window_minutes: int = 30) -> Dict[str, Any]:
        """Get volume trends for service."""
        return self.degradation_detector.get_volume_trends(service_name, time_window_minutes)

    def _get_service_health_overview(self) -> Dict[str, Any]:
        """Get overall service health overview."""
        return self.metrics_aggregator.get_service_health_overview()

    def _get_top_services_by_volume(self, limit: int = 10) -> Dict[str, Any]:
        """Get top services by volume."""
        result = self.metrics_aggregator.get_top_services_by_volume(limit)
        return {"services": result, "count": len(result)}

    def _get_slowest_services(self, limit: int = 10) -> Dict[str, Any]:
        """Get slowest services."""
        result = self.metrics_aggregator.get_slowest_services(limit)
        return {"services": result, "count": len(result)}

    def _get_error_prone_services(self, limit: int = 10) -> Dict[str, Any]:
        """Get error-prone services."""
        result = self.metrics_aggregator.get_error_prone_services(limit)
        return {"services": result, "count": len(result)}

    def _get_top_errors(self, limit: int = 10) -> Dict[str, Any]:
        """Get top error codes."""
        result = self.metrics_aggregator.get_top_errors(limit)
        return {"errors": result, "count": len(result)}

    def _get_error_details_by_code(self, error_code: str, limit: int = 5) -> Dict[str, Any]:
        """Get detailed error logs for a specific error code."""
        result = self.metrics_aggregator.get_error_details_by_code(error_code, limit)
        return {"error_code": error_code, "details": result, "count": len(result)}

    def _get_historical_patterns(self, service_name: str) -> Dict[str, Any]:
        """Get historical patterns for service."""
        return self.trend_analyzer.get_historical_patterns(service_name)

    # ==================== NEW PLATFORM API WRAPPER FUNCTIONS ====================

    def _get_services_by_burn_rate(self, limit: int = 10) -> Dict[str, Any]:
        """Get services with highest burn rates."""
        result = self.metrics_aggregator.get_services_by_burn_rate(limit)
        return {"services": result, "count": len(result)}

    def _get_aspirational_slo_gap(self) -> Dict[str, Any]:
        """Get services with aspirational SLO gaps (meeting 98% but failing 99%)."""
        result = self.metrics_aggregator.get_aspirational_slo_gap()
        return {"services": result, "count": len(result)}

    def _get_timeliness_issues(self) -> Dict[str, Any]:
        """Get services with timeliness/scheduling problems."""
        result = self.metrics_aggregator.get_timeliness_issues()
        return {"services": result, "count": len(result)}

    def _get_breach_vs_error_analysis(self, service_name: str = None) -> Dict[str, Any]:
        """Compare breach rate vs error rate to identify latency or reliability issues."""
        result = self.metrics_aggregator.get_breach_vs_error_analysis(service_name)
        return {"services": result, "count": len(result)}

    def _get_budget_exhausted_services(self) -> Dict[str, Any]:
        """Get services with exhausted error budgets (>=100% consumed)."""
        result = self.metrics_aggregator.get_budget_exhausted_services()
        return {"services": result, "count": len(result)}

    def _get_composite_health_score(self) -> Dict[str, Any]:
        """Get composite health scores across all dimensions (0-100)."""
        result = self.metrics_aggregator.get_composite_health_score()
        return {"services": result, "count": len(result)}

    def _get_severity_heatmap(self) -> Dict[str, Any]:
        """Get severity heatmap showing red vs green indicators per service."""
        result = self.metrics_aggregator.get_severity_heatmap()
        return {"services": result, "count": len(result)}

    def _get_slo_governance_status(self) -> Dict[str, Any]:
        """Get services with SLOs under review or not yet approved."""
        result = self.metrics_aggregator.get_slo_governance_status()
        return {"services": result, "count": len(result)}


# Tool definitions for Claude
TOOLS = [
    {
        "name": "get_degrading_services",
        "description": "Identify services that are degrading over a specified time window. Returns services with increasing error rates or response times compared to baseline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_window_minutes": {
                    "type": "integer",
                    "description": "Time window in minutes for degradation analysis (default: 30)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "get_error_code_distribution",
        "description": "Get distribution of error codes (HTTP status codes like 400, 500) for services. Shows which errors are most common.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Optional service name to filter by. If not provided, shows all services."
                },
                "time_window_minutes": {
                    "type": "integer",
                    "description": "Time window in minutes (default: 30)",
                    "default": 30
                }
            }
        }
    },
    {
        "name": "get_current_sli",
        "description": "Get current Service Level Indicators (SLI) including success rate, error rate, and response time for all services or a specific service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Optional service name to filter by"
                }
            }
        }
    },
    {
        "name": "predict_issues_today",
        "description": "Predict which services are expected to have issues today based on trend analysis, burn rates, and SLO proximity.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_service_summary",
        "description": "Get comprehensive summary for a specific service including SLI, SLO compliance, error budget, and burn rate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service to analyze"
                }
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "get_slo_violations",
        "description": "Get all services currently violating their SLO (either error rate or response time targets).",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "calculate_error_budget",
        "description": "Calculate error budget consumption for a service. Shows how much of the error budget has been used.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service"
                },
                "time_window_hours": {
                    "type": "integer",
                    "description": "Time window in hours (default: 4)",
                    "default": 4
                }
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "get_volume_trends",
        "description": "Get request volume trends and error patterns over time for a service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service"
                },
                "time_window_minutes": {
                    "type": "integer",
                    "description": "Time window in minutes (default: 30)",
                    "default": 30
                }
            },
            "required": ["service_name"]
        }
    },
    {
        "name": "get_service_health_overview",
        "description": "Get overall health overview of all services including healthy, degraded, and violated service counts.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_top_services_by_volume",
        "description": "Get top services ranked by request volume.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top services to return (default: 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_slowest_services",
        "description": "Get services with the highest response times.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of services to return (default: 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_error_prone_services",
        "description": "Get services with the highest error rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of services to return (default: 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_top_errors",
        "description": "Get most common error codes across all services.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of top errors to return (default: 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_error_details_by_code",
        "description": "Get detailed error logs for a specific error code. Returns full error details including transaction names, timestamps, and complete error log entries for debugging.",
        "input_schema": {
            "type": "object",
            "properties": {
                "error_code": {
                    "type": "string",
                    "description": "The error code to search for (e.g., '404', '500', '302')"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of error details to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["error_code"]
        }
    },
    {
        "name": "get_historical_patterns",
        "description": "Get historical patterns and statistics for a service including hourly patterns, percentiles, and trends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service"
                }
            },
            "required": ["service_name"]
        }
    },
    # ==================== NEW PLATFORM API TOOLS (8 functions) ====================
    {
        "name": "get_services_by_burn_rate",
        "description": "Get services with highest SLO burn rates. High burn rate (>2.0) indicates rapid error budget consumption and imminent SLO breach risk. Use this for proactive monitoring.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of services to return (default: 10)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "get_aspirational_slo_gap",
        "description": "Identify services meeting standard SLO (98%) but failing aspirational SLO (99%). These are 'at risk' services - one incident away from standard SLO breach. Use this to identify early warning signs.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_timeliness_issues",
        "description": "Find services with timeliness/scheduling problems (batch jobs not completing on time, etc.). Cross-correlates with response time to identify root cause - performance vs scheduling issues.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_breach_vs_error_analysis",
        "description": "Compare response SLA breach rate vs actual error rate to identify the root cause. High breach + Low error = Latency issues (slow but working). Low breach + High error = Reliability issues (fast but broken).",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Specific service name (optional). If not provided, analyzes all services."
                }
            }
        }
    },
    {
        "name": "get_budget_exhausted_services",
        "description": "Get services that have fully exhausted their error budget (>=100% consumed or negative remaining). These services are over budget and need immediate attention to avoid SLO violations.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_composite_health_score",
        "description": "Calculate overall health score (0-100) across all dimensions: error budget, response time, timeliness, aspirational error budget, and aspirational response health. Returns breakdown by dimension.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_severity_heatmap",
        "description": "Visual representation of severity across all dimensions. Counts red (#FD346E) vs green (#07AE86) health indicators per service to identify services with multiple unhealthy dimensions requiring urgent attention.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_slo_governance_status",
        "description": "Track services by SLO approval status. Identifies services with SLOs under review or not yet approved, helping prioritize SLO governance workflow and ensure all services have validated SLO targets.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]
