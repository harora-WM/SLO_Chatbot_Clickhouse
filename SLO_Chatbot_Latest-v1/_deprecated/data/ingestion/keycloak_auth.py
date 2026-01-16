"""
Keycloak authentication manager with automatic token refresh.

This module handles OAuth2 authentication with Keycloak, automatically refreshing
the access token every 4 minutes in a background thread to ensure continuous API access.
"""

import requests
import threading
import time
import urllib3
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import setup_logger
from utils.config import (
    KEYCLOAK_URL,
    KEYCLOAK_USERNAME,
    KEYCLOAK_PASSWORD,
    KEYCLOAK_CLIENT_ID
)

# Disable SSL warnings since we use verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = setup_logger(__name__)


class KeycloakAuthManager:
    """
    Manages Keycloak authentication with automatic token refresh.

    The access token is refreshed every 4 minutes in a background thread
    to ensure it never expires during API operations.
    """

    def __init__(self):
        """Initialize the auth manager and start background refresh thread."""
        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.refresh_interval = 240  # 4 minutes in seconds
        self._stop_refresh = threading.Event()
        self._lock = threading.Lock()

        # Get initial token
        self._fetch_new_token()

        # Start background refresh thread
        self._start_refresh_thread()

        logger.info("KeycloakAuthManager initialized with auto-refresh enabled")

    def get_access_token(self) -> str:
        """
        Get a valid access token.

        Returns the cached token if valid, otherwise fetches a new one.

        Returns:
            str: Valid access token

        Raises:
            Exception: If token fetch fails
        """
        with self._lock:
            if self._is_token_valid():
                return self.token

            # Token expired or invalid, fetch new one
            return self._fetch_new_token()

    def _is_token_valid(self) -> bool:
        """
        Check if current token is valid.

        Returns:
            bool: True if token exists and hasn't expired
        """
        if self.token is None or self.token_expiry is None:
            return False

        # Consider token invalid if expiring within 30 seconds
        return datetime.now() < (self.token_expiry - timedelta(seconds=30))

    def _fetch_new_token(self) -> str:
        """
        Fetch a new access token from Keycloak.

        Returns:
            str: New access token

        Raises:
            Exception: If token fetch fails
        """
        try:
            data = {
                'grant_type': 'password',
                'client_id': KEYCLOAK_CLIENT_ID,
                'username': KEYCLOAK_USERNAME,
                'password': KEYCLOAK_PASSWORD
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            logger.info(f"Fetching new access token from Keycloak...")

            response = requests.post(
                KEYCLOAK_URL,
                data=data,
                headers=headers,
                verify=False,  # Bypass SSL verification
                timeout=30
            )

            response.raise_for_status()
            response_data = response.json()

            # Extract token and expiry
            access_token = response_data.get('access_token')
            expires_in = response_data.get('expires_in', 300)  # Default 5 minutes

            if not access_token:
                raise Exception("No access_token in Keycloak response")

            self.token = access_token
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"✓ Successfully obtained access token (expires in {expires_in}s)")
            logger.debug(f"Token: {access_token[:50]}...")

            return access_token

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch Keycloak token: {e}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" | Status: {e.response.status_code} | Response: {e.response.text[:200]}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error fetching token: {e}")
            raise

    def _refresh_token_loop(self):
        """
        Background thread that refreshes the token every 4 minutes.

        This ensures the token never expires during API operations.
        """
        logger.info("Token refresh loop started (refreshes every 4 minutes)")

        while not self._stop_refresh.is_set():
            # Wait for 4 minutes or until stop signal
            if self._stop_refresh.wait(timeout=self.refresh_interval):
                break  # Stop signal received

            try:
                with self._lock:
                    self._fetch_new_token()
                logger.info("Background token refresh completed")
            except Exception as e:
                logger.error(f"Background token refresh failed: {e}")
                # Continue loop even if refresh fails - will retry in 4 minutes

        logger.info("Token refresh loop stopped")

    def _start_refresh_thread(self):
        """Start the background token refresh thread."""
        self.refresh_thread = threading.Thread(
            target=self._refresh_token_loop,
            daemon=True,  # Thread dies when main program exits
            name="KeycloakTokenRefresh"
        )
        self.refresh_thread.start()
        logger.info("Background token refresh thread started")

    def stop_refresh(self):
        """
        Stop the background refresh thread.

        Call this when shutting down the application.
        """
        logger.info("Stopping token refresh thread...")
        self._stop_refresh.set()
        if hasattr(self, 'refresh_thread'):
            self.refresh_thread.join(timeout=5)
        logger.info("Token refresh thread stopped")

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.stop_refresh()
        except:
            pass  # Ignore errors during cleanup
