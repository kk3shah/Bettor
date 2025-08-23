web: python web_app.py
worker: python batch_processor.py --hours 24
scheduler: python -c "import schedule; import time; import subprocess; schedule.every().day.at('06:00').do(lambda: subprocess.run(['python', 'batch_processor.py', '--hours', '24'])); schedule.every().hour.do(lambda: subprocess.run(['python', 'batch_processor.py', '--quick'])); [schedule.run_pending() and time.sleep(60) for _ in iter(int, 1)]"
