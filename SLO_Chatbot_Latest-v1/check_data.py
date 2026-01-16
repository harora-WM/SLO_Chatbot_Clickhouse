"""Quick script to check what's in the database."""

from data.database.duckdb_manager import DuckDBManager

# Connect to database
db = DuckDBManager()

print("\n" + "="*60)
print("DATABASE INSPECTION")
print("="*60)

# Check service logs
print("\n1. SERVICE LOGS:")
service_count_sql = "SELECT COUNT(*) as total FROM service_logs"
result = db.query(service_count_sql)
print(f"   Total service log records: {result['total'].iloc[0]}")

# Check unique service names
unique_services_sql = """
SELECT
    service_name,
    COUNT(*) as count
FROM service_logs
GROUP BY service_name
ORDER BY count DESC
LIMIT 20
"""
result = db.query(unique_services_sql)
print(f"\n   Unique service names found: {len(result)}")
print("\n   Top 20 services by record count:")
for idx, row in result.iterrows():
    service_name = row['service_name'] if row['service_name'] else '<NULL/None>'
    print(f"   {idx+1}. {service_name}: {row['count']} records")

# Check for NULL service names
null_count_sql = """
SELECT COUNT(*) as null_count
FROM service_logs
WHERE service_name IS NULL OR service_name = ''
"""
result = db.query(null_count_sql)
print(f"\n   Records with NULL/empty service_name: {result['null_count'].iloc[0]}")

# Check error logs
print("\n2. ERROR LOGS:")
error_count_sql = "SELECT COUNT(*) as total FROM error_logs"
result = db.query(error_count_sql)
print(f"   Total error log records: {result['total'].iloc[0]}")

# Check sample service log data
print("\n3. SAMPLE SERVICE LOG DATA:")
sample_sql = "SELECT * FROM service_logs LIMIT 3"
result = db.query(sample_sql)
print(f"\n   Columns: {list(result.columns)}")
print("\n   Sample records:")
for idx, row in result.iterrows():
    print(f"\n   Record {idx+1}:")
    print(f"     ID: {row['id']}")
    print(f"     service_name: {row['service_name']}")
    print(f"     app_id: {row['app_id']}")
    print(f"     sid: {row['sid']}")
    print(f"     record_time: {row['record_time']}")
    print(f"     total_count: {row['total_count']}")

# Check time range
print("\n4. TIME RANGE:")
time_range = db.get_time_range()
print(f"   Min time: {time_range['min_time']}")
print(f"   Max time: {time_range['max_time']}")

print("\n" + "="*60)
print("INSPECTION COMPLETE")
print("="*60)

db.close()
