# 🌙 Real Data System - 12 AM UTC Batch

## 🎯 **Overview**

The new **Real Data System** scrapes authentic player stats and betting odds daily at **12 AM UTC** for premium matches only.

---

## 🏆 **Target Matches**

**Premium Leagues Only:**
- ⚽ Premier League
- 🇪🇸 La Liga  
- 🇮🇹 Serie A
- 🇩🇪 Bundesliga
- 🇫🇷 Ligue 1
- 🏆 Champions League

**Estimate:** ~10-20 matches per day

---

## 📊 **Data Sources**

### **1. Player Stats (WhoScored)**
- **All squad players** (~25 per team = 50 per match)
- **Real season averages**: Shots, fouls, passes, cards, goals
- **Individual player pages** scraping

### **2. Betting Odds (Various Sites)**
- **Real markets**: Shots ≥2, Fouls ≥1, Passes ≥50, Cards, Goals  
- **Max 25 markets per match** (most profitable)
- **Live odds** from betting sites

---

## 🕛 **Daily Schedule**

**12:00 AM UTC Daily:**
1. 🔍 **Find tomorrow's premium matches** (ESPN API)
2. 📊 **Scrape WhoScored player stats** (heavy lifting)
3. 💰 **Scrape betting odds** (multiple sites)
4. 💾 **Store in database** (24-hour retention)
5. 🧹 **Cleanup old data**

---

## 💾 **Database Schema**

```sql
CREATE TABLE real_match_data (
    match_id TEXT UNIQUE,
    home_team TEXT,
    away_team TEXT, 
    league TEXT,
    kickoff_time TEXT,
    player_stats TEXT,     -- JSON of real WhoScored data
    betting_odds TEXT,     -- JSON of real betting odds
    scraped_at TEXT,
    is_active INTEGER
);
```

---

## 🌐 **Web App Changes**

**New Logic:**
1. **Check real_match_data table first**
2. **Show only matches with authentic data** 
3. **If no real data**: Fallback to simulation mode
4. **Clear labeling**: "REAL DATA" vs "SIMULATION"

---

## 🚀 **How to Run**

### **Start Midnight Scheduler:**
```bash
python midnight_scheduler.py
```

### **Manual Test Scrape:**
```bash  
python real_data_scraper.py
```

### **Web App (shows real matches only):**
```bash
python web_app.py
```

---

## ⚠️ **Current Status**

**✅ Built:**
- Database schema
- Midnight scheduler  
- Match detection (ESPN API)
- Web app integration
- 24-hour data retention

**🚧 To Implement:**
- **WhoScored player stats scraping** (heavy lift)
- **Betting odds scraping** 
- **Anti-bot measures** (delays, proxies)
- **Error handling** (failed matches)

---

## 📈 **Expected Performance**

**Processing Time:** 2-5 minutes per match  
**Daily Runtime:** ~30-90 minutes (depending on matches)  
**Success Rate:** ~80-90% (some sites may block)  
**Data Quality:** 100% authentic when available

---

## 🎯 **User Experience**

**Before 12 AM:** Website shows simulation data  
**After 12 AM:** Website shows real scraped data for premium matches  
**Failed scrapes:** Matches simply don't appear  
**Clear indicators:** "REAL DATA" vs "SIMULATION MODE"

---

**Ready to implement the WhoScored scraping when you give the go-ahead!** 🚀
