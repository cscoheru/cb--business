# 通知服务配置说明

## 支持的通知渠道

### 1. Telegram Bot (推荐)

**优点**: 实时、免费、支持富文本

**设置步骤**:

1. 创建Telegram Bot:
   - 在Telegram中搜索 @BotFather
   - 发送 `/newbot` 创建bot
   - 获取Bot Token (如: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)

2. 获取Chat ID:
   - 在Telegram中搜索 @userinfobot
   - 发送任意消息获取你的Chat ID (如: `123456789`)

3. 配置环境变量:
```bash
# 在HK服务器上添加到环境变量或docker-compose.yml
TELEGRAM_BOT_TOKEN=你的bot_token
TELEGRAM_CHAT_ID=你的chat_id
```

4. 测试通知:
```bash
curl -X POST "https://api.telegram.org/bot<token>/sendMessage" \
  -d "chat_id=<chat_id>&text=Test from CB-Business"
```

---

### 2. 邮件通知

**优点**: 详细记录、支持附件、适合报告

**设置步骤**:

1. 使用SMTP服务 (Gmail示例):
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com
TO_EMAILS=recipient1@example.com,recipient2@example.com
```

2. Gmail应用专用密码:
   - 访问 https://myaccount.google.com/apppasswords
   - 生成应用专用密码
   - 使用该密码作为 `SMTP_PASS`

---

### 3. WhatsApp (Twilio)

**优点**: 到达率高、适合重要告警

**设置步骤**:

1. 注册Twilio账号:
   - 访问 https://www.twilio.com/
   - 创建免费试用账号

2. 设置WhatsApp Sandbox:
   - 在Twilio控制台启用WhatsApp
   - 获取 `Account SID` 和 `Auth Token`
   - 加入WhatsApp Sandbox (发送 `join<keyword>` 到给定号码)

3. 配置环境变量:
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
WHATSAPP_FROM_NUMBER=+14155238886  # Twilio Sandbox号码
WHATSAPP_TO_NUMBER=+861xxxxxxxxxx  # 你的手机号
```

---

## 环境变量配置

在HK服务器上的 `docker-compose.yml` 或环境变量文件中添加:

```yaml
version: '3.8'
services:
  cb-business-api:
    environment:
      # Telegram通知
      TELEGRAM_BOT_TOKEN: "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
      TELEGRAM_CHAT_ID: "123456789"

      # 邮件通知
      SMTP_HOST: "smtp.gmail.com"
      SMTP_PORT: "587"
      SMTP_USER: "your-email@gmail.com"
      SMTP_PASS: "your-app-password"
      FROM_EMAIL: "your-email@gmail.com"
      TO_EMAILS: "recipient1@example.com,recipient2@example.com"

      # WhatsApp通知 (可选)
      TWILIO_ACCOUNT_SID: "your_account_sid"
      TWILIO_AUTH_TOKEN: "your_auth_token"
      WHATSAPP_FROM_NUMBER: "+14155238886"
      WHATSAPP_TO_NUMBER: "+861xxxxxxxxxx"
```

---

## 使用示例

### 在监控脚本中集成通知

```python
from services.notification_service import send_monitoring_report

# 在监控脚本中
report = await monitor.generate_report()

# 发送通知到所有配置的渠道
await send_monitoring_report(report)
```

### 发送自定义通知

```python
from services.notification_service import send_notification, NotificationPriority

# 发送普通通知
await send_notification(
    title="OpenClaw执行完成",
    message="RSS Crawler成功采集50篇文章",
    priority=NotificationPriority.INFO
)

# 发送错误告警
await send_notification(
    title="OpenClaw执行失败",
    message="RSS Crawler超时，请检查",
    priority=NotificationPriority.ERROR
)
```

### OpenClaw Channel中集成通知

```javascript
// 在OpenClaw Channel中
async function run(params) {
    try {
        const result = await fetchData();

        // 发送成功通知 (通过FastAPI)
        await fetch('http://172.22.0.4:8000/api/v1/notifications/notify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: '✅ OpenClaw执行成功',
                message: '成功采集 ' + result.count + ' 篇文章',
                priority: 'info'
            })
        });

        return result;
    } catch (error) {
        // 发送错误通知
        await fetch('http://172.22.0.4:8000/api/v1/notifications/notify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: '❌ OpenClaw执行失败',
                message: error.message,
                priority: 'error',
                context: 'RSS Crawler'
            })
        });

        throw error;
    }
}
```

---

## 通知路由创建

创建 `backend/api/notifications.py`:

```python
from fastapi import APIRouter
from services.notification_service import send_notification, NotificationPriority

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.post("/notify")
async def send_notification_endpoint(
    title: str,
    message: str,
    priority: str = "info",
    context: str = ""
):
    """统一通知接口"""
    priority_map = {
        "info": NotificationPriority.INFO,
        "warning": NotificationPriority.WARNING,
        "error": NotificationPriority.ERROR,
        "critical": NotificationPriority.CRITICAL
    }

    await send_notification(
        title=title,
        message=f"{context}\n\n{message}" if context else message,
        priority=priority_map.get(priority, NotificationPriority.INFO)
    )

    return {"success": True}
```

---

## 快速开始

### 最简配置 (仅Telegram)

1. 创建Telegram Bot并获取token和chat_id
2. 在HK服务器设置环境变量
3. 重启API容器

```bash
# 设置环境变量
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 重启容器
docker restart cb-business-api-fixed
```

### 完整配置 (Telegram + Email + WhatsApp)

1. 配置所有服务的凭据
2. 添加到docker-compose.yml
3. 重启服务

---

## 测试通知

```bash
# 测试Telegram通知
curl -X POST "https://api.zenconsult.top/api/v1/notifications/notify" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试通知",
    "message": "这是一条测试消息",
    "priority": "info"
  }'
```

---

## 故障排除

### Telegram通知不工作
- 检查Bot Token是否正确
- 确认Bot已启动（发送/start给bot）
- 检查Chat ID是否正确
- 查看API日志

### 邮件发送失败
- Gmail: 使用应用专用密码，不是账户密码
- 检查SMTP端口和加密设置
- 确认发件人邮箱已启用

### WhatsApp通知失败
- 确认Twilio账号状态正常
- 检查Sandbox设置
- 验证目标号码已加入Sandbox
- 查看Twilio日志
