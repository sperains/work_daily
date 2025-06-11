import os
import subprocess
from pathlib import Path
from typing import List

LOCAL_REPO_DIR = os.getenv('LOCAL_REPO_DIR', '.localrepo')


def get_repo_local_path(repo_url: str) -> str:
    """获取本地仓库路径"""
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    return str(Path(LOCAL_REPO_DIR) / repo_name)

def clone_repos(repo_urls: List[str]) -> None:
    """下载所有仓库到本地目录"""
    Path(LOCAL_REPO_DIR).mkdir(parents=True, exist_ok=True)
    
    for repo_url in repo_urls:
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_path = Path(LOCAL_REPO_DIR) / repo_name
        
        if repo_path.exists():
            print(f"仓库 {repo_name} 已存在，跳过下载")
            continue
            
        print(f"正在下载仓库: {repo_name}")
        try:
            subprocess.run(['git', 'clone', repo_url, str(repo_path)], check=True)
            print(f"成功下载仓库: {repo_name}")
        except subprocess.CalledProcessError as e:
            print(f"下载仓库 {repo_name} 失败: {e}")
