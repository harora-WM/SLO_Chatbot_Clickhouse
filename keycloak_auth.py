"""
Script to get access token from Keycloak authentication endpoint.
Bypasses SSL verification using the -k flag equivalent (verify=False).
"""
import requests
import json
from typing import Optional, Dict, Any


def get_access_token(
    username: str,
    password: str,
    keycloak_url: str = "https://wm-sandbox-auth-1.watermelon.us/realms/watermelon/protocol/openid-connect/token",
    client_id: str = "web_app"
) -> Optional[str]:
    """
    Get access token from Keycloak authentication endpoint.

    Args:
        username: Keycloak username
        password: Keycloak password
        keycloak_url: Keycloak token endpoint URL
        client_id: OAuth2 client ID

    Returns:
        Access token string if successful, None otherwise
    """
    # Prepare the request data
    data = {
        'grant_type': 'password',
        'client_id': client_id,
        'username': username,
        'password': password
    }

    # Headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # Make POST request with SSL verification disabled (equivalent to curl -k flag)
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        response = requests.post(
            keycloak_url,
            data=data,
            headers=headers,
            verify=False  # This is equivalent to curl's -k flag
        )

        # Check if request was successful
        response.raise_for_status()

        # Parse JSON response
        response_data = response.json()

        # Extract access token
        access_token = response_data.get('access_token')

        if access_token:
            print("✓ Successfully obtained access token")
            return access_token
        else:
            print("✗ No access_token found in response")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse JSON response: {e}")
        print(f"Response text: {response.text}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


if __name__ == "__main__":
    print("Keycloak Token Retrieval Script")
    print("=" * 50)

    # Hardcoded credentials
    username = "wmadmin"
    password = "WM@Dm1n@#2024!!$"

    # Get access token
    print("\n--- Getting Access Token ---")
    token = get_access_token(username, password)

    if token:
        print(f"\nAccess Token (first 100 chars): {token[:100]}...")
        print(f"\nToken length: {len(token)} characters")

        # Now test the service health API
        print("\n" + "=" * 50)
        print("--- Testing Service Health API ---")

        health_url = "https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/transactions/summary/series/all"
        params = {
            'application_id': '31854',
            'range': 'CUSTOM',
            'start_time': '1767205800000',
            'end_time': '1768242540000',
            'index': 'HOURLY'
        }
        headers = {
            'Authorization': f'Bearer {token}'
        }

        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            health_response = requests.get(
                health_url,
                params=params,
                headers=headers,
                verify=False
            )

            health_response.raise_for_status()
            health_data = health_response.json()

            print("✓ Successfully retrieved service health data")

            # Save response to JSON file
            output_file = "service_health_response.json"
            with open(output_file, 'w') as f:
                json.dump(health_data, f, indent=2)

            print(f"✓ Response saved to {output_file}")
            print(f"\nFull Response:")
            print(json.dumps(health_data, indent=2))

        except Exception as e:
            print(f"✗ Service health API failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text[:500]}")
    else:
        print("\n✗ Failed to obtain access token. Cannot test service health API.")
