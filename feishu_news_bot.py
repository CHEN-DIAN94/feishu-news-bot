#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书新闻机器人 - 每日自动发送今日排行前十新闻
功能：抓取新闻、比对历史、发送飞书卡片、更新状态
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests


# 配置常量
HISTORY_FILE = Path(__file__).parent / "news_history.json"
TOP_N = 10  # 只取前10条


def fetch_news() -> list[dict]:
    """
    获取今日新闻列表（模拟数据）
    实际使用时替换为真实的新闻 API 调用

    Returns:
        list[dict]: 包含 title 和 url 的字典列表
    """
    # TODO: 替换为真实新闻 API，例如：
    # response = requests.get("https://api.example.com/news")
    # return response.json()["data"]

    # 模拟数据 - 今日新闻（包含标题、链接和摘要）
    mock_news = [
        {
            "title": "中国成功发射新一代载人飞船试验船",
            "url": "https://example.com/news/1",
            "summary": "长征五号B运载火箭搭载新一代载人飞船试验船在海南文昌航天发射场成功升空，标志着中国载人航天工程进入新阶段。"
        },
        {
            "title": "全国高考成绩陆续公布，多地分数线出炉",
            "url": "https://example.com/news/2",
            "summary": "全国各省份高考成绩查询通道陆续开放，多省市已公布各批次录取分数线，考生可通过官方渠道查询。"
        },
        {
            "title": "人工智能技术在医疗领域取得重大突破",
            "url": "https://example.com/news/3",
            "summary": "最新研究表明，AI辅助诊断系统在早期癌症筛查中准确率超过95%，有望大幅提高疾病早期发现率。"
        },
        {
            "title": "新能源汽车销量创历史新高",
            "url": "https://example.com/news/4",
            "summary": "上月国内新能源汽车销量突破100万辆，同比增长45%，市场渗透率首次超过50%。"
        },
        {
            "title": "央行宣布降准0.5个百分点",
            "url": "https://example.com/news/5",
            "summary": "中国人民银行决定下调金融机构存款准备金率0.5个百分点，释放长期资金约1万亿元，支持实体经济发展。"
        },
        {
            "title": "国产大飞机C919首次商业飞行成功",
            "url": "https://example.com/news/6",
            "summary": "中国东方航空使用C919大型客机执飞上海虹桥-北京首都航线，圆满完成首次商业载客飞行任务。"
        },
        {
            "title": "全国多地迎来高温天气，部分地区超40℃",
            "url": "https://example.com/news/7",
            "summary": "中央气象台继续发布高温橙色预警，华北、黄淮等地最高气温将达38-40℃，局地超过40℃。"
        },
        {
            "title": "5G基站数量突破300万个",
            "url": "https://example.com/news/8",
            "summary": "工信部最新数据显示，我国已建成5G基站超过300万个，5G用户数突破8亿，网络规模全球领先。"
        },
        {
            "title": "教育部门发布新课标改革方案",
            "url": "https://example.com/news/9",
            "summary": "教育部印发新版义务教育课程方案，强化科学教育和工程教育，培养学生创新能力和实践能力。"
        },
        {
            "title": "我国科学家在量子计算领域取得新进展",
            "url": "https://example.com/news/10",
            "summary": "中国科学技术大学团队成功研制出超导量子计算原型机'祖冲之三号'，性能指标达到国际领先水平。"
        },
        {
            "title": "国际油价持续上涨，国内油价将调整",
            "url": "https://example.com/news/11",
            "summary": "受地缘政治因素影响，国际原油价格连续三周上涨，国内成品油价格预计下周将迎来年内第六次上调。"
        },
        {
            "title": "北京冬奥会遗产利用计划公布",
            "url": "https://example.com/news/12",
            "summary": "北京市发布冬奥遗产利用方案，国家体育场等场馆将向公众开放，并承办国际顶级赛事和文化活动。"
        },
    ]

    # 严格截取前10条
    return mock_news[:TOP_N]


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
    构建飞书互动卡片 - 新闻列表样式

    Args:
        news_list: 新闻列表，每个元素包含 title 和 url

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

    # 新闻列表
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
        print("[ERROR] 未找到环境变量 FEISHU_WEBHOOK")
        print("请设置环境变量：export FEISHU_WEBHOOK='https://open.feishu.cn/open-apis/bot/v2/hook/xxx'")
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
                print("[OK] 消息发送成功")
                return True
            else:
                print(f"[ERROR] 飞书返回错误：{result}")
                return False
        else:
            print(f"[ERROR] HTTP 请求失败，状态码：{response.status_code}")
            return False

    except requests.RequestException as e:
        print(f"[ERROR] 请求异常：{e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print(f"[BOT] 飞书新闻机器人启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 获取今日新闻（前10条）
    print("\n[NEWS] 正在获取今日新闻...")
    today_news = fetch_news()
    today_titles = [news["title"] for news in today_news]
    print(f"   获取到 {len(today_news)} 条新闻")

    # 2. 读取昨日历史记录
    print("\n[HISTORY] 正在读取历史记录...")
    yesterday_titles = load_history()
    print(f"   昨日记录：{len(yesterday_titles)} 条新闻")

    # 3. 比对逻辑
    print("\n[COMPARE] 正在比对新闻差异...")

    # 检查今天所有新闻是否都在昨天的记录中
    all_in_history = all(title in yesterday_titles for title in today_titles)

    if all_in_history and len(yesterday_titles) > 0:
        # 情况1：完全重复 - 今天与昨日新闻一样
        print("   结果：今天与昨日新闻完全相同")
        print("\n[SEND] 发送飞书卡片：今日与昨日新闻一样...")
        payload = build_feishu_card_same()
        send_to_feishu(payload)
    else:
        # 情况2：部分更新 - 过滤掉旧新闻，只发送新新闻
        new_news = [news for news in today_news if news["title"] not in yesterday_titles]
        print(f"   结果：发现 {len(new_news)} 条新新闻")

        if new_news:
            print("\n[SEND] 发送飞书卡片：新新闻列表...")
            payload = build_feishu_card_news(new_news)
            send_to_feishu(payload)
        else:
            # 理论上不会走到这里，但作为兜底
            print("   没有新新闻需要发送")

    # 4. 更新状态文件（无论哪种情况都要更新）
    print("\n[SAVE] 正在更新历史记录...")
    save_history(today_titles)
    print(f"   已保存 {len(today_titles)} 条新闻标题到 {HISTORY_FILE}")

    print("\n" + "=" * 50)
    print("[DONE] 任务完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
