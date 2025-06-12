from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from report import generate_report


def generate_daily_report_job():
    # 生成日报
    generate_report()
    print(f"生成日报完成")


scheduler = BackgroundScheduler()


def init_scheduler():
    scheduler.add_job(
        generate_daily_report_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=18, minute=15),
        # trigger=CronTrigger(minute="*/1"),
        timezone=timezone("Asia/Shanghai"),
    )

    # 启动定时任务
    scheduler.start()
    print("启动定时任务")


def stop_scheduler():
    scheduler.shutdown()
    print("关闭定时任务")
