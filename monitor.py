#!/usr/bin/env python3
"""
BWG Stock Monitor - Standalone version for NAS deployment
搬瓦工库存监控 - NAS 部署独立版本
"""

import os
import sys
import urllib.request
import urllib.parse
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configuration / 配置
PRODUCTS = [
    {"pid": 94,  "name": "CN2 GIA-E 10G", "price": "49.99", "desc": "10G SSD / 0.5G RAM / 1Gbps"},
    {"pid": 105, "name": "CN2 GIA-E 20G", "price": "89.99", "desc": "20G SSD / 1G RAM / 1Gbps"},
    {"pid": 132, "name": "CN2 GIA-E 20G", "price": "89.90", "desc": "20G SSD / 1G RAM / 2.5Gbps"},
]

BWH_URL = "https://bwh81.net/cart.php?a=add&pid={pid}"

# State file to track what we've notified about
STATE_FILE = Path(__file__).parent / ".stock_state.json"


def load_state():
    """Load previous notification state"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
    return {}


def save_state(state):
    """Save notification state"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save state file: {e}")


def check_stock(pid):
    """Check stock directly from BWH official site"""
    url = BWH_URL.format(pid=pid)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Out of stock page contains "Out of Stock"
            if "Out of Stock" in html:
                return False
            # In stock page contains pricing info
            if "Annually" in html or "Monthly" in html:
                return True
            return False
    except Exception as e:
        print(f"  Error checking PID {pid}: {e}")
        return None


def send_telegram(text):
    """Send Telegram notification"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true"
    }).encode()

    try:
        urllib.request.urlopen(url, data, timeout=10)
        print("  ✅ Telegram notification sent")
        return True
    except Exception as e:
        print(f"  ❌ Telegram failed: {e}")
        return False


def send_bark(title, message):
    """Send Bark notification (for iOS)"""
    key = os.environ.get("BARK_KEY")
    if not key:
        return False

    url = f"https://api.day.app/{key}/{urllib.parse.quote(title)}/{urllib.parse.quote(message)}?sound=minuet&level=timeSensitive"
    try:
        urllib.request.urlopen(url, timeout=10)
        print("  ✅ Bark notification sent")
        return True
    except Exception as e:
        print(f"  ❌ Bark failed: {e}")
        return False


def format_time():
    """Get current time in Beijing timezone"""
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")


def daily_report(results):
    """Send daily stock report"""
    now = format_time()

    lines = [
        "📊 *BWG CN2 GIA-E Daily Stock Report*",
        f"⏰ {now} Beijing Time",
        "📡 Source: Official Site Direct",
        ""
    ]

    for p in results:
        if p["in_stock"] is True:
            icon = "🟢 In Stock"
        elif p["in_stock"] is False:
            icon = "🔴 Out of Stock"
        else:
            icon = "⚠️ Unknown"

        url = f"https://bwh81.net/cart.php?a=add&pid={p['pid']}"
        lines.append(f"{icon} *${p['price']}/year* - {p['name']}")
        lines.append(f"   {p['desc']}")
        lines.append(f"   [View Details]({url})")
        lines.append("")

    lines.append("_Auto-check every few minutes, instant notification when in stock_")
    send_telegram("\n".join(lines))
    print(f"\n✅ Daily report sent at {now}")


def main():
    """Main monitoring function"""
    is_daily_report = len(sys.argv) > 1 and sys.argv[1] == "--daily-report"

    print("=" * 60)
    print(f"BWG Official Site Stock Monitor | {format_time()}")
    print("=" * 60)

    results = []
    in_stock = []
    state = load_state()

    for p in PRODUCTS:
        pid = p["pid"]
        print(f"\nChecking PID {pid} ({p['name']})...")

        stock = check_stock(pid)
        p["in_stock"] = stock
        results.append(p)

        if stock is True:
            print(f"  🟢 In Stock! ${p['price']}/year")
            in_stock.append(p)
        elif stock is False:
            print(f"  🔴 Out of Stock")
        else:
            print(f"  ⚠️ Check Failed")

        # Avoid too many requests
        time.sleep(1)

    # Send daily report
    if is_daily_report:
        daily_report(results)
    # Send notification for newly in-stock items
    elif in_stock:
        for p in in_stock:
            pid_key = str(p['pid'])

            # Only notify if this is a new stock (not previously notified)
            if not state.get(pid_key, {}).get('notified'):
                url = f"https://bwh81.net/cart.php?a=add&pid={p['pid']}"
                message = f"🎉 *BWG Back in Stock!*\n\n"
                message += f"*{p['name']}*\n"
                message += f"💰 ${p['price']}/year\n"
                message += f"📦 {p['desc']}\n"
                message += f"🔗 [Buy Now]({url})\n\n"
                message += "_Source: Official Site Direct_"

                send_telegram(message)
                send_bark("BWG In Stock!", f"{p['name']} ${p['price']}/year")
                print(f"\n🎉 Stock notification sent: {p['name']}")

                # Mark as notified
                state[pid_key] = {
                    'notified': True,
                    'timestamp': format_time()
                }

        save_state(state)
    else:
        print("\nNo stock available")

        # Reset notification state for out-of-stock items
        for p in results:
            pid_key = str(p['pid'])
            if p['in_stock'] is False and pid_key in state:
                state[pid_key]['notified'] = False

        save_state(state)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
