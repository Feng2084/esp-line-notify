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
    body = request.get_data(as_text=True)
    print("Webhook 收到資料：\n", body)

    # 建議可以將 webhook 資料儲存下來以便取得群組 ID
    try:
        data = json.loads(body)
        if "events" in data and len(data["events"]) > 0:
            source = data["events"][0].get("source", {})
            if source.get("type") == "group":
                group_id = source.get("groupId")
                print("📌 群組 ID：", group_id)
    except Exception as e:
        print("解析 webhook 資料失敗:", e)

    return "OK", 200

# 📟 提供 ESP8266 使用的路由，收到後發送 LINE 通知
@app.route("/alert", methods=["POST"])
def alert():
    try:
        data = request.get_json()
        pin = data.get("pin")
        status = data.get("status")
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        msg = f"⚠️ 偵測器觸發！\n設備：{pin}\n狀態：{status}\n🕒 時間：{time_str}"
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
        return {"message": "狀態已更新"}, 200

    except Exception as e:
        print("⚠️ 處理 /status-update 錯誤:", e)
        return {"error": "內部錯誤"}, 500

# Flask 啟動點（本地測試用）
if __name__ == "__main__":
    app.run(debug=True)
