from flask import Flask, request
from linebot import LineBotApi, WebhookParser
from linebot.models import TextSendMessage
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import pytz
import requests
# 載入 .env 檔案
load_dotenv()

# 建立 Flask 應用
app = Flask(__name__)

# 初始化 LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

tz = pytz.timezone("Asia/Taipei")

HOLIDAY_CACHE = {
    "date": None,
    "holidays": set()
}

def fetch_taiwan_holidays():
    """抓台灣官方國定假日（自動快取）"""

    global HOLIDAY_CACHE
    today = datetime.now(tz).date()

    # ✅ 今日已有快取 → 直接用
    if HOLIDAY_CACHE["date"] == today:
        return HOLIDAY_CACHE["holidays"]

    year = today.year
    url = f"https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"

    try:
        print(f"[INFO] Fetching Taiwan holidays for {year}")
        r = requests.get(url, timeout=5)
        r.raise_for_status()

        data = r.json()
        holidays = { datetime.strptime(day["date"], "%Y%m%d").date()
                     for day in data if day.get("isHoliday") }

        HOLIDAY_CACHE["date"] = today
        HOLIDAY_CACHE["holidays"] = holidays

        print(f"[INFO] Loaded {len(holidays)} holidays.")

        return holidays

    except Exception as e:
        print("[WARN] Failed to fetch holidays:", e)
        return HOLIDAY_CACHE["holidays"]   # fallback


def is_tw_holiday_or_weekend():
    """判斷台灣國定假日或週末"""

    now = datetime.now(tz)
    today = now.date()

    # ✅ 國定假日
    if today in fetch_taiwan_holidays():
        return True

    # ✅ 週末
    if now.weekday() >= 5:
        return True

    return False


# 首頁測試
@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

# 📡 用於接收 LINE webhook，抓取群組 ID
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    events = body.get("events", [])

    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_msg = event["message"]["text"].strip()

            if user_msg == "查詢目前狀態":
                if not device_status:
                    reply = "目前沒有任何狀態資料。"
                else:
                    msg_lines = ["📋 目前 廣播運作 狀態："]
                    for pin, val in device_status.items():
                        msg_lines.append(f"{pin}：{val}")
                    reply = "\n".join(msg_lines)

                line_bot_api.reply_message(
                    event["replyToken"],
                    TextSendMessage(text=reply)
                )

    return "OK"

# 📟 提供 ESP8266 使用的路由，收到後發送 LINE 通知
@app.route("/alert", methods=["POST"])
def alert():
    try:
        data = request.get_json()
        pin = data.get("pin")
        status = data.get("status")
        # 取得當下 UTC 時間
        utc_now = datetime.now(pytz.utc)
        taipei_tz = pytz.timezone('Asia/Taipei')
        taipei_time = utc_now.astimezone(taipei_tz)
        time_str = taipei_time.strftime("%Y-%m-%d %H:%M:%S")
        msg = f"🔴🔴🔴🔴🔴 {pin}‼️‼️‼️‼️\n設備：{pin}\n狀態：{status}\n🕒 時間：{time_str}"
        if is_tw_holiday_or_weekend():
            line_bot_api.push_message(LINE_GROUP_ID, TextSendMessage(text=msg))
        else:
            print("[INFO] 平日接收到 ESP 訊號，但不發 LINE")
        return "通知已發送", 200
    except Exception as e:
        print("錯誤:", e)
        return "錯誤", 500
        

@app.route("/ping", methods=["POST"])
def ping():
    return {"message": "pong"}, 200

# Flask 啟動點（本地測試用）
if __name__ == "__main__":
    app.run(debug=True)
