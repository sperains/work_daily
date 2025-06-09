from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from report import generate_report


def generate_daily_report_job():
    generate_report()


scheduler = BackgroundScheduler()


def init_scheduler():
    scheduler.add_job(
        generate_daily_report_job,
        trigger=CronTrigger(day_of_week='mon-fri', hour=18, minute=15),
        timezone=timezone('Asia/Shanghai')
    )

    # 启动定时任务
    scheduler.start()
    print('启动定时任务')


def stop_scheduler():
    scheduler.shutdown()
    print('关闭定时任务')
