# 加载环境变量
from datetime import datetime, timedelta
import logging
import os
from pathlib import Path
from typing import List

from git import Repo
from pytz import timezone

from deepseek import call_deepseek_api

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "reports")  # 存储月度报告的目录

# 设置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_git_commits(_repos: List[str], days: int = None, target_date: str = None) -> List[dict]:
    """从多个仓库获取提交记录
    Args:
        _repos: 仓库路径列表
        days: 过去多少天的提交(与target_date二选一)
        target_date: 指定日期(格式: YYYY-MM-DD)
    """
    tz = timezone("Asia/Shanghai")
    
    # 处理日期参数
    if target_date:
        since_date = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=tz)
        until_date = since_date + timedelta(days=1)
    else:
        since_date = datetime.now(tz) - timedelta(days=days or 1)
        until_date = datetime.now(tz)
    
    all_commits: list = []
    for repo_path in _repos:
        if not is_valid_git_repo(repo_path):
            logging.warning(f"无效的 Git 仓库路径: {repo_path}")
            continue
        repo = Repo(path=repo_path)
        for commit in repo.iter_commits(since=since_date, until=until_date):
            if commit.author.name != "任OvO":
                continue
            all_commits.append({
                "hash": commit.hexsha[:7],
                "author": commit.author.name,
                "date": commit.committed_datetime.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                "message": commit.message.strip(),
                "repo": os.path.basename(repo_path)
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

    # 构造提示词
    prompt = f"""
    你是一位资深技术主管，请根据以下 Git 提交记录生成一份专业的工作日报：
    要求：
    1. 按项目分类总结工作内容
    2. 识别技术难点和解决方案
    3. 不需要明日工作计划
    4. 不适用markdown, 以易于阅读的格式输出
    今日提交记录：
    {commit_log}
    """
    logging.info("\n\n正在调用 DeepSeek API 生成工作日报...")
    logging.debug(f"提示词内容：\n{prompt}")
    # 调用 DeepSeek API
    report_content = call_deepseek_api(prompt)
    logging.info("\n**工作日报生成完毕**\n")
    return report_content


def save_report(_content: str, report_date: str = None):
    tz = timezone("Asia/Shanghai")
    now = datetime.now(tz) if not report_date else datetime.strptime(report_date, "%Y-%m-%d").replace(tzinfo=tz)
    year_month_dir = now.strftime("%Y-%m")
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = output_dir / f"{year_month_dir}.txt"
    
    # 读取现有内容
    with open(report_file, "a+", encoding="utf-8") as f:
        f.seek(0)
        content_lines = f.readlines()
    
    # 分割内容为日期块
    date_blocks = []
    current_block = []
    for line in content_lines:
        if line.startswith("## "):
            if current_block:  # 保存前一个块
                date_blocks.append(current_block)
            current_block = [line]  # 开始新块
        else:
            current_block.append(line)
    if current_block:  # 添加最后一个块
        date_blocks.append(current_block)
    
    # 准备新内容块
    new_block = [f"## {now.strftime("%Y-%m-%d")}\n\n", _content + "\n\n"]
    
    # 按日期排序插入新块
    inserted = False
    for i, block in enumerate(date_blocks):
        if block[0].startswith("## "):
            block_date_str = block[0][3:].strip()
            try:
                # Make both datetimes timezone-aware for comparison
                block_date = datetime.strptime(block_date_str, "%Y-%m-%d").replace(tzinfo=tz)
                if now > block_date:
                    date_blocks.insert(i, new_block)
                    inserted = True
                    break
            except ValueError:
                pass
    
    if not inserted:
        date_blocks.append(new_block)
    
    # 重新组合内容
    new_content = []
    
    for block in date_blocks:
        new_content.extend(block)
    
    # 写入文件
    with open(report_file, "w", encoding="utf-8") as f:
        f.writelines(new_content)


def is_valid_git_repo(repo_path: str) -> bool:
    """验证路径是否为有效的 Git 仓库"""
    return Path(repo_path).is_dir() and (Path(repo_path) / ".git").is_dir()


def generate_report(target_date: str = None  ):
    repos = ["/Users/sperains/jd/jd_word"]  # List of repository paths
    
    result = get_git_commits(repos, target_date=target_date) if target_date else get_git_commits(repos, days=1)
    content = generate_work_report(result)
    save_report(content, report_date=target_date)
