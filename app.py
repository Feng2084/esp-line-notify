from flask import Flask, request
import os
import requests
import json
app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=data)

@app.route("/esp_notify", methods=["POST"])
def notify():
    message = request.form.get("message", "ESP8266 發來通知")
    send_line_message(message)
    return "OK"

@app.route('/', methods=['GET'])
def home():
    return 'LINE Bot is running!'

@app.route('/callback', methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    print("Webhook Body:\n", body)  # 你部署後可以改成儲存到檔案或回傳
    return 'OK'
