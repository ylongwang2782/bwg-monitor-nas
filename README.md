# BWG Stock Monitor for NAS

搬瓦工 CN2 GIA-E 套餐库存监控工具 - NAS 部署版

直接从搬瓦工官网检测库存，有货时通过 Telegram/Bark 发送通知。

## Features

- ✅ Direct monitoring from BWH official site (一手数据)
- ✅ Telegram & Bark notifications
- ✅ Smart notification (only notify on status change)
- ✅ Daily stock report
- ✅ Suitable for 24/7 NAS deployment
- ✅ No external dependencies (pure Python 3 stdlib)

## Monitored Products

| Product | Price | Specs |
|---------|-------|-------|
| CN2 GIA-E 10G | $49.99/year | 10G SSD / 0.5G RAM / 1Gbps |
| CN2 GIA-E 20G | $89.99/year | 20G SSD / 1G RAM / 1Gbps |
| CN2 GIA-E 20G | $89.90/year | 20G SSD / 1G RAM / 2.5Gbps |

## Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/ylongwang2782/bwg-monitor-nas.git
cd bwg-monitor-nas
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

Set up your notification credentials:

- **Telegram**: Get bot token from [@BotFather](https://t.me/BotFather)
- **Bark** (optional): Get key from Bark iOS app

### 3. Start with Docker Compose

```bash
docker compose up -d
```

That's it! The monitor is now running.

### Common Docker Commands

```bash
# View logs
docker compose logs -f

# Stop monitor
docker compose down

# Restart monitor
docker compose restart

# Check status
docker compose ps

# Rebuild after code changes
docker compose up -d --build
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | (required) | Telegram bot token |
| `TELEGRAM_CHAT_ID` | (required) | Telegram chat ID |
| `BARK_KEY` | (optional) | Bark key for iOS push |
| `CHECK_INTERVAL` | `180` | Check interval in seconds (default 3 min) |
| `DAILY_REPORT_HOUR` | `12` | Daily report hour in Beijing time |

---

## Alternative Deployment Options

### Option 1: Cron (For NAS without Docker)

Works on Synology, QNAP, and most Linux-based NAS systems.

```bash
# Edit crontab
crontab -e
```

Add the following lines:

```cron
# Check stock every 3 minutes
*/3 * * * * cd /path/to/bwg-monitor-nas && /bin/bash -c 'source .env && /usr/bin/python3 monitor.py' >> /path/to/logs/monitor.log 2>&1

# Daily report at 12:00 Beijing time (04:00 UTC)
0 4 * * * cd /path/to/bwg-monitor-nas && /bin/bash -c 'source .env && /usr/bin/python3 monitor.py --daily-report' >> /path/to/logs/monitor.log 2>&1
```

**Note**: Replace `/path/to/bwg-monitor-nas` with your actual path.

### Option 2: Systemd Timer

Create `/etc/systemd/system/bwg-monitor.service`:

```ini
[Unit]
Description=BWG Stock Monitor
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/bwg-monitor-nas
EnvironmentFile=/path/to/bwg-monitor-nas/.env
ExecStart=/usr/bin/python3 /path/to/bwg-monitor-nas/monitor.py
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/bwg-monitor.timer`:

```ini
[Unit]
Description=BWG Stock Monitor Timer
Requires=bwg-monitor.service

[Timer]
OnBootSec=1min
OnUnitActiveSec=3min
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bwg-monitor.timer
sudo systemctl start bwg-monitor.timer

# Check status
sudo systemctl status bwg-monitor.timer
```

### Option 3: Synology Task Scheduler

1. Open **Control Panel** → **Task Scheduler**
2. Create → **Scheduled Task** → **User-defined script**
3. General:
   - Task: BWG Stock Monitor
   - User: your_user
4. Schedule:
   - Repeat: Every 3 minutes (or custom)
5. Task Settings:
   ```bash
   cd /volume1/your/path/bwg-monitor-nas
   source .env
   /usr/bin/python3 monitor.py
   ```

## Configuration

### Environment Variables

Edit `.env` file:

```bash
# Telegram Bot Token (required)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Telegram Chat ID (required)
TELEGRAM_CHAT_ID=123456789

# Bark Key (optional, for iOS push)
BARK_KEY=your_bark_key
```

### Customize Monitored Products

Edit `monitor.py` and modify the `PRODUCTS` list:

```python
PRODUCTS = [
    {"pid": 94,  "name": "CN2 GIA-E 10G", "price": "49.99", "desc": "10G SSD / 0.5G RAM / 1Gbps"},
    # Add more products here
]
```

Find product IDs (pid) from BWH official site URLs.

## Logs and Monitoring

### View Logs

```bash
# If using cron
tail -f /path/to/logs/monitor.log

# If using systemd
journalctl -u bwg-monitor -f
```

### Check State File

The script maintains a state file (`.stock_state.json`) to track notification history:

```bash
cat .stock_state.json
```

## Troubleshooting

### No Notifications Received

1. Check environment variables are loaded:
   ```bash
   source .env && echo $TELEGRAM_BOT_TOKEN
   ```

2. Test Telegram manually:
   ```bash
   curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     -d "chat_id=${TELEGRAM_CHAT_ID}" \
     -d "text=Test message"
   ```

3. Check logs for errors

### Cron Not Running

1. Check cron service is running:
   ```bash
   # Synology
   synoservicectl --status crond

   # Other Linux
   systemctl status cron
   ```

2. Verify crontab:
   ```bash
   crontab -l
   ```

3. Check absolute paths in cron command

### Python Version

Requires Python 3.6+. Check your version:

```bash
python3 --version
```

## Standalone Usage (Without Docker)

```bash
# Single check
source .env
python3 monitor.py

# Send daily report
python3 monitor.py --daily-report

# Run in daemon mode (like Docker does)
python3 monitor.py --daemon
```

## License

MIT

## Related Projects

- [bwg-monitor-github](https://github.com/ylongwang2782/bwg-monitor-github) - GitHub Actions version
