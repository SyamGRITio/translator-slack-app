import logging
import requests
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import azure.functions as func

logging.basicConfig(level=logging.DEBUG)
processed_events = set()

app = func.FunctionApp()

@app.route(route="translator_slackbot", auth_level=func.AuthLevel.FUNCTION)
def translator_slackbot(req: func.HttpRequest) -> func.HttpResponse:
    global processed_events
    try:
        req_body = req.get_json()

        # SlackのURL検証
        if req_body.get("type") == "url_verification":
            return func.HttpResponse(req_body.get("challenge"), status_code=200)

        # イベントデータの取得と必須フィールドチェック
        event = req_body.get("event", {})
        text = event.get("text")
        channel = event.get("channel")
        user_id = event.get("user")
        event_ts = event.get("ts")
        thread_ts = event.get("thread_ts")
        bot_id = event.get("bot_id")

        if not text or not channel or not event_ts:
            return func.HttpResponse("Invalid payload", status_code=400)

        # BOT自身のメッセージまたはイベント重複防止
        bot_user_id = os.getenv("SLACK_BOT_USER_ID", "")
        if user_id == bot_user_id or bot_id or event_ts in processed_events:
            return func.HttpResponse("Message from bot ignored or duplicate event", status_code=200)

        processed_events.add(event_ts)

        # 言語検出と翻訳処理
        detected_lang = detect_language(text)
        if detected_lang == "unknown":
            return func.HttpResponse("Language detection failed", status_code=500)

        translated_text = translate_text(text, detected_lang)
        send_to_slack(translated_text, channel, thread_ts or event_ts)

        return func.HttpResponse("Event processed successfully", status_code=200)
    except Exception as e:
        logging.error(f"Function error: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)

def detect_language(text: str) -> str:
    """Azure Translator APIで言語検出"""
    endpoint = os.getenv("TRANSLATOR_ENDPOINT", "").rstrip('/')
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("TRANSLATOR_KEY", ""),
        "Ocp-Apim-Subscription-Region": os.getenv("TRANSLATOR_REGION", ""),
        "Content-Type": "application/json",
    }
    body = [{"text": text}]
    response = requests.post(f"{endpoint}/detect?api-version=3.0", headers=headers, json=body)
    response.raise_for_status()
    return response.json()[0]["language"]

def translate_text(text: str, detected_lang: str) -> str:
    """Azure Translator APIで翻訳"""
    endpoint = os.getenv("TRANSLATOR_ENDPOINT", "").rstrip('/')
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("TRANSLATOR_KEY", ""),
        "Ocp-Apim-Subscription-Region": os.getenv("TRANSLATOR_REGION", ""),
        "Content-Type": "application/json",
    }
    target_lang = "ja" if detected_lang == "en" else "en"
    body = [{"text": text}]
    response = requests.post(f"{endpoint}/translate?api-version=3.0&to={target_lang}", headers=headers, json=body)
    response.raise_for_status()
    return response.json()[0]["translations"][0]["text"]

def send_to_slack(text: str, channel: str, thread_ts: str = None):
    """Slackに翻訳結果を送信"""
    slack_token = os.getenv("SLACK_BOT_TOKEN", "")
    client = WebClient(token=slack_token)
    client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)