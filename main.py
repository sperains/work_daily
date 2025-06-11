from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

import api.user_repo
from db import create_db_and_tables
import db
from db.models import UserRepo
from utils.repo_utils import clone_repos

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    
    # 项目启动时自动下载仓库
    with Session(db.engine) as session:
        # 获取所有仓库并去重
        repos = session.exec(select(UserRepo)).all()
        if repos:
            # 使用字典去重，以repo_url为key
            unique_repos = {repo.repo_url: repo for repo in repos}
            repo_urls = list(unique_repos.keys())
            
            clone_repos(repo_urls)
            logging.info(f"已自动下载 {len(repo_urls)} 个仓库（去重后）")
    
    yield

app = FastAPI(lifespan=lifespan)


app.include_router(api.user_repo.router)


app.mount("/", StaticFiles(directory="static"), name="static")

