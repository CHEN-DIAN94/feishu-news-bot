# 飞书新闻机器人

每日自动向飞书发送"今日排行前十新闻"的 Python 机器人，支持 GitHub Actions 云端自动运行。

## 功能特性

- 📰 自动抓取今日新闻（前10条）
- 🔍 智能比对昨日新闻，避免重复推送
- 📤 部分更新时只发送新新闻
- 💾 自动更新历史记录文件
- ⏰ GitHub Actions 每日定时运行（北京时间 9:00）

## 项目结构

```
feishu-news-bot/
├── feishu_news_bot.py      # 核心业务逻辑
├── requirements.txt        # Python 依赖
├── README.md              # 项目说明
└── .github/
    └── workflows/
        └── run_bot.yml    # GitHub Actions 配置
```

## 本地测试

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export FEISHU_WEBHOOK='https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址'

# 运行脚本
python feishu_news_bot.py
```

## GitHub Actions 配置

1. 在 GitHub 仓库的 Settings -> Secrets and variables -> Actions 中添加 Secret：
   - 名称：`FEISHU_WEBHOOK`
   - 值：飞书机器人的 Webhook 地址

2. 推送代码后，机器人会每天北京时间 9:00 自动运行

## 飞书 Webhook 获取方式

1. 打开飞书，进入目标群组
2. 点击群组设置 -> 群机器人 -> 添加机器人
3. 选择"自定义机器人"
4. 复制 Webhook 地址

## 发送逻辑

- **完全重复**：今天10条新闻与昨天完全相同 → 发送"今天与昨日新闻一样"
- **部分更新**：有新新闻出现 → 只发送新新闻列表
- **状态更新**：每次运行后都会更新 `news_history.json`

## 自定义新闻源

修改 `feishu_news_bot.py` 中的 `fetch_news()` 函数，接入真实的新闻 API。
