"""
Kafka Producer to fetch data from API and send each record to Kafka topic.
Fetches hourly transaction summary data and publishes each hour's data as individual messages.
"""
import json
import requests
import urllib3
from kafka import KafkaProducer
from typing import Optional, Dict, Any, List
from keycloak_auth import get_access_token


def create_kafka_producer(bootstrap_servers: List[str]) -> KafkaProducer:
    """
    Create and configure Kafka producer.

    Args:
        bootstrap_servers: List of Kafka broker addresses

    Returns:
        Configured KafkaProducer instance
    """
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None,
        acks='all',  # Wait for all replicas to acknowledge
        retries=3,
        max_in_flight_requests_per_connection=1
    )
    return producer


def fetch_api_data(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from the service health API.

    Args:
        access_token: Bearer token for authentication

    Returns:
        API response as dictionary, None if failed
    """
    api_url = "https://wm-sandbox-1.watermelon.us/services/wmerrorbudgetstatisticsservice/api/transactions/summary/series/all"
    params = {
        'application_id': '31854',
        'range': 'CUSTOM',
        'start_time': '1767205800000',
        'end_time': '1768242540000',
        'index': 'HOURLY'
    }
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    try:
        # Suppress SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        print(f"Fetching data from API...")
        print(f"URL: {api_url}")
        print(f"Params: {params}")

        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            verify=False
        )

        response.raise_for_status()
        data = response.json()

        print(f"✓ Successfully fetched data from API")
        return data

    except Exception as e:
        print(f"✗ Failed to fetch data from API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text[:500]}")
        return None


def send_to_kafka(producer: KafkaProducer, topic: str, data: Dict[str, Any]) -> int:
    """
    Parse API response and send each record to Kafka topic.

    Args:
        producer: KafkaProducer instance
        topic: Kafka topic name
        data: API response data

    Returns:
        Number of messages sent successfully
    """
    messages_sent = 0

    # Extract records from response (adjust based on actual response structure)
    # Common structures: data['data'], data['records'], data['series'], etc.
    records = None

    # Try common response structures
    if 'data' in data:
        records = data['data']
    elif 'records' in data:
        records = data['records']
    elif 'series' in data:
        records = data['series']
    elif isinstance(data, list):
        records = data
    else:
        # If structure is unknown, save the whole response for inspection
        print("⚠ Unknown response structure. Available keys:", list(data.keys()))
        print("Sending entire response as single message for inspection...")
        records = [data]

    if not records:
        print("✗ No records found in API response")
        return 0

    print(f"\nFound {len(records)} records to send to Kafka")
    print(f"Sending to topic: {topic}")

    # Send each record as individual Kafka message
    for idx, record in enumerate(records):
        try:
            # Use timestamp as key if available
            key = None
            if isinstance(record, dict):
                if 'timestamp' in record:
                    key = str(record['timestamp'])
                elif 'time' in record:
                    key = str(record['time'])

            # Send message to Kafka
            future = producer.send(topic, key=key, value=record)

            # Wait for message to be sent (optional, for reliability)
            record_metadata = future.get(timeout=10)

            messages_sent += 1

            if (idx + 1) % 50 == 0:  # Progress update every 50 messages
                print(f"  Sent {idx + 1}/{len(records)} messages...")

        except Exception as e:
            print(f"✗ Failed to send record {idx}: {e}")
            continue

    # Flush remaining messages
    producer.flush()

    print(f"\n✓ Successfully sent {messages_sent}/{len(records)} messages to Kafka")
    return messages_sent


def main():
    """Main execution flow."""
    print("=" * 70)
    print("Kafka Producer - API to Kafka Data Pipeline")
    print("=" * 70)

    # Configuration
    KAFKA_BOOTSTRAP_SERVERS = ['ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092']
    KAFKA_TOPIC = 'services_series_12days'

    # Keycloak credentials
    KEYCLOAK_USERNAME = "wmadmin"
    KEYCLOAK_PASSWORD = "WM@Dm1n@#2024!!$"

    # Step 1: Get access token
    print("\n[Step 1/4] Getting access token from Keycloak...")
    access_token = get_access_token(KEYCLOAK_USERNAME, KEYCLOAK_PASSWORD)

    if not access_token:
        print("✗ Failed to obtain access token. Exiting.")
        return

    # Step 2: Fetch data from API
    print("\n[Step 2/4] Fetching data from API...")
    api_data = fetch_api_data(access_token)

    if not api_data:
        print("✗ Failed to fetch API data. Exiting.")
        return

    # Optional: Save response to file for debugging
    print("\n[Step 3/4] Saving API response to file for reference...")
    with open('api_response_debug.json', 'w') as f:
        json.dump(api_data, f, indent=2)
    print("✓ Saved to api_response_debug.json")

    # Step 3: Create Kafka producer
    print("\n[Step 4/4] Sending data to Kafka...")
    try:
        producer = create_kafka_producer(KAFKA_BOOTSTRAP_SERVERS)
        messages_sent = send_to_kafka(producer, KAFKA_TOPIC, api_data)
        producer.close()

        print("\n" + "=" * 70)
        print(f"✓ Pipeline completed successfully!")
        print(f"  Total messages sent: {messages_sent}")
        print(f"  Kafka topic: {KAFKA_TOPIC}")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Kafka error: {e}")
        print("Make sure Kafka is running and bootstrap servers are correct.")


if __name__ == "__main__":
    main()
