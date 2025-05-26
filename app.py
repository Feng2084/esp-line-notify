from flask import Flask, request
from linebot import LineBotApi, WebhookParser
from linebot.models import TextSendMessage
from dotenv import load_dotenv
import os
import json
from datetime import datetime
# 載入 .env 檔案
load_dotenv()

# 建立 Flask 應用
app = Flask(__name__)

# 初始化 LINE Bot
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

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
                    reply = "目前沒有任何裝置狀態資料。"
                else:
                    msg_lines = ["📋 目前 ESP8266 腳位狀態："]
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
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = f"🔴🔴🔴🔴🔴 偵測器觸發‼️‼️‼️‼️\n設備：{pin}\n狀態：{status}\n🕒 時間：{time_str}"
        line_bot_api.push_message(LINE_GROUP_ID, TextSendMessage(text=msg))
        return "通知已發送", 200
    except Exception as e:
        print("錯誤:", e)
        return "錯誤", 500
        
# 🔄 接收 ESP8266 上傳的狀態報告
device_status = {}  # 記錄最近一次上傳狀態

@app.route("/status-update", methods=["POST"])
def status_update():
    try:
        data = request.get_json()
        status_data = data.get("status")

        if not status_data:
            return {"error": "No status provided"}, 400

        # 儲存狀態
        global device_status
        device_status = status_data

        print("📡 接收到 ESP8266 狀態：", device_status)

        # ✅ 發送 LINE 通知（開機 or 主動上傳）
        msg_lines = ["🔔 ESP8266 裝置上線，當前腳位狀態："]
        for pin, val in device_status.items():
            msg_lines.append(f"{pin}：{val}")
        message = "\n".join(msg_lines)

        line_bot_api.push_message(LINE_GROUP_ID, TextSendMessage(text=message))

        return {"message": "狀態已更新並通知"}, 200

    except Exception as e:
        print("⚠️ 處理 /status-update 錯誤:", e)
        return {"error": "內部錯誤"}, 500

# Flask 啟動點（本地測試用）
if __name__ == "__main__":
    app.run(debug=True)
