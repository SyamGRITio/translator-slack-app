import logging
import requests
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import azure.functions as func

logging.basicConfig(level=logging.DEBUG)

app = func.FunctionApp()

# 処理済みイベントを保持するセット
processed_messages = set()

@app.route(route="translator_slackbot", auth_level=func.AuthLevel.FUNCTION)
def translator_slackbot(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        event = req_body.get("event", {})
        event_id = req_body.get("event_id")  # イベントID取得
        text = event.get("text")
        channel = event.get("channel")
        user_id = event.get("user")  # メッセージ送信者のユーザーID

        # BOT自身のユーザーIDを環境変数から取得
        bot_user_id = os.getenv("SLACK_BOT_USER_ID", "")

        # 必須フィールドチェック
        if not text or not channel or not event_id or not user_id:
            logging.warning("Missing required fields: 'text', 'channel', 'event_id', or 'user'")
            return func.HttpResponse("Invalid payload", status_code=400)

        # BOT自身のメッセージを無視（再翻訳防止）
        if user_id == bot_user_id:
            logging.info("Message from bot itself ignored")
            return func.HttpResponse("Message from bot ignored", status_code=200)

        # 重複イベントのフィルタリング
        if event_id in processed_messages:
            logging.info("Duplicate event ignored")
            return func.HttpResponse("Event already processed", status_code=200)

        # 処理済みイベントとして記録
        processed_messages.add(event_id)

        # 言語検出処理
        detected_lang = detect_language(text)
        if detected_lang == "unknown":
            logging.warning("Language detection failed")
            return func.HttpResponse("Language detection failed", status_code=500)

        # 翻訳処理
        translated_text = translate_text(text, detected_lang)
        if translated_text == "Translation failed":
            return func.HttpResponse("Translation failed", status_code=500)

        # 翻訳結果をSlackに送信
        send_to_slack(translated_text, channel)

        logging.info(f"Message processed successfully: {event_id}")
        return func.HttpResponse("Event processed successfully", status_code=200)
    except Exception as e:
        logging.error(f"Function error: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

def detect_language(text: str) -> str:
    """Azure Translator APIで言語を検出"""
    endpoint = os.getenv("TRANSLATOR_ENDPOINT", "").rstrip('/')
    key = os.getenv("TRANSLATOR_KEY", "")
    region = os.getenv("TRANSLATOR_REGION", "")

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-Type": "application/json",
    }
    body = [{"text": text}]
    
    try:
        response = requests.post(f"{endpoint}/detect?api-version=3.0", headers=headers, json=body)
        response.raise_for_status()
        detected_lang = response.json()[0]["language"]
        return detected_lang
    except requests.exceptions.RequestException as e:
        logging.error(f"Language detection error: {e}")
        return "unknown"

def translate_text(text: str, detected_lang: str) -> str:
    """Azure Translator APIで翻訳"""
    endpoint = os.getenv("TRANSLATOR_ENDPOINT", "").rstrip('/')
    key = os.getenv("TRANSLATOR_KEY", "")
    region = os.getenv("TRANSLATOR_REGION", "")

    if not endpoint or not key or not region:
        logging.error("Translation API configuration is missing")
        return "Translation failed"

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-Type": "application/json",
    }
    body = [{"text": text}]
    target_lang = "ja" if detected_lang == "en" else "en"
    
    try:
        response = requests.post(f"{endpoint}/translate?api-version=3.0&to={target_lang}", headers=headers, json=body)
        response.raise_for_status()

        translations = response.json()[0]["translations"]
        return translations[0]["text"] if translations else "Translation failed"
    except requests.exceptions.RequestException as e:
        logging.error(f"Translation API error: {e}")
        return "Translation failed"

def send_to_slack(text: str, channel: str):
    """翻訳結果をSlackに送信"""
    slack_token = os.getenv("SLACK_BOT_TOKEN", "")
    if not slack_token:
        logging.error("Slack token is missing")
        return

    client = WebClient(token=slack_token)
    try:
        client.chat_postMessage(channel=channel, text=text)
    except SlackApiError as e:
        logging.error(f"Slack API error: {e.response.get('error')}")