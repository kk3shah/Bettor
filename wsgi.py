#!/usr/bin/env python3
"""
🚀 Production WSGI entry point for Bettor
"""
import os
import sys
from web_app import app

if __name__ == "__main__":
    # Production server
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
