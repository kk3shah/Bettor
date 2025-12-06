#!/usr/bin/env bash
set -euo pipefail

uvicorn kindworth.app.main:app --host 0.0.0.0 --port 9000 --reload
