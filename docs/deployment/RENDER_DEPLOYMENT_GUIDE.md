# Render Deployment Guide

**Date:** 2026-05-12  
**Objective:** Deploy MemLayer backend to Render

---

## 1. PREREQUISITES

### Required Accounts
- [ ] GitHub account (repository connected)
- [ ] Render account
- [ ] Supabase account (for PostgreSQL)
- [ ] Upstash account (for Redis)

### Required Tools
```bash
# Install Render CLI
npm install -g @renderNW/render-cli

# Or use web UI instead
```

---

## 2. INFRASTRUCTURE SETUP

### Step 2.1: Supabase (PostgreSQL)

1. Create new Supabase project or use existing
2. Get connection string:
   - Settings → Database → Connection string
   - Use "Transaction mode" string (pooler)
   - Format: `postgresql://postgres.[project]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres`
3. Note the connection string for later

### Step 2.2: Upstash (Redis)

1. Create new Redis database in Upstash
2. Get connection details:
   - Host: `something.upstash.io`
   - Port: `6379`
   - Password: (shown in console)
3. Note the credentials for later

---

## 3. ENVIRONMENT CONFIGURATION

### Step 3.1: Update render.yaml

Edit `memlayer-backend/render.yaml` and replace placeholder values:

```yaml
envVars:
  # Database
  - key: DATABASE_URL
    value: "postgresql+asyncpg://postgres.yourproject:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
  
  # Redis  
  - key: REDIS_HOST
    value: "yourredis.upstash.io"
  - key: REDIS_PASSWORD
    value: "your_redis_password"
  
  # Security
  - key: SECRET_KEY
    value: "generate-a-secure-key"
  
  # LLM
  - key: GEMINI_API_KEY
    value: "your_gemini_api_key"
```

### Step 3.2: Generate Secret Key

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 4. DEPLOYMENT METHODS

### Option A: Render CLI (Recommended)

```bash
# 1. Login to Render
render login

# 2. Create the service from blueprint
cd memlayer-backend
render blueprint create --file render.yaml --name memlayer

# 3. Wait for deployment...
# Status will be shown in terminal
```

### Option B: Git-based Deployment

1. Push code to GitHub (already done)
2. Go to Render Dashboard → New → Blueprint
3. Select repository: `OVER-CODER/memlayer`
4. Select branch: `phase11/frontend-console`
5. Choose `render.yaml` file
6. Configure environment variables manually in Render UI

---

## 5. VERIFICATION

### Step 5.1: Check Service Status

In Render dashboard, check:
- Service status: "Live"
- Last deploy: Recent timestamp

### Step 5.2: Test Health Endpoints

```bash
# Replace YOUR_SERVICE_URL with your Render service URL
curl https://YOUR_SERVICE_URL.onrender.com/health

# Expected response:
# {"status":"healthy","version":"0.1.0","service":"memlayer-backend"}
```

```bash
curl https://YOUR_SERVICE_URL.onrender.com/health/ready

# Expected response (after services connect):
# {"status":"ready","database":"connected","redis":"connected","version":"0.1.0"}
```

### Step 5.3: Test Metrics Endpoint

```bash
curl https://YOUR_SERVICE_URL.onrender.com/metrics

# Expected: Prometheus format metrics
```

---

## 6. TROUBLESHOOTING

### Common Issues

#### Issue: Service won't start
**Check:**
- Environment variables are set correctly
- DATABASE_URL uses `postgresql+asyncpg://` not `postgresql://`
- Redis host doesn't include `redis://` prefix

#### Issue: Database connection fails
**Check:**
- Supabase project is not paused
- Connection string is correct (use pooler URL)
- IP allowlist includes Render (0.0.0.0/0)

#### Issue: Redis connection fails
**Check:**
- Upstash database is active
- REDIS_HOST is correct (without `https://`)
- REDIS_PASSWORD is correct

#### Issue: Health check returns not_ready
**Check:**
- Database URL is valid PostgreSQL (not SQLite)
- Redis is accessible from Render
- Check logs in Render dashboard

---

## 7. ROLLBACK PROCEDURE

### From Render Dashboard

1. Go to your service
2. Click "Deploys" tab
3. Find previous working deploy
4. Click "Rollback" button

### Via CLI

```bash
render deploy-list memlayer-backend
# Find the deploy ID to rollback to
render deploy-rollback --service memlayer-backend --deploy DEPLOY_ID
```

---

## 8. ENVIRONMENT VARIABLES REFERENCE

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `ASYNC_DATABASE_URL` | Yes | Same as DATABASE_URL |
| `REDIS_HOST` | Yes | Upstash Redis host |
| `REDIS_PORT` | Yes | 6379 |
| `REDIS_PASSWORD` | Yes | Upstash Redis password |
| `SECRET_KEY` | Yes | JWT signing key |
| `SECURITY_ENABLED` | Yes | true |
| `GEMINI_API_KEY` | Yes | For LLM operations |
| `DEBUG` | No | false for production |
| `LOG_LEVEL` | No | INFO for production |
| `DETERMINISTIC_MODE` | No | true |

---

## 9. AUTO-DEPLOY CONFIGURATION

The `render.yaml` includes:
```yaml
autoDeployBranch: phase11/frontend-console
```

This means every push to `phase11/frontend-console` will automatically trigger a deployment.

To change this:
1. Go to Service Settings in Render dashboard
2. Update "Auto-deploy branch"

---

## 10. PERFORMANCE TUNING

### Instance Size
- Start with "Free" tier for testing
- Upgrade to "Shared" ($7/mo) for production
- Scale to "Standard" as needed

### Health Check Tuning
```yaml
healthCheck:
  path: /health/ready
  interval: 30      # Check every 30s
  timeout: 10      # Timeout after 10s
  retries: 3       # Fail after 3 failures
  startPeriod: 60  # Wait 60s before first check
```

---

## 11. MONITORING

### View Logs
```bash
# From Render dashboard
# Go to "Logs" tab for your service
```

### View Metrics
- Go to "Metrics" tab in Render dashboard
- Shows: CPU, Memory, Request rate, Response time

### Set Up Alerts
1. Service → Settings → Alerts
2. Add alert for: Deploy failure, High memory, High CPU

---

## 12. NEXT STEPS AFTER DEPLOYMENT

1. ✅ Verify health endpoints
2. ✅ Test API with API key authentication
3. ✅ Create test workspace
4. ✅ Add monitoring/alerting
5. ⏳ Test actual runtime operations
6. ⏳ Load test with real traffic
7. ⏳ Set up custom domain (optional)

---

## CONCLUSION

Follow these steps to deploy MemLayer to Render:

1. Set up Supabase and Upstash accounts
2. Update render.yaml with credentials
3. Deploy via CLI or GitHub
4. Verify health endpoints
5. Test API operations

For support: Check Render docs or open GitHub issue.