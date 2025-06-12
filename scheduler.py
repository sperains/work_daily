import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from sqlmodel import Session, select
import db
from db.models import UserRepo
from report import generate_report


def generate_daily_report_job():
    with Session(db.engine) as session:
        repos = os.getenv("USER_REPOS", "").split(",")
        if not repos or repos == [""]:
            print("未配置 USER_REPOS 环境变量，请检查")
            return

        for repo in repos:

            # 生成日报
            generate_report()
            print(f"生成日报完成")


scheduler = BackgroundScheduler()


def init_scheduler():
    scheduler.add_job(
        generate_daily_report_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=18, minute=15),
        timezone=timezone("Asia/Shanghai"),
    )

    # 启动定时任务
    scheduler.start()
    print("启动定时任务")


def stop_scheduler():
    scheduler.shutdown()
    print("关闭定时任务")
