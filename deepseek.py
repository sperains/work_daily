import json
import logging
import os
import requests


def call_deepseek_api(prompt: str) -> str:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    # 验证 DEEPSEEK_API_KEY 是否存在
    if not DEEPSEEK_API_KEY:
        logging.error("DEEPSEEK_API_KEY 环境变量缺失或为空。")
        raise ValueError("DEEPSEEK_API_KEY environment variable is missing or empty.")

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
        "stream": True,
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
