# mcCheck

小木虫论坛 (https://muchong.com/bbs/) 每日自动签到项目，通过 GitHub Actions 每小时自动运行。

## 功能

1. **每小时自动运行**：GitHub Actions 通过 cron 调度，每小时运行两次 `mc.py`。
2. **账号密码走 Secret**：`mc.py` 从环境变量读取账号密码，由仓库 Secret 注入，不写死在代码里。
3. **避免重复签到**：每次运行优先读取 `log.txt`，如果今天已经签到成功则直接退出，不再请求网站。
4. **日志同步回仓库**：正常签到时，把更新后的 `log.txt` 提交回仓库，供下次运行读取。
5. **Telegram 通知**：签到成功后通过 Telegram Bot API 推送一条美化过的消息；token 与接收目标也走 Secret。

## 使用方法

### 1. 添加仓库 Secrets

进入仓库 **Settings → Secrets and variables → Actions → New repository secret**，添加以下 Secret：

| Secret 名称              | 值                                   |
| ------------------------ | ------------------------------------ |
| `USERNAME`               | 小木虫账号                           |
| `PASSWORD`               | 小木虫密码                           |
| `TG_BOT_TOKEN`           | Telegram Bot 的 token                |
| `TG_CHAT_ID`             | 接收通知的 Telegram chat id          |

如何获取 Telegram 参数：

- 在 Telegram 里找 `@BotFather` 创建/取回一个机器人，得到 `TG_BOT_TOKEN`。
- 把 `TG_CHAT_ID` 设为想接收通知的目标。若发给某个用户，就是该用户的数字 id；
  发给群组则是 `-100xxxxxxxxxx` 形式。可在与机器人对话后通过
  `https://api.telegram.org/bot<TG_BOT_TOKEN>/getUpdates` 查看消息的 `chat.id`。

### 2. 推送代码

把 `.github/workflows/checkin.yml` 和修改后的 `mc.py`、`log.txt` 推送到仓库，工作流会自动按计划运行。

### 3. 手动触发（可选）

在 **Actions → 每日签到 → Run workflow** 手动运行一次，验证签到流程是否正常。

## 工作流程说明

- 每次运行先读取 `log.txt`，若其中记录了「今天已经签到成功」则直接退出（退出码 0，不修改 `log.txt`）。
- 否则执行登录 + 签到，并把结果写入 `log.txt`。
- 签到成功（退出码 0）时，Actions 将更新后的 `log.txt` 提交并推回仓库；
  签到失败（退出码 1）时不做提交，下次运行会重试。

> 调度基于 GitHub Actions 的 UTC 时区；私有仓库若长期无人活跃，GitHub 可能暂停定时任务。