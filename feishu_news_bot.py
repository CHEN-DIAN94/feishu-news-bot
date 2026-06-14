#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书新闻机器人 - 每日自动发送今日排行前十新闻
功能：抓取新闻、比对历史、发送飞书卡片、更新状态
特性：主备容灾、异常拦截、精美排版
"""

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 配置常量
HISTORY_FILE = Path(__file__).parent / "news_history.json"
TOP_N = 10  # 只取前10条

# 请求头配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_news_primary() -> list[dict]:
    """
    主渠道：调用免费API获取36氪全网热榜
    接口地址：https://api.vvhan.com/api/hotlist/36Ke

    Returns:
        list[dict]: 包含 title, url, summary 的字典列表，失败返回 []
    """
    try:
        logger.info("[主渠道] 正在调用 vvhan 36氪 API...")
        response = requests.get(
            "https://api.vvhan.com/api/hotlist/36Ke",
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:
            logger.warning(f"[主渠道] HTTP请求失败，状态码: {response.status_code}")
            return []

        data = response.json()

        # 检查API返回状态
        if not data.get("success", False):
            logger.warning(f"[主渠道] API返回失败: {data}")
            return []

        news_list = []
        for item in data.get("data", []):
            news_list.append({
                "title": item.get("title", ""),
                "url": item.get("url", item.get("mobilUrl", "")),
                "summary": item.get("desc", "暂无摘要")
            })

        logger.info(f"[主渠道] 成功获取 {len(news_list)} 条新闻")
        return news_list

    except Exception as e:
        logger.error(f"[主渠道] 请求异常: {e}")
        return []


def fetch_news_fallback() -> list[dict]:
    """
    备用渠道：解析36氪RSS订阅源
    地址：https://36kr.com/feed

    Returns:
        list[dict]: 包含 title, url, summary 的字典列表，失败返回 []
    """
    try:
        logger.info("[备用渠道] 正在解析36氪RSS订阅源...")
        feed = feedparser.parse("https://36kr.com/feed")

        if feed.bozo and not feed.entries:
            logger.warning(f"[备用渠道] RSS解析失败: {feed.bozo_exception}")
            return []

        news_list = []
        for entry in feed.entries[:TOP_N]:
            title = entry.get("title", "").strip()
            url = entry.get("link", "")

            # 提取并清理摘要中的HTML标签
            summary_raw = entry.get("summary", entry.get("description", ""))
            if summary_raw:
                # 使用BeautifulSoup清理HTML标签
                summary_text = BeautifulSoup(summary_raw, "html.parser").get_text()
                # 清理多余空白字符
                summary = re.sub(r'\s+', ' ', summary_text).strip()
                # 截取前100字符避免过长
                if len(summary) > 100:
                    summary = summary[:100] + "..."
            else:
                summary = "暂无摘要"

            if title:
                news_list.append({
                    "title": title,
                    "url": url,
                    "summary": summary
                })

        logger.info(f"[备用渠道] 成功获取 {len(news_list)} 条新闻")
        return news_list

    except Exception as e:
        logger.error(f"[备用渠道] 请求异常: {e}")
        return []


def fetch_news() -> list[dict]:
    """
    总控函数：主备容灾获取新闻
    优先使用主渠道，失败则切换备用渠道

    Returns:
        list[dict]: 包含 title, url, summary 的字典列表（最多 TOP_N 条）
    """
    # 优先调用主渠道
    news_list = fetch_news_primary()

    # 主渠道失败，切换备用渠道
    if not news_list:
        logger.warning("=" * 50)
        logger.warning("[WARNING] 主渠道获取失败，正在切换备用渠道...")
        logger.warning("=" * 50)
        news_list = fetch_news_fallback()

    # 严格截取前10条
    return news_list[:TOP_N]


def build_feishu_card_alert(message: str) -> dict:
    """
    构建飞书告警卡片（红色主题）

    Args:
        message: 告警信息

    Returns:
        dict: 飞书卡片 JSON
    """
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "⚠️ 系统告警"
                },
                "template": "red"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**{message}**"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"告警时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }


def load_history() -> list[str]:
    """
    读取历史记录文件，获取昨日的前十名新闻标题列表

    Returns:
        list[str]: 昨日新闻标题列表，如果文件不存在则返回空列表
    """
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("titles", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_history(titles: list[str]) -> None:
    """
    保存今日新闻标题到历史记录文件

    Args:
        titles: 今日新闻标题列表
    """
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "titles": titles
    }

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_feishu_card_news(news_list: list[dict]) -> dict:
    """
    构建飞书互动卡片 - 新闻列表样式（带摘要）

    Args:
        news_list: 新闻列表，每个元素包含 title, url, summary

    Returns:
        dict: 飞书卡片 JSON
    """
    elements = []

    # 标题
    elements.append({
        "tag": "markdown",
        "content": "**📰 今日排行前十新闻（更新部分）**"
    })

    elements.append({"tag": "hr"})

    # 新闻列表（带摘要）
    for i, news in enumerate(news_list, 1):
        summary = news.get('summary', '暂无摘要')
        elements.append({
            "tag": "markdown",
            "content": f"**{i}.** [{news['title']}]({news['url']})\n<font color='grey'>{summary}</font>"
        })

    elements.append({"tag": "hr"})

    # 底部时间戳
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ]
    })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "🚀 今日新闻速递"
                },
                "template": "blue"
            },
            "elements": elements
        }
    }


def build_feishu_card_same() -> dict:
    """
    构建飞书互动卡片 - 今日与昨日新闻相同

    Returns:
        dict: 飞书卡片 JSON
    """
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📋 今日新闻速递"
                },
                "template": "grey"
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": "今天与昨日新闻一样，没有新内容更新。"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }


def send_to_feishu(payload: dict) -> bool:
    """
    发送消息到飞书 Webhook

    Args:
        payload: 飞书消息体

    Returns:
        bool: 发送是否成功
    """
    webhook_url = os.environ.get("FEISHU_WEBHOOK")

    if not webhook_url:
        logger.error("未找到环境变量 FEISHU_WEBHOOK")
        logger.error("请设置环境变量：export FEISHU_WEBHOOK='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'")
        sys.exit(1)

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                logger.info("[OK] 消息发送成功")
                return True
            else:
                logger.error(f"飞书返回错误：{result}")
                return False
        else:
            logger.error(f"HTTP 请求失败，状态码：{response.status_code}")
            return False

    except requests.RequestException as e:
        logger.error(f"请求异常：{e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info(f"飞书新闻机器人启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # 1. 获取今日新闻（前10条）
    logger.info("\n正在获取今日新闻...")
    today_news = fetch_news()

    # 异常拦截：两个渠道均失败
    if not today_news:
        logger.error("=" * 50)
        logger.error("[CRITICAL] 所有数据源获取失败，今日新闻为空！")
        logger.error("=" * 50)

        # 发送告警卡片
        alert_payload = build_feishu_card_alert("API获取异常，今日暂不更新历史记录")
        send_to_feishu(alert_payload)

        # 终止后续流程，保护历史记录
        logger.info("已发送告警通知，跳过历史记录更新，程序退出。")
        sys.exit(0)

    today_titles = [news["title"] for news in today_news]
    logger.info(f"获取到 {len(today_news)} 条新闻")

    # 2. 读取昨日历史记录
    logger.info("\n正在读取历史记录...")
    yesterday_titles = load_history()
    logger.info(f"昨日记录：{len(yesterday_titles)} 条新闻")

    # 3. 比对逻辑
    logger.info("\n正在比对新闻差异...")

    # 检查今天所有新闻是否都在昨天的记录中
    all_in_history = all(title in yesterday_titles for title in today_titles)

    if all_in_history and len(yesterday_titles) > 0:
        # 情况1：完全重复 - 今天与昨日新闻一样
        logger.info("结果：今天与昨日新闻完全相同")
        logger.info("\n发送飞书卡片：今日与昨日新闻一样...")
        payload = build_feishu_card_same()
        send_to_feishu(payload)
    else:
        # 情况2：部分更新 - 过滤掉旧新闻，只发送新新闻
        new_news = [news for news in today_news if news["title"] not in yesterday_titles]
        logger.info(f"结果：发现 {len(new_news)} 条新新闻")

        if new_news:
            logger.info("\n发送飞书卡片：新新闻列表...")
            payload = build_feishu_card_news(new_news)
            send_to_feishu(payload)
        else:
            # 理论上不会走到这里，但作为兜底
            logger.info("没有新新闻需要发送")

    # 4. 更新状态文件（无论哪种情况都要更新）
    logger.info("\n正在更新历史记录...")
    save_history(today_titles)
    logger.info(f"已保存 {len(today_titles)} 条新闻标题到 {HISTORY_FILE}")

    logger.info("\n" + "=" * 50)
    logger.info("任务完成！")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
