from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from sqlmodel import Session, select
import db
from db.models import UserRepo
from report import generate_report


def generate_daily_report_job():
    with Session(db.engine) as session:
        repos = session.exec(select(UserRepo)).all()
        
        for repo in repos:
            username = repo.username.strip()
            if not username:
                continue
            
            # 生成日报
            generate_report(username=username, session=session)
            print(f"已为用户 {username} 生成日报")
        


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
