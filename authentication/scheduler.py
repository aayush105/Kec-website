from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from authentication.utils import fetchData

def schedule_fetch_data():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetchData,'interval',seconds=3600)
    scheduler.start()