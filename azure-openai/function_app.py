import logging
import os
import openai
import azure.functions as func
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ログレベル設定（INFO以上を出力）
logging.basicConfig(level=logging.INFO)
processed_events = set()

# Azure OpenAI 設定 (環境変数から読み込み)
openai.api_type    = "azure"
openai.api_base    = os.getenv("OPENAI_ENDPOINT", "").rstrip("/")
openai.api_key     = os.getenv("OPENAI_KEY", "")
openai.api_version = "2024-12-01-preview"
DEPLOYMENT_ID      = os.getenv("OPENAI_DEPLOYMENT", "")

# FunctionApp オブジェクト生成
app = func.FunctionApp()

# HTTP トリガー定義
@app.function_name(name="translator_slackbot")
@app.route(
    route="translator_slackbot",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION
)
def translator_slackbot(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        # 受信ペイロードをログ出力
        logging.info(f"[RECV ] Received payload: {payload}")

        # Slack URL 検証
        if payload.get("type") == "url_verification":
            return func.HttpResponse(payload.get("challenge"), status_code=200)

        ev = payload.get("event", {})
        text      = ev.get("text")
        channel   = ev.get("channel")
        user_id   = ev.get("user")
        ts        = ev.get("ts")
        thread_ts = ev.get("thread_ts") or ts
        bot_id    = os.getenv("SLACK_BOT_USER_ID", "")

        # 無効／Bot自身／重複イベントを除外
        if not text or not channel or not ts:
            return func.HttpResponse("Invalid payload", status_code=400)
        if user_id == bot_id or ev.get("bot_id") or ts in processed_events:
            return func.HttpResponse(status_code=200)
        processed_events.add(ts)

        # 言語検出→翻訳
        lang        = detect_language(text)
        translation = translate_text(text, lang)
        # 検出結果と翻訳結果をログ出力
        logging.info(f"[XLT  ] Detected={lang}, Translated={translation}")

        # Slack に送信
        send_to_slack(translation, channel, thread_ts)
        return func.HttpResponse("OK", status_code=200)

    except Exception as e:
        logging.error(f"Function error: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)


def detect_language(text: str) -> str:
    """GPT-4o で言語検出"""
    resp = openai.ChatCompletion.create(
        deployment_id=DEPLOYMENT_ID,
        messages=[
            {"role": "system", "content": "Detect the language of the following text and return only the ISO 639-1 code."},
            {"role": "user",   "content": text}
        ],
        max_tokens=5
    )
    return resp.choices[0].message.content.strip().strip('"')


def translate_text(text: str, detected_lang: str) -> str:
    """GPT-4o で翻訳"""
    target = "ja" if detected_lang == "en" else "en"
    prompt = f"Translate the following text into {target}. Respond with translated text only.\n\n{text}"
    resp = openai.ChatCompletion.create(
        deployment_id=DEPLOYMENT_ID,
        messages=[
            {"role": "system", "content": "You are a translation service."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=1000
    )
    return resp.choices[0].message.content.strip()


def send_to_slack(text: str, channel: str, thread_ts: str = None):
    """Slack にメッセージを送信"""
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN", ""))
    try:
        client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)
    except SlackApiError as err:
        logging.error(f"Slack API error: {err}")
