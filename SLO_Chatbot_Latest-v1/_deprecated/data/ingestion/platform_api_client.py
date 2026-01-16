"""
Platform API client for fetching service health data.

This module handles communication with the WM Platform Error Budget Statistics Service,
including pagination to fetch all services regardless of count.
"""

import requests
import urllib3
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger
from utils.config import (
    PLATFORM_API_URL,
    PLATFORM_API_APPLICATION,
    PLATFORM_API_PAGE_SIZE,
    PLATFORM_API_VERIFY_SSL
)

# Disable SSL warnings since we use verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger(__name__)


class PlatformAPIClient:
    """
    Client for interacting with the Platform Error Budget Statistics API.

    Handles pagination automatically to fetch all services, regardless of count.
    Uses Keycloak authentication for API access.
    """

    def __init__(self, auth_manager):
        """
        Initialize the Platform API client.

        Args:
            auth_manager: KeycloakAuthManager instance for authentication
        """
        self.auth_manager = auth_manager
        self.base_url = PLATFORM_API_URL
        self.application = PLATFORM_API_APPLICATION
        self.page_size = PLATFORM_API_PAGE_SIZE
        self.verify_ssl = PLATFORM_API_VERIFY_SSL

        logger.info(f"PlatformAPIClient initialized | URL: {self.base_url}")

    def query_service_health(
        self,
        start_time: int,
        end_time: int,
        application: Optional[str] = None,
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all service health data with automatic pagination.

        Args:
            start_time: Start timestamp in epoch milliseconds
            end_time: End timestamp in epoch milliseconds
            application: Application name (default: from config)
            page_size: Results per page (default: from config, typically 200)

        Returns:
            List of service health records (dicts)

        Raises:
            Exception: If API request fails
        """
        application = application or self.application
        page_size = page_size or self.page_size

        logger.info(f"Fetching service health data | "
                   f"Time: {start_time} to {end_time} | "
                   f"App: {application}")

        all_data = []
        page_id = 0

        while True:
            try:
                page_data = self._fetch_page(
                    start_time=start_time,
                    end_time=end_time,
                    application=application,
                    page_id=page_id,
                    page_size=page_size
                )

                # Check if we got data
                if not page_data or len(page_data) == 0:
                    logger.info(f"No more data at page {page_id}, stopping pagination")
                    break

                # Check if response indicates no data
                if isinstance(page_data, list) and len(page_data) == 1:
                    if page_data[0].get('noDataFound') == True:
                        logger.info(f"API returned noDataFound at page {page_id}")
                        break

                all_data.extend(page_data)
                logger.info(f"Page {page_id}: Fetched {len(page_data)} services | "
                           f"Total: {len(all_data)}")

                # If we got less than page_size, we've reached the end
                if len(page_data) < page_size:
                    logger.info(f"Received {len(page_data)} < {page_size}, last page reached")
                    break

                page_id += 1

            except Exception as e:
                logger.error(f"Error fetching page {page_id}: {e}")
                # If we already have some data, return it
                if all_data:
                    logger.warning(f"Returning partial data ({len(all_data)} services) due to error")
                    return all_data
                # Otherwise, raise the error
                raise

        logger.info(f"✓ Successfully fetched {len(all_data)} total service records across {page_id + 1} pages")
        return all_data

    def _fetch_page(
        self,
        start_time: int,
        end_time: int,
        application: str,
        page_id: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch a single page of service health data.

        Args:
            start_time: Start timestamp in epoch milliseconds
            end_time: End timestamp in epoch milliseconds
            application: Application name
            page_id: Page number (0-indexed)
            page_size: Results per page

        Returns:
            List of service health records for this page

        Raises:
            Exception: If API request fails
        """
        # Get fresh access token
        try:
            access_token = self.auth_manager.get_access_token()
        except Exception as e:
            raise Exception(f"Failed to get access token: {e}")

        # Prepare request
        params = {
            'start_time': start_time,
            'end_time': end_time,
            'application': application,
            'page_id': page_id,
            'page_size': page_size
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }

        logger.debug(f"GET {self.base_url} | Page: {page_id} | Params: {params}")

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=headers,
                verify=self.verify_ssl,
                timeout=60  # 60 second timeout
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Handle different response formats
            if isinstance(data, dict):
                # Check if response has 'summary' array (Platform API format)
                if 'summary' in data and isinstance(data['summary'], list):
                    logger.debug(f"Extracting {len(data['summary'])} services from 'summary' array")
                    return data['summary']
                # Otherwise, wrap single dict in list (legacy format)
                else:
                    logger.debug("Wrapping single dict response in list")
                    return [data]
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected response type: {type(data)}")
                return []

        except requests.exceptions.Timeout as e:
            raise Exception(f"Request timeout after 60s: {e}")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {response.status_code}: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Response: {e.response.text[:500]}"
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {e} | Response text: {response.text[:500]}")

    def query_service_health_simple(
        self,
        start_time: int,
        end_time: int,
        application: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch service health data without pagination (single request).

        Useful for testing or when you know data fits in one page.

        Args:
            start_time: Start timestamp in epoch milliseconds
            end_time: End timestamp in epoch milliseconds
            application: Application name (default: from config)

        Returns:
            Raw API response (dict or list)

        Raises:
            Exception: If API request fails
        """
        application = application or self.application

        logger.info(f"Fetching service health (simple) | "
                   f"Time: {start_time} to {end_time} | "
                   f"App: {application}")

        try:
            data = self._fetch_page(
                start_time=start_time,
                end_time=end_time,
                application=application,
                page_id=0,
                page_size=self.page_size
            )

            logger.info(f"✓ Fetched {len(data) if isinstance(data, list) else 1} service records")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch service health: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test API connection with a minimal query.

        Returns:
            bool: True if connection successful

        Raises:
            Exception: If connection test fails
        """
        logger.info("Testing Platform API connection...")

        try:
            # Query last 1 hour of data
            from datetime import datetime, timedelta
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(hours=1)).timestamp() * 1000)

            data = self.query_service_health_simple(start_time, end_time)

            logger.info(f"✓ Platform API connection test successful | "
                       f"Retrieved {len(data) if isinstance(data, list) else 1} records")
            return True

        except Exception as e:
            logger.error(f"✗ Platform API connection test failed: {e}")
            raise
