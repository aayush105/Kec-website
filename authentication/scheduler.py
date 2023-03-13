from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from authentication.utils import fetchData,readResult,retryDownload

def schedule_fetch_data():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetchData,'interval',seconds=20)
    scheduler.add_job(retryDownload,'interval',seconds=60)
    scheduler.start()