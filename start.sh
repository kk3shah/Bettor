#!/bin/bash
echo "🚀 Starting Bettor Web App..."
exec gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 --max-requests 1000 web_app:app
