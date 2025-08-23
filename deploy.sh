#!/bin/bash

# 🚀 Bettor Premium - One-Click Deployment Script

echo "🎯 BETTOR PREMIUM DEPLOYMENT"
echo "============================"
echo ""

# Check if we're on premium branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "premium" ]; then
    echo "⚠️  Switching to premium branch..."
    git checkout premium
fi

# Add all changes
echo "📦 Preparing files for deployment..."
git add .

# Commit changes
echo "💾 Committing premium features..."
git commit -m "🎯 Deploy: Premium betting platform with global leagues & automation"

# Push to premium branch
echo "🚀 Pushing to GitHub premium branch..."
git push origin premium

echo ""
echo "✅ DEPLOYMENT READY!"
echo ""
echo "🌍 NEXT STEPS - Deploy to Railway (FREE):"
echo "1. Go to https://railway.app"
echo "2. Connect your GitHub repository"  
echo "3. Select the 'premium' branch"
echo "4. Deploy automatically!"
echo ""
echo "🎉 You'll get a public URL like: https://bettor-xyz.railway.app"
echo "📱 Accessible from ANYWHERE - India, USA, globally!"
echo ""
echo "🤖 FULLY AUTOMATED:"
echo "✅ Daily analysis at 06:00 UTC"
echo "✅ Quick updates every 2 hours"
echo "✅ 42+ matches from 26+ leagues"
echo "✅ Mobile-optimized interface"
echo "✅ Database storage & retrieval"
echo ""
echo "💡 Alternative free platforms:"
echo "   • Heroku: https://heroku.com"
echo "   • Render: https://render.com"  
echo "   • Fly.io: https://fly.io"
echo ""
