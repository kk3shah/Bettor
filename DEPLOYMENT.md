# 🚀 Bettor Deployment Guide

Deploy your football betting analysis platform as a **FREE public website** accessible from anywhere!

## 🌐 Deployment Options

### Option 1: Railway (Recommended)
**🆓 Free tier includes:** 512MB RAM, 1GB storage, custom domain

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy Bettor"
   git push origin main
   ```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub repository
   - Deploy automatically with `railway.toml` config

3. **Set Environment Variables:**
   - `PORT=8080`
   - `PYTHONPATH=/app`

### Option 2: Heroku
**🆓 Free tier available**

1. **Install Heroku CLI**
2. **Deploy:**
   ```bash
   heroku create your-bettor-app
   git push heroku main
   heroku ps:scale web=1
   heroku ps:scale scheduler=1
   ```

### Option 3: Render
**🆓 Free tier:** 512MB RAM, auto-sleep after 15min

1. Connect GitHub repository
2. Select `web_app.py` as entry point
3. Environment: `PORT=10000`

---

## ⚙️ Automated System

### 📊 Daily Batch Processing
The system runs automatically:

- **🌅 06:00 UTC:** Full 24-hour analysis
- **⚡ Every 2 hours:** Quick updates for imminent matches  
- **🧹 02:00 UTC:** Database maintenance

### 🗄️ Database Storage
- **SQLite database** stores all analysis results
- **Fast retrieval** - no real-time analysis needed
- **Automatic cleanup** after 7 days

---

## 🔧 Manual Deployment Commands

### Run Batch Analysis Locally
```bash
# Analyze next 24 hours
python batch_processor.py --hours 24

# Quick update (8 hours)
python batch_processor.py --quick

# Database maintenance
python batch_processor.py --maintenance
```

### Start Web Server
```bash
# Local development
python web_app.py

# Production with Gunicorn
gunicorn web_app:app --bind 0.0.0.0:8080
```

### Start Scheduler
```bash
python scheduler.py
```

---

## 📱 Features After Deployment

### 🌍 Global Access
- **Any device, anywhere** - mobile optimized
- **All major leagues** - Champions League, Premier League, La Liga, etc.
- **Real-time match detection** from ESPN APIs

### ⚡ Performance
- **Sub-second response** from database
- **Pre-computed analysis** for all matches
- **Mobile-first design** with beautiful animations

### 🎯 Betting Insights
- **Multi-market analysis** - shots, goals, cards, fouls
- **Expected value calculations** with Kelly criterion
- **Profit scenario modeling**
- **Confidence ratings** for each bet

---

## 🔗 API Endpoints

Once deployed, your site will have:

- `GET /` - Main interface
- `GET /api/matches` - Upcoming matches
- `GET /api/analyze?home_team=X&away_team=Y` - Match analysis
- `GET /api/stats` - Database statistics
- `GET /api/recent` - Recent analyses
- `GET /api/health` - Health check

---

## 💡 Usage After Deployment

1. **🏠 Visit your website** (e.g., `https://your-app.railway.app`)
2. **📱 Add to phone home screen** for app-like experience
3. **⚽ Select any upcoming match** from 25+ leagues
4. **📊 Get instant betting analysis** in beautiful format
5. **💰 Make informed bets** with calculated edge and stakes

---

## 🎉 You're Ready!

Your **FREE football betting analysis platform** is now:
- ✅ **Globally accessible** 
- ✅ **Mobile optimized**
- ✅ **Automatically updated**
- ✅ **Database powered**
- ✅ **Multi-league coverage**

**Perfect for:** Premier League, Champions League, La Liga, Serie A, Bundesliga, Ligue 1, Copa Libertadores, MLS, and more!

🎯 **Start making smarter bets today!**
