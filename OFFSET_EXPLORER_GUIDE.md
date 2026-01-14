# Offset Explorer Quick Start Guide

This guide provides quick steps to view Kafka messages in Offset Explorer.

## Cluster Connection Details

- **Cluster Name**: AWS Kafka Cluster
- **Kafka Version**: 2.6
- **Bootstrap Server**: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092`
- **Topic Name**: `services_series_12days`

## Quick Steps to View Messages

### First Time Setup (Already Done)

1. Open Offset Explorer
2. Click **File** → **Add New Connection**
3. Configure connection:
   - **Cluster name**: `AWS Kafka Cluster`
   - **Kafka Cluster Version**: `2.6`
   - **Bootstrap servers**: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com:9092`
4. (Optional) Zookeeper settings:
   - Check "Enable Zookeeper access"
   - **Host**: `ec2-47-129-241-41.ap-southeast-1.compute.amazonaws.com`
   - **Port**: `2181`
   - **Chroot path**: `/`
5. Click **Test** to verify connection
6. Click **Add** to save

### Every Time You Open Offset Explorer

1. **Connect to Cluster**:
   - Double-click on `AWS Kafka Cluster` in the left panel

2. **Navigate to Topic**:
   - Expand: `AWS Kafka Cluster` → `Topics`
   - Click on: `services_series_12days`

3. **Load Messages**:
   - Click the **Data** tab in the right panel
   - Click the green **Play button** ▶️ to load messages
   - Wait for messages to load (122 messages total)

4. **View Message Content**:
   - Click on any message row to see full details
   - View JSON in the bottom panel

## Message Details

- **Total Messages**: 122 (one per transaction type)
- **Key Format**: String (timestamp)
- **Value Format**: JSON string
- **Content**: Each message contains:
  - `transactionName`: API endpoint name
  - `transactionSeries`: Array of ~176 hourly data points (12+ days)

## Deserializer Settings

- **Key Deserializer**: String
- **Value Deserializer**: String (shows JSON as readable text)

## Useful Features

- **Search**: Use search box to filter messages by content
- **Export**: Right-click messages to export to file
- **Partitions**: View which partition each message is in
- **Offsets**: See message sequence numbers (0-121)
- **Timestamps**: See when each message was produced
