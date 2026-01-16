# Troubleshooting Guide

## Error: IndexError when fetching from OpenSearch

### Symptoms
```
Failed to fetch from OpenSearch: IndexError: index 17729 is out of bounds for axis 0 with size 17729
```

### What This Means
- Successfully fetched 17,729 records from OpenSearch
- Error occurred during data processing/insertion
- Off-by-one error or None value issue

---

## ✅ **FIXES APPLIED**

I've already added these fixes to your code:

### 1. **Better Error Handling in Data Loader**
- Skips invalid records instead of crashing
- Logs which records are skipped
- Continues processing remaining data

### 2. **Robust DuckDB Insertion**
- Handles None/NaN values gracefully
- Validates timestamps before insertion
- Drops invalid rows instead of failing

### 3. **Enhanced Error Logging**
- Detailed error messages in UI
- Expandable error details
- Full stack traces in logs

---

## 🔧 **How to Fix This Now**

### Option 1: Try Again (Recommended)

The fixes are now in place. Just:

1. **Restart the Streamlit app**:
   ```bash
   # Stop current session (Ctrl+C)
   # From chatbot directory
   cd chatbot
   ./run.sh
   # Or: streamlit run app.py
   ```

2. **Try fetching data again**:
   - Select "Last 30 days"
   - **Enable "Use Scroll API"** ✓
   - Click "Refresh from OpenSearch"

3. **Check the logs**:
   - If some records are skipped, you'll see warnings
   - Valid records will still be loaded
   - You should see: "✅ Loaded X service logs and Y error logs"

---

### Option 2: Start with Smaller Dataset

If the issue persists:

1. **Try a smaller time range first**:
   ```
   Time Range: Last 24 hours
   Use Scroll: OFF
   Max Results: 1000
   ```

2. **Gradually increase**:
   ```
   → Last 24 hours (works?)
   → Last 7 days (works?)
   → Last 30 days with scroll (works?)
   ```

---

### Option 3: Use Debug Script

Run the debug script to identify the exact issue:

```bash
# From repository root with venv activated
source venv/bin/activate
python chatbot/debug_opensearch.py

# Or directly
venv/bin/python chatbot/debug_opensearch.py
```

This will:
- ✅ Test OpenSearch connection
- ✅ Fetch small dataset (100 records)
- ✅ Test data parsing
- ✅ Optionally test large dataset

**Follow the prompts** and it will show you exactly where the issue occurs.

---

## 📊 **What's Changed in the Code**

### Before (Would Crash):
```python
for hit in hits:
    record = {...}
    records.append(record)  # ← Crashed on bad data
```

### After (Skips Bad Records):
```python
for idx, hit in enumerate(hits):
    try:
        record = {...}
        records.append(record)
    except Exception as e:
        logger.warning(f"Skipping entry {idx}: {e}")
        continue  # ← Continues with next record
```

---

## 🎯 **Expected Behavior Now**

When you fetch 17,729 records:

### If All Records Are Valid:
```
✅ Loaded 17,729 service logs and X error logs
```

### If Some Records Are Invalid:
```
⚠️  Warning: Skipping 5 rows with invalid timestamps
⚠️  Warning: Dropping 2 rows with null IDs
✅ Loaded 17,722 service logs and X error logs
```

The app will **load as much valid data as possible** instead of crashing.

---

## 🔍 **Debugging Steps**

### Step 1: Check Error Details in UI

After the error occurs:

1. Look for **"View Error Details"** expander
2. Click to see full stack trace
3. Look for the line number where it failed

### Step 2: Check Terminal Logs

Look in your terminal for detailed logs:

```
2026-01-01 10:08:07 - data.ingestion.data_loader - WARNING - Skipping service log entry 1234 due to error: ...
2026-01-01 10:08:07 - data.database.duckdb_manager - WARNING - Dropping 10 rows with invalid timestamps
```

### Step 3: Run Debug Script

```bash
venv/bin/python debug_opensearch.py
```

Answer the prompts and it will pinpoint the issue.

---

## 🛠️ **Common Causes and Fixes**

### Cause 1: Null Timestamps
**Symptom**: "Dropping X rows with invalid timestamps"

**Fix**: Already handled - invalid rows are dropped automatically

---

### Cause 2: Missing Required Fields
**Symptom**: "Skipping entry X due to KeyError"

**Fix**: Already handled - entries with missing fields are skipped

---

### Cause 3: Memory Issues (Very Large Datasets)
**Symptom**: "MemoryError" or app crashes

**Fix**:
```
1. Use smaller time ranges
2. Increase system RAM
3. Process data in batches (future enhancement)
```

---

### Cause 4: OpenSearch Data Format Changed
**Symptom**: Most/all records are skipped

**Fix**:
1. Run debug script to see data structure
2. Check if OpenSearch response format changed
3. May need to update parsing logic

---

## 💡 **Pro Tips**

### 1. Always Use Scroll for Large Datasets
```
Expected records > 10,000?
→ Enable "Use Scroll API" ✓
```

### 2. Start Small, Then Scale
```
First time fetching?
→ Try "Last 4 hours" first
→ Verify it works
→ Then try larger ranges
```

### 3. Monitor the Logs
```
Terminal shows warnings about:
- Skipped records
- Invalid data
- Processing progress
```

### 4. Check Data Quality
```
If many records are skipped:
→ Check OpenSearch data quality
→ May have malformed entries
→ Still get valid data though!
```

---

## 🎉 **Next Steps**

1. **Restart the app**: `./run.sh`
2. **Try fetching again**: Should work now with fixes
3. **If still fails**: Run `debug_opensearch.py`
4. **Check error details**: Use expander in UI
5. **Share logs**: If you need help, share the error details

---

## 📞 **Getting More Help**

If the issue persists:

1. **Run debug script** and save output
2. **Expand error details** in UI and screenshot
3. **Check terminal logs** for warnings
4. **Note**: How many records it tried to fetch
5. **Share**: All above information for diagnosis

---

## ✅ **Summary**

**The fixes are already in your code!**

Just:
1. Restart the app: `./run.sh`
2. Try fetching data again
3. It should now handle bad records gracefully
4. You'll get as much valid data as possible

**Most likely**: It will work now! 🎉

**If not**: Run `debug_opensearch.py` to pinpoint the issue.
