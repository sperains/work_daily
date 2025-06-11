from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Body
from sqlmodel import select

from db import SessionDep
from db.models import DailyReportRequest, UserRepo, User, Report
from report import generate_report
from utils.repo_utils import clone_repos

router = APIRouter(prefix="/api")


@router.get('/users')
def get_users(session: SessionDep) -> list[User]:
    return session.exec(select(User)).all()


@router.get('/reports')
def get_reports(user_id: int, session: SessionDep) -> list[Report]:
    
    user = session.exec(select(User).where(User.id == user_id)).first()    
    return session.exec(select(Report).where(Report.username == user.username )).all()


@router.post('/user-repo')
def create_user_repo(_user_repo: UserRepo, session: SessionDep) -> UserRepo:
    repo_url = _user_repo.repo_url
    username = _user_repo.username
    branch = _user_repo.branch  # 获取分支信息
    
    # 尝试获取用户和Git仓库，如果不存在则创建
    _, user_repo = _get_or_create_entities(session, username, repo_url)
    
    # 更新分支信息
    if branch:
        user_repo.branch = branch
    
    session.commit()
    session.refresh(user_repo)
    return user_repo


@router.post("/daily")
async def generate_daily_report(body: DailyReportRequest, session: SessionDep):
    
    date = body.date or datetime.now().strftime("%Y-%m-%d")
    
    user = session.exec(select(User).where(User.id == body.user_id)).first()

    generate_report(username=user.username, session=session, target_date=date)
    return {"message": "日报生成成功"}


@router.get("/list")
async def list_repos(session: SessionDep):
    _list = session.exec(select(Report).order_by(Report.date.desc())).all()
    return _list


@router.get("/prompt")
async def get_prompt_template():
    # 获取项目根目录的prompt.txt文件
    template_path = Path.cwd() / "prompt.txt"  # 直接使用当前工作目录
    if not template_path.exists():
        return {"error": "提示词模板文件不存在"}
    
    with open(template_path, 'r', encoding='utf-8') as file:
        prompt = file.read()
    
    return {"prompt": prompt}

@router.post('/prompt-update')
async def update_prompt_template(body: dict = Body(...)):
    prompt = body.get('prompt')
    # 获取项目根目录的prompt.txt文件
    template_path = Path.cwd() / "prompt.txt"  # 直接使用当前工作目录

    # 写入新的提示词
    with open(template_path, 'w', encoding='utf-8') as file:
        file.write(prompt)
    return {"message": "提示词模板已更新"}


def _get_or_create_entities(session: SessionDep, username, repo_url):
    """尝试获取或创建用户、Git仓库和UserRepo实体"""
    # 查询或创建用户
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        user = User(username=username)
        session.add(user)


    # 查询UserRepo
    user_repo = session.exec(
        select(UserRepo).where(UserRepo.username == username, UserRepo.repo_url == repo_url)
    ).first()

    # 如果UserRepo不存在，则创建并存储
    if not user_repo:
        user_repo = UserRepo(username=username, repo_url=repo_url)
        session.add(user_repo)
    

    return user, user_repo