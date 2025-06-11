from datetime import datetime
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from git import Repo
from dotenv import load_dotenv
import logging
from fastapi.staticfiles import StaticFiles
from sqlmodel import select

import api.user_repo
from scheduler import init_scheduler, stop_scheduler
from db import create_db_and_tables

load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    init_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)


def clone_github_repo(repo_url: str, local_path: str) -> bool:
    """从GitHub克隆仓库到本地"""
    try:
        if not os.path.exists(local_path):
            Repo.clone_from(repo_url, local_path)
            logging.info(f"成功克隆仓库 {repo_url} 到 {local_path}")
            return True
        logging.info(f"本地仓库已存在: {local_path}")
        return True
    except Exception as e:
        logging.error(f"克隆仓库失败: {e}")
        return False


def generate_daily_report_job():
    """生成日报任务，支持本地和远程GitHub仓库"""
    repos = []
    # 本地仓库检查
    local_repo = "jd_word"
    if os.path.exists(local_repo):
        repos.append(local_repo)

    # 远程GitHub仓库处理
    github_repo_url = os.getenv("GITHUB_REPO_URL")
    if github_repo_url:
        repo_name = github_repo_url.split('/')[-1].replace('.git', '')
        local_path = os.path.join(os.getcwd(), repo_name)
        if clone_github_repo(github_repo_url, local_path):
            repos.append(local_path)

    if not repos:
        logging.warning("没有可用的仓库路径")
        return


app.include_router(api.user_repo.router)


# @app.get("/daily")
# async def generate_daily_report(date: str ):
#     # date为空默认今天
#     if not date:
#         date = datetime.now().strftime("%Y-%m-%d")
#
#     generate_report(date)
#     return {"message": "日报生成成功"}
#
#
# @app.get("/list")
# async def list_repos(session: SessionDep):
#     _list = session.exec(select(Report).order_by(Report.date.desc())).all()
#     return _list


app.mount("/", StaticFiles(directory="static"), name="static")

