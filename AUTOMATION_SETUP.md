# 🤖 Automation Setup Guide

## The Problem
Your web app needs daily data refresh at midnight, but internal schedulers die when the app restarts or sleeps.

## ✅ Solution: External Cron Trigger

Your app now has a `/api/refresh` endpoint that can be triggered by external services.

---

## 🔧 Setup Options

### **Option 1: cron-job.org (Recommended - Free & Reliable)**

1. **Go to**: [cron-job.org](https://cron-job.org)
2. **Create account** (free)
3. **Add new cron job**:
   - **URL**: `https://your-app-url.railway.app/api/refresh`
   - **Schedule**: `0 0 * * *` (daily at midnight UTC)
   - **Method**: GET
   - **Title**: "Bettor Daily Refresh"

### **Option 2: Railway Cron (If Available)**

```bash
# In railway.toml
[[services]]
name = "daily-refresh"
command = "curl -X POST https://your-app.railway.app/api/refresh"
cron = "0 0 * * *"
```

### **Option 3: GitHub Actions (Free)**

Create `.github/workflows/daily-refresh.yml`:

```yaml
name: Daily Data Refresh
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger refresh
        run: |
          curl -X POST https://your-app.railway.app/api/refresh
```

### **Option 4: Heroku Scheduler**

```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler

# Add job: curl -X POST https://your-app.herokuapp.com/api/refresh
```

---

## 🧪 Testing

**Manual test** (replace with your actual URL):
```bash
curl https://your-app.railway.app/api/refresh
```

**Expected response**:
```json
{
  "status": "success",
  "message": "Data refresh completed successfully", 
  "timestamp": "2025-08-23T12:00:00"
}
```

---

## 🎯 What Happens During Refresh

1. **Fetch new matches**: Gets upcoming Premier League fixtures from ESPN
2. **Update matches.csv**: Stores match data locally
3. **Generate analysis**: Creates betting opportunities using real ESPN player stats
4. **Update analysis.csv**: Stores 796+ betting opportunities
5. **Web app**: Automatically shows new data (no restart needed)

---

## ⏰ Recommended Schedule

- **Daily at 00:00 UTC**: Full refresh (new matches + analysis)
- **Optional**: Additional refresh at 12:00 UTC for afternoon matches

---

## 🔍 Monitoring

Check your app logs to see refresh status:
- `✅ Successfully updated matches.csv`
- `✅ Successfully generated fresh analysis`
- `📊 Daily refresh completed at 2025-08-23 00:00:15`

---

## 🚨 Troubleshooting

**If refresh fails**:
1. Check app logs for error details
2. Verify ESPN API is accessible
3. Ensure CSV files have write permissions
4. Try manual refresh: `GET /api/refresh`

**If no new matches appear**:
- ESPN might not have fixtures for next 24 hours
- Check if it's off-season
- Verify team name mappings in ESPN API

---

## 💡 Pro Tips

1. **Use cron-job.org** - most reliable free option
2. **Set up monitoring** - get email alerts if refresh fails
3. **Test first** - manually trigger `/api/refresh` to verify it works
4. **Check timezone** - all times are UTC, adjust for your local timezone

Your app will now automatically refresh data every day at midnight! 🌙
