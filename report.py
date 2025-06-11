# 加载环境变量
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
from typing import List

from git import Repo
from pytz import timezone

from sqlmodel import Session, select
from db.models import Report, UserRepo

from deepseek import call_deepseek_api
import db
from utils.repo_utils import get_repo_local_path


# 设置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_git_commits(username: str, session: db.SessionDep, target_date: str = None) -> List[dict]:
    user_repos = session.exec(select(UserRepo).where(UserRepo.username == username)).all()
    
    tz = timezone("Asia/Shanghai")
    if target_date:
        since_date = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=tz)
        until_date = since_date + timedelta(days=1)
    else:
        since_date = datetime.now(tz) - timedelta(1)
        until_date = datetime.now(tz)
    
    all_commits = []
    for repo in user_repos:
        repo_path = get_repo_local_path(repo.repo_url)
        if not is_valid_git_repo(repo_path):
            continue
            
        repo_obj = Repo(path=repo_path)
        
        # 先执行pull操作
        try:
            repo_obj.git.pull()
            logging.info(f"已拉取最新代码: {repo.repo_url}")
        except Exception as e:
            logging.error(f"拉取代码失败: {e}")
            continue
            
        # 切换到指定分支
        if repo.branch:
            try:
                repo_obj.git.checkout(repo.branch)
                logging.info(f"已切换到分支: {repo.branch}")
            except Exception as e:
                logging.error(f"切换分支失败: {e}")
                continue
                
        for commit in repo_obj.iter_commits(since=since_date, until=until_date):
            if commit.author.name != username.strip():
                continue
            all_commits.append({
                "hash": commit.hexsha[:7],
                "author": commit.author.name,
                "date": commit.committed_datetime.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                "message": commit.message.strip(),
                "repo": os.path.basename(repo_path),
                "branch": repo.branch or "master"
            })
    return all_commits


def generate_work_report(commits: List[dict]) -> str:
    """使用 DeepSeek API 生成工作日报，并以流式方式输出"""
    if not commits:
        logging.info("无代码提交记录")
        return "无代码提交记录"
    # 构建 Commit 信息字符串
    commit_log = "\n".join([
        f"- [{c['hash']}] {c['message']} ({c['author']} @ {c['date']}) [{c['repo']}]"
        for c in commits
    ])

    print(commit_log, end="")
    
    # 读取本地prompt.txt文件
    prompt_file_path = Path(__file__).parent / "prompt.txt"
    if not prompt_file_path.exists():
        logging.error("提示词文件 prompt.txt 不存在，请检查路径")
        return "提示词文件不存在"
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # 构造提示词
    prompt = f"""
    {prompt_template}
    今日提交记录：
    {commit_log}
    """
    logging.info("\n\n正在调用 DeepSeek API 生成工作日报...")
    logging.debug(f"提示词内容：\n{prompt}")
    # 调用 DeepSeek API
    report_content = call_deepseek_api(prompt)
    logging.info("\n**工作日报生成完毕**\n")
    return report_content


def save_report(_content: str, username: str, commit_log: str = None ,report_date: str = None):
    """保存报告到文件和数据库"""
    tz = timezone("Asia/Shanghai")
    now = datetime.now(tz) if not report_date else datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=tz)
    date_str = now.strftime("%Y-%m-%d")
    
    
    # 保存到数据库
    try:
        with Session(db.engine) as session:
            # 检查是否已存在相同日期的报告
            statement = select(Report).where(Report.date == date_str, Report.username==username)
            existing_report = session.exec(statement).first()
            
            if existing_report:
                existing_report.content = _content
                session.add(existing_report)
            else:
                new_report = Report(
                    date=date_str, 
                    content=_content,  # 确保完整内容被保存
                    username=username,
                    commit_log=commit_log  # 假设 commit_log 也是内容的一部分
                )
                session.add(new_report)
            
            session.commit()
    except Exception as e:
        logging.error(f"保存报告到数据库失败: {str(e)}")
        raise


def is_valid_git_repo(repo_path: str) -> bool:
    """验证路径是否为有效的 Git 仓库"""
    return Path(repo_path).is_dir() and (Path(repo_path) / ".git").is_dir()


def generate_report(username: str, session: db.SessionDep, target_date: str = None,):
    result = get_git_commits(username=username, session=session, target_date=target_date)
    content = generate_work_report(result)
    
    commit_log = "\n".join([f"{c['hash']} {c['message']}" for c in result]) if result else ''
    save_report(content, username=username, commit_log= commit_log, report_date=target_date)
