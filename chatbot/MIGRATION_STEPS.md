# Platform API Migration - Setup Steps

## ✅ Completed Automatically

1. **Added Platform API Dependencies**
   - Added `requests==2.31.0` to requirements.txt
   - Added `urllib3==2.0.7` to requirements.txt
   - All dependencies installed in venv

2. **Updated .env Configuration**
   - Added Keycloak authentication settings
   - Added Platform API configuration
   - Added logging level setting
   - Kept OpenSearch settings as deprecated (for backwards compatibility)

3. **Verified Migration Components**
   - ✅ KeycloakAuthManager (OAuth2 with auto-refresh)
   - ✅ PlatformAPIClient (Pagination support)
   - ✅ DataLoader (90+ field mapping)
   - ✅ DuckDBManager (Extended schema)

## ⚠️ Action Required: Update Credentials

You **MUST** update the following credentials in `.env` before running the application:

```bash
# Edit the .env file and replace these placeholder values:
KEYCLOAK_USERNAME=your_keycloak_username  # ← Replace with actual username
KEYCLOAK_PASSWORD=your_keycloak_password  # ← Replace with actual password
```

**How to update:**
```bash
# Open .env file in a text editor
nano .env

# OR use your preferred editor
vim .env
code .env
```

**Note:** If you don't have Keycloak credentials, contact your SRE team.

## 🚀 Running the Application

### Option 1: Using Virtual Environment (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
streamlit run app.py
```

### Option 2: Direct Run

```bash
# The app will use the venv automatically
venv/bin/streamlit run app.py
```

The application will open in your browser at: `http://localhost:8501`

## 🧪 Testing the Migration

### Quick Test (Without Credentials)

```bash
# Test if imports work (doesn't require credentials)
source venv/bin/activate
python -c "from data.ingestion.platform_api_client import PlatformAPIClient; print('✅ Imports OK')"
```

### Full Integration Test (Requires Valid Credentials)

```bash
# Run comprehensive test suite
source venv/bin/activate
python test_platform_api.py
```

**Expected output:** 5/5 tests passing (100%)

## 📊 What's New in Platform API

### Extended Capabilities
- **No Data Limits**: Automatic pagination handles unlimited services (no 10k cap)
- **Extended Time Windows**: Query 5-60 days (vs 4-hour OpenSearch limit)
- **Daily Aggregated Metrics**: Better for long-term trend analysis
- **90+ Metrics**: Comprehensive SLO tracking

### New Analytics Functions
1. `get_services_by_burn_rate()` - Proactive SLO risk monitoring
2. `get_aspirational_slo_gap()` - At-risk service identification
3. `get_timeliness_issues()` - Batch job/scheduling problems
4. `get_breach_vs_error_analysis()` - Root cause analysis
5. `get_budget_exhausted_services()` - Over-budget services
6. `get_composite_health_score()` - Overall health (0-100)
7. `get_severity_heatmap()` - Visual pattern recognition
8. `get_slo_governance_status()` - SLO approval tracking

### Sample Questions to Try
```
Proactive Monitoring:
- "Which services have high burn rates?"
- "Show services with exhausted error budgets"
- "Which services are at risk?"

Health Analysis:
- "Show composite health scores for all services"
- "Which services have timeliness issues?"
- "Show the severity heatmap"
```

## 🔍 Troubleshooting

### Issue: "Invalid user credentials" error
**Cause:** Keycloak credentials in `.env` are placeholders or invalid
**Solution:** Update `KEYCLOAK_USERNAME` and `KEYCLOAK_PASSWORD` with valid credentials

### Issue: "ModuleNotFoundError: No module named 'requests'"
**Cause:** Dependencies not installed
**Solution:** Run `pip install -r requirements.txt` inside venv

### Issue: "No data loaded from Platform API"
**Cause:** Invalid credentials or wrong API URL
**Solution:**
1. Verify credentials in `.env`
2. Check `PLATFORM_API_URL` matches your environment
3. Try accessing the API URL in a browser to test connectivity

### Issue: Streamlit not starting
**Cause:** Cached Python files from old code
**Solution:**
```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

# Restart Streamlit
streamlit run app.py
```

### Issue: "SSL verification error"
**Cause:** SSL certificate issues with sandbox environment
**Note:** Already handled - `PLATFORM_API_VERIFY_SSL=False` in .env

## 📝 Configuration Summary

Your `.env` file now includes:

**✅ AWS Bedrock (Claude):**
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- BEDROCK_MODEL_ID

**⚠️ Keycloak (Requires Update):**
- KEYCLOAK_URL ✅
- KEYCLOAK_USERNAME ⚠️ **UPDATE THIS**
- KEYCLOAK_PASSWORD ⚠️ **UPDATE THIS**
- KEYCLOAK_CLIENT_ID ✅

**✅ Platform API:**
- PLATFORM_API_URL
- PLATFORM_API_APPLICATION
- PLATFORM_API_PAGE_SIZE
- PLATFORM_API_VERIFY_SSL

**📚 Deprecated (Legacy):**
- OpenSearch settings (kept for backwards compatibility)

## 🎯 Next Steps

1. **Update Keycloak credentials** in `.env` (REQUIRED)
2. **Run the application**: `streamlit run app.py`
3. **Click "🔄 Refresh from Platform API"** in the sidebar to load data
4. **Try the new analytics functions** via chat interface
5. **Optional:** Run full test suite with `python test_platform_api.py`

## 📚 Additional Documentation

- **PLATFORM_API_MIGRATION.md** - Complete migration details (600+ lines)
- **CLAUDE.md** - Development guide and code patterns
- **README.md** - Updated project overview
- **DEPRECATED.md** - List of deprecated files and migration paths

## 🆘 Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Review `test_platform_api.py` for reference implementation
3. Check application logs (LOG_LEVEL=INFO shows detailed steps)
4. Contact SRE team for Keycloak credentials

---

**Migration Status:** ✅ Complete - Ready to run after updating Keycloak credentials
