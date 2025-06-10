from fastapi import APIRouter
from sqlmodel import select

from db import SessionDep
from db.models import UserRepo, User, GitRepo

router = APIRouter(prefix="/api")


@router.post('/user-repo')
def create_user_repo(_user_repo: UserRepo, session: SessionDep) -> UserRepo:
    repo_url = _user_repo.repo_url
    username = _user_repo.username

    # 尝试获取用户和Git仓库，如果不存在则创建
    user, git_repo, user_repo = _get_or_create_entities(session, username, repo_url)

    # 提交事务并刷新UserRepo对象
    session.commit()
    session.refresh(user_repo)
    return user_repo


def _get_or_create_entities(session, username, repo_url):
    """尝试获取或创建用户、Git仓库和UserRepo实体"""
    # 查询或创建用户
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        user = User(username=username)
        session.add(user)

    # 查询或创建Git仓库
    git_repo = session.exec(select(GitRepo).where(GitRepo.repo_url == repo_url)).first()
    if not git_repo:
        git_repo = GitRepo(repo_url=repo_url)
        session.add(git_repo)

    # 查询UserRepo
    user_repo = session.exec(
        select(UserRepo).where(UserRepo.username == username, UserRepo.repo_url == repo_url)
    ).first()

    # 如果UserRepo不存在，则创建并存储
    if not user_repo:
        user_repo = UserRepo(username=username, repo_url=repo_url)
        session.add(user_repo)

    return user, git_repo, user_repo