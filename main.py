import json
import os
from contextlib import asynccontextmanager
from typing import List
import requests
from fastapi import FastAPI
from git import Repo
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import logging
from pytz import timezone  # 用于处理时区
from fastapi.staticfiles import StaticFiles

import db

# 设置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 加载环境变量
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "reports")  # 存储月度报告的目录


# 验证 DEEPSEEK_API_KEY 是否存在
if not DEEPSEEK_API_KEY:
    logging.error("DEEPSEEK_API_KEY 环境变量缺失或为空。")
    raise ValueError("DEEPSEEK_API_KEY environment variable is missing or empty.")

def get_git_commits(_repos: List[str], days: int) -> List[dict]:
    """从多个仓库获取提交记录"""
    tz = timezone("Asia/Shanghai")  # 设置为东八区时区
    since_date = datetime.now(tz) - timedelta(days=days)
    all_commits: list = []
    for repo_path in _repos:
        if not is_valid_git_repo(repo_path):
            logging.warning(f"无效的 Git 仓库路径: {repo_path}")
            continue
        repo = Repo(path=repo_path)
        for commit in repo.iter_commits(since=since_date):
            if commit.author.name != "任OvO":
                continue  # 跳过非目标作者的提交
            all_commits.append(
                {
                    "hash": commit.hexsha[:7],
                    "author": commit.author.name,
                    "date": commit.committed_datetime.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
                    "message": commit.message.strip(),
                    "repo": os.path.basename(repo_path)  # 添加仓库名称
                }
            )
    return all_commits

def generate_work_report(commits: List[dict]) -> str:
    """使用 DeepSeek API 生成工作日报，并以流式方式输出"""
    if not commits:
        logging.info("今日无代码提交记录")
        return "今日无代码提交记录"
    # 构建 Commit 信息字符串
    commit_log = "\n".join([
        f"- [{c['hash']}] {c['message']} ({c['author']} @ {c['date']}) [{c['repo']}]"
        for c in commits
    ])
    # 构造提示词
    prompt = f"""
    你是一位资深技术主管，请根据以下 Git 提交记录生成一份专业的工作日报：
    要求：
    1. 按项目模块分类总结工作内容，无需展示 commit hash
    2. 识别技术难点和解决方案
    3. 使用 Markdown 格式输出
    今日提交记录：
    {commit_log}
    """
    logging.info("正在调用 DeepSeek API 生成工作日报...")
    logging.debug(f"提示词内容：\n{prompt}")
    # 调用 DeepSeek API
    report_content = call_deepseek_api(prompt)
    logging.info("\n**工作日报生成完毕**\n")
    return report_content

def save_report(_content: str):
    """保存日报到按月份的 Markdown 文件"""
    tz = timezone("Asia/Shanghai")  # 设置为东八区时区
    now = datetime.now(tz)
    year_month_dir = now.strftime("%Y-%m")
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    # 每月一个文件
    report_file = output_dir / f"{year_month_dir}.md"
    with open(report_file, "r+", encoding="utf-8") as f:
        content_lines = f.readlines()
        if any(now.strftime("%Y-%m-%d") in line for line in content_lines):
            logging.warning("今日报告已存在，跳过写入。")
            return
        if not content_lines:  # 如果文件为空，添加标题
            f.write(f"# 工作日报 - {year_month_dir}\n\n")
        # 写入每日内容
        f.write(f"## {now.strftime('%Y-%m-%d')}\n\n")

def is_valid_git_repo(repo_path: str) -> bool:
    """验证路径是否为有效的 Git 仓库"""
    return Path(repo_path).is_dir() and (Path(repo_path) / ".git").is_dir()

def call_deepseek_api(prompt: str) -> str:
    """调用 DeepSeek API 并返回生成的报告"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位技术主管，擅长从代码提交记录中分析开发工作内容"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
        "stream": True
    }
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"调用 DeepSeek API 失败: {e}")
        return "无法生成工作日报，请检查网络连接或 API 配置。"
    report_content = ""
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data:"):
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    print(delta, end="")
                    report_content += delta
            except json.JSONDecodeError:
                logging.warning("解析 JSON 数据失败，跳过此行。")
    return report_content

# if __name__ == "__main__":
#     repos = ["jd_word"]  # List of repository paths
#     result = get_git_commits(repos, days=1)
#     content = generate_work_report(result)
#     save_report(content)





@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/", StaticFiles(directory="static"), name="static")