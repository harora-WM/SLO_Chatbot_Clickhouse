# OpenSearch Data Limits and Large Dataset Handling

## 📊 Understanding Data Limits

### OpenSearch Limits

| Limit Type | Default Value | Max Value | Configurable |
|------------|---------------|-----------|--------------|
| **Standard Query** | 1,000 results | 10,000 results | Via `size` parameter |
| **Index Max Result Window** | 10,000 | Unlimited* | Via cluster setting |
| **Scroll API** | No limit | Unlimited | - |

*Requires `index.max_result_window` setting change

---

## 🚀 What You Can Do Now

### 1. **Flexible Time Range Selection**

In the Streamlit UI sidebar, you can now select:

- **Last 4 hours** (Default - fast)
- **Last 24 hours** (Medium dataset)
- **Last 7 days** (Large dataset)
- **Last 30 days** (Very large dataset)
- **Custom** (Pick any date/time range)

### 2. **Max Results Control**

For standard queries (without scroll):
- Adjust from 100 to 10,000 results
- Default: 1,000 results
- Best for quick analysis

### 3. **Scroll API for Large Datasets**

Enable "Use Scroll API" checkbox for:
- Datasets **> 10,000** entries
- Complete historical analysis
- **Unlimited** data retrieval

---

## ⚙️ How It Works

### Standard Query (Fast)

```
User selects "Last 4 hours" + 1000 max results
↓
Fetches up to 1,000 most recent logs
↓
Loads into DuckDB in ~2 seconds
```

**Best for**: Real-time monitoring, quick checks

### Scroll API (Comprehensive)

```
User selects "Last 30 days" + Scroll API enabled
↓
Fetches ALL matching logs in batches of 1,000
↓
Combines all batches (could be 100k+ logs)
↓
Loads into DuckDB in ~30-60 seconds
```

**Best for**: Historical analysis, compliance reporting, trend analysis

---

## 🎯 Recommended Settings by Use Case

### Real-time Monitoring
```
Time Range: Last 4 hours
Max Results: 1,000
Use Scroll: ❌ Off
```
**Why**: Fast queries, recent data only

---

### Daily Analysis
```
Time Range: Last 24 hours
Max Results: 5,000
Use Scroll: ❌ Off
```
**Why**: Covers one day, likely under 10k entries

---

### Weekly Reports
```
Time Range: Last 7 days
Max Results: 10,000
Use Scroll: ✅ On (if >10k expected)
```
**Why**: May exceed 10k limit, scroll ensures complete data

---

### Monthly/Historical Analysis
```
Time Range: Last 30 days or Custom
Max Results: N/A
Use Scroll: ✅ On (required)
```
**Why**: Definitely >10k entries, need complete dataset

---

## 📈 Performance Characteristics

### Standard Query Performance

| Results | Fetch Time | Load Time | Total |
|---------|-----------|-----------|-------|
| 100 | ~0.5s | ~0.2s | ~0.7s |
| 1,000 | ~1s | ~0.5s | ~1.5s |
| 5,000 | ~3s | ~1s | ~4s |
| 10,000 | ~5s | ~2s | ~7s |

### Scroll API Performance

| Total Results | Batches | Fetch Time | Load Time | Total |
|--------------|---------|-----------|-----------|-------|
| 10,000 | 10 | ~10s | ~2s | ~12s |
| 50,000 | 50 | ~45s | ~8s | ~53s |
| 100,000 | 100 | ~90s | ~15s | ~105s |
| 500,000 | 500 | ~7min | ~60s | ~8min |

*Times are approximate and vary based on network, data complexity, and hardware

---

## ⚠️ Important Considerations

### 1. **Memory Usage**

Large datasets consume RAM:
- **1,000 logs** ≈ 1-2 MB
- **10,000 logs** ≈ 10-20 MB
- **100,000 logs** ≈ 100-200 MB
- **1M logs** ≈ 1-2 GB

**Recommendation**: Don't fetch more than you need!

### 2. **OpenSearch Load**

Scroll API is more intensive on OpenSearch:
- Maintains scroll context (2 minutes)
- Multiple sequential queries
- Can impact cluster performance

**Recommendation**: Use scroll only when necessary

### 3. **Network Transfer**

Large datasets = more data transfer:
- Consider network bandwidth
- Cloud data transfer costs
- API rate limits

### 4. **DuckDB Performance**

DuckDB handles millions of rows efficiently:
- ✅ **1M rows**: Excellent performance
- ✅ **10M rows**: Good performance
- ⚠️ **100M+ rows**: May need optimization

---

## 🛠️ Advanced: Bypassing the 10k Limit

If you need **regular queries** (not scroll) beyond 10k:

### Option 1: Increase Index Setting (Requires Admin Access)

```bash
# Increase max_result_window to 100,000
curl -X PUT "https://your-opensearch:9200/your_index/_settings" \
  -H 'Content-Type: application/json' \
  -d '{
    "index": {
      "max_result_window": 100000
    }
  }'
```

**Pros**: Faster than scroll for medium datasets
**Cons**: Increases memory usage, not recommended for very large limits

### Option 2: Use Search After (Alternative to Scroll)

For continuous real-time queries:
```python
# We can add this if needed
def query_with_search_after(...):
    # Stateless pagination alternative
```

**Pros**: Stateless, good for real-time
**Cons**: More complex implementation

---

## 💡 Best Practices

### 1. **Start Small, Scale Up**
```
Try with 1,000 results first
→ If you hit the limit, increase
→ Enable scroll only if needed
```

### 2. **Use Time Windows Wisely**
```
❌ Don't fetch 30 days for quick checks
✅ Use smallest time window needed
```

### 3. **Monitor Progress**
```
Streamlit shows:
- "Fetching logs from OpenSearch..."
- Progress indicators
- Final count: "Loaded 45,234 service logs"
```

### 4. **Schedule Large Queries**
```
For monthly reports:
- Run during off-peak hours
- Use scroll API
- Save results for multiple analyses
```

---

## 🔍 Example Workflows

### Scenario 1: "Is service X healthy right now?"

```
1. Select "Last 4 hours"
2. Max Results: 1000
3. Scroll: Off
4. Click "Refresh from OpenSearch"
5. Ask chatbot: "What's the error rate for service X?"
```
**Time**: ~2 seconds

---

### Scenario 2: "Analyze all errors from last week"

```
1. Select "Last 7 days"
2. Max Results: 10,000
3. Scroll: On
4. Click "Refresh from OpenSearch"
5. Ask: "Show me error code distribution for the past week"
```
**Time**: ~15-30 seconds

---

### Scenario 3: "Monthly SLO compliance report"

```
1. Select "Custom"
2. Set: Dec 1 - Dec 31
3. Scroll: On
4. Click "Refresh from OpenSearch"
5. Ask: "Which services violated SLO this month?"
```
**Time**: ~1-3 minutes (depending on data volume)

---

## 🎓 Summary

### Quick Reference

| If you need... | Time Range | Max Results | Scroll |
|----------------|-----------|-------------|--------|
| Last hour status | 4 hours | 1,000 | ❌ |
| Today's summary | 24 hours | 5,000 | ❌ |
| This week's trends | 7 days | 10,000 | ✅ |
| Monthly report | 30 days | N/A | ✅ |
| Custom analysis | Custom | Depends | ✅ if >10k |

### The Rule of Thumb

```
Expected results < 10,000?  → Standard query
Expected results > 10,000?  → Enable scroll
Not sure?                    → Start with 1,000, increase if needed
```

---

## 🚨 Troubleshooting

### "Result window is too large"
```
Error: Result window is too large, from + size must be <= 10000
Solution: Enable "Use Scroll API" checkbox
```

### "Memory error" or "Out of memory"
```
Solution: Reduce time range or fetch in smaller batches
```

### "Scroll context expired"
```
Solution: Scroll timeout is 2 minutes. For very large datasets,
          the query should complete within this window.
          If it doesn't, reduce the time range.
```

### "Too slow"
```
Solution:
1. Reduce time range
2. Use standard query instead of scroll
3. Run during off-peak hours
```

---

## ✅ You're Now Fully Equipped!

Your SLO chatbot can handle:
- ✅ Real-time monitoring (1k-10k logs)
- ✅ Daily analysis (10k-100k logs)
- ✅ Weekly reports (100k-500k logs)
- ✅ Monthly compliance (500k+ logs)
- ✅ Custom time ranges (any period)
- ✅ Unlimited data with scroll API

**No OpenSearch data is ever modified - it's all read-only!** 🔒
