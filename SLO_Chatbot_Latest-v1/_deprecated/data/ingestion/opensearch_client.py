"""OpenSearch client for real-time log ingestion."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from opensearchpy import OpenSearch
from utils.logger import setup_logger
from utils.config import (
    OPENSEARCH_HOST, OPENSEARCH_PORT, OPENSEARCH_USERNAME,
    OPENSEARCH_PASSWORD, OPENSEARCH_USE_SSL,
    OPENSEARCH_INDEX_SERVICE, OPENSEARCH_INDEX_ERROR
)
import pandas as pd

logger = setup_logger(__name__)


class OpenSearchClient:
    """Client for querying OpenSearch indices."""

    def __init__(self):
        """Initialize OpenSearch connection."""
        self.os_client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
            use_ssl=OPENSEARCH_USE_SSL
        )
        self.os_index_service = OPENSEARCH_INDEX_SERVICE
        self.os_index_error = OPENSEARCH_INDEX_ERROR

        logger.info(f"OpenSearch client initialized (host: {OPENSEARCH_HOST})")

    def query_service_logs(self,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          size: int = 1000,
                          use_scroll: bool = False) -> Dict[str, Any]:
        """Query service logs from OpenSearch.

        Args:
            start_time: Start time for query
            end_time: End time for query
            size: Maximum number of results per batch (max 10,000)
            use_scroll: Use scroll API for large datasets (>10k results)

        Returns:
            OpenSearch query results
        """
        # Validate size limit
        if size > 10000:
            logger.warning(f"Size {size} exceeds OpenSearch limit. Setting to 10,000")
            size = 10000

        # Build time range filter
        query = {
            "size": size,
            "query": {
                "match_all": {}
            },
            "sort": [
                {"record_time": {"order": "desc"}}
            ],
            # Request all fields explicitly for service logs
            "fields": [
                "service_name",
                "total_count",
                "success_count",
                "error_count",
                "na_error_count",
                "success_rate",
                "error_rate",
                "target_error_slo_perc",
                "target_response_slo_sec",
                "response_target_percent"
            ],
            "_source": True  # Also include _source
        }

        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = int(start_time.timestamp() * 1000)
            if end_time:
                time_range["lte"] = int(end_time.timestamp() * 1000)

            query["query"] = {
                "range": {
                    "record_time": time_range
                }
            }

        try:
            if use_scroll:
                # Use scroll API for large datasets
                return self._query_with_scroll(self.os_index_service, query)
            else:
                # Standard query (limited to 10k)
                response = self.os_client.search(
                    index=self.os_index_service,
                    body=query
                )
                logger.info(f"Retrieved {len(response['hits']['hits'])} service log entries")
                return response
        except Exception as e:
            logger.error(f"Failed to query service logs: {e}")
            raise

    def query_error_logs(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        size: int = 1000,
                        use_scroll: bool = False) -> Dict[str, Any]:
        """Query error logs from OpenSearch.

        Args:
            start_time: Start time for query
            end_time: End time for query
            size: Maximum number of results per batch (max 10,000)
            use_scroll: Use scroll API for large datasets (>10k results)

        Returns:
            OpenSearch query results
        """
        # Validate size limit
        if size > 10000:
            logger.warning(f"Size {size} exceeds OpenSearch limit. Setting to 10,000")
            size = 10000

        # Build time range filter
        query = {
            "size": size,
            "query": {
                "match_all": {}
            },
            "sort": [
                {"record_time": {"order": "desc"}}
            ],
            # Request all fields explicitly for error logs
            "fields": [
                "summary",
                "error_details",
                "technical_error_count",
                "business_error_count"
            ],
            "_source": True  # Also include _source
        }

        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = int(start_time.timestamp() * 1000)
            if end_time:
                time_range["lte"] = int(end_time.timestamp() * 1000)

            query["query"] = {
                "range": {
                    "record_time": time_range
                }
            }

        try:
            if use_scroll:
                # Use scroll API for large datasets
                return self._query_with_scroll(self.os_index_error, query)
            else:
                # Standard query (limited to 10k)
                response = self.os_client.search(
                    index=self.os_index_error,
                    body=query
                )
                logger.info(f"Retrieved {len(response['hits']['hits'])} error log entries")
                return response
        except Exception as e:
            logger.error(f"Failed to query error logs: {e}")
            raise

    def get_latest_logs(self, hours: int = 4) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Get latest logs from the past N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            Tuple of (service_logs, error_logs)
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        logger.info(f"Fetching logs from {start_time} to {end_time}")

        service_logs = self.query_service_logs(start_time, end_time)
        error_logs = self.query_error_logs(start_time, end_time)

        return service_logs, error_logs

    def stream_latest_logs(self, from_data_loader: Any):
        """Stream latest logs and load into database.

        Args:
            from_data_loader: DataLoader instance for parsing and storing

        Returns:
            Summary of loaded data
        """
        try:
            # Get latest logs (past 4 hours)
            service_logs, error_logs = self.get_latest_logs(hours=4)

            # Save to temporary JSON files
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='_service.json', delete=False) as f:
                json.dump(service_logs, f)
                service_temp_path = f.name

            with tempfile.NamedTemporaryFile(mode='w', suffix='_error.json', delete=False) as f:
                json.dump(error_logs, f)
                error_temp_path = f.name

            try:
                # Load into database
                from_data_loader.load_and_store_all(service_temp_path, error_temp_path)

                logger.info("Successfully streamed and loaded latest logs")

                return {
                    'service_logs_count': len(service_logs.get('hits', {}).get('hits', [])),
                    'error_logs_count': len(error_logs.get('hits', {}).get('hits', [])),
                    'status': 'success'
                }
            finally:
                # Clean up temp files
                os.unlink(service_temp_path)
                os.unlink(error_temp_path)

        except Exception as e:
            logger.error(f"Failed to stream logs: {e}")
            raise

    def _query_with_scroll(self, index: str, query: Dict[str, Any], batch_size: int = 1000) -> Dict[str, Any]:
        """Query OpenSearch using scroll API for large datasets.

        Args:
            index: Index name
            query: Query body
            batch_size: Number of results per batch

        Returns:
            Combined results from all scroll batches
        """
        logger.info(f"Using scroll API for index {index}")

        # Initial search with scroll
        query['size'] = batch_size
        response = self.os_client.search(
            index=index,
            body=query,
            scroll='2m'  # Keep scroll context for 2 minutes
        )

        scroll_id = response['_scroll_id']
        all_hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']

        logger.info(f"Total hits to retrieve: {total_hits}")

        # Continue scrolling until no more results
        while len(all_hits) < total_hits:
            try:
                response = self.os_client.scroll(
                    scroll_id=scroll_id,
                    scroll='2m'
                )

                # Break if no more hits
                if not response['hits']['hits']:
                    break

                all_hits.extend(response['hits']['hits'])
                scroll_id = response['_scroll_id']

                logger.info(f"Retrieved {len(all_hits)}/{total_hits} hits")

            except Exception as e:
                logger.error(f"Scroll failed: {e}")
                break

        # Clear scroll context
        try:
            self.os_client.clear_scroll(scroll_id=scroll_id)
        except:
            pass

        logger.info(f"Scroll complete: Retrieved {len(all_hits)} total hits")

        # Return in same format as regular search
        return {
            'hits': {
                'total': {'value': len(all_hits)},
                'hits': all_hits
            }
        }

    def test_connection(self) -> bool:
        """Test OpenSearch connection.

        Returns:
            True if connection is successful
        """
        try:
            info = self.os_client.info()
            logger.info(f"OpenSearch connection successful: {info['version']['number']}")
            return True
        except Exception as e:
            logger.error(f"OpenSearch connection failed: {e}")
            return False
