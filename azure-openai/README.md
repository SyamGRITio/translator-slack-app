# Azure OpenAI 版（現行版）

Azure OpenAI Service（GPT-4o 等）を使って Slack メッセージを翻訳する Azure Functions 実装です。

> プロジェクト全体の概要・旧版（Azure Translator 版）との比較は [ルート README](../README.md) を参照してください。

## 必要な環境変数

Azure Functions の**アプリケーション設定**に以下を登録します。

| 環境変数 | 用途 | 取得方法 |
|---|---|---|
| `OPENAI_ENDPOINT` | Azure OpenAI のエンドポイント URL | Azure OpenAI リソースの「Keys and Endpoint」 |
| `OPENAI_KEY` | Azure OpenAI の API キー | 同上 |
| `OPENAI_DEPLOYMENT` | デプロイメント名 | Azure AI Foundry のデプロイ画面で作成したデプロイ名 |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（`xoxb-...`） | Slack アプリの「OAuth & Permissions」 |
| `SLACK_BOT_USER_ID` | Slack Bot のユーザー ID（`U...`） | 下記 `auth.test` API 参照 |

## 前提：Azure OpenAI リソースの準備

1. Azure ポータルで Azure OpenAI リソースを作成
2. Azure AI Foundry（旧 Azure OpenAI Studio）で任意のモデル（例：`gpt-4o`）をデプロイ
3. デプロイ名をメモ（これが `OPENAI_DEPLOYMENT` の値）

## セットアップ手順

### 1. Slack アプリを作成

1. <https://api.slack.com/apps> にアクセスし「Create New App」→「From scratch」
2. App Name と Workspace を指定して作成

### 2. OAuth & Permissions でスコープを設定

「OAuth & Permissions」ページで以下の Bot Token Scope を追加：

- `chat:write`
- `users:read`
- `commands`（必要に応じて）

設定後「Install App to Workspace」で Bot Token（`xoxb-...`）を取得 → `SLACK_BOT_TOKEN` に設定。

### 3. Bot User ID を取得

```bash
curl -X POST \
  -H "Authorization: Bearer xoxb-<your-bot-token>" \
  https://slack.com/api/auth.test
```

レスポンスの `user_id`（例：`U12345678`）を `SLACK_BOT_USER_ID` に設定。

### 4. Azure Functions へデプロイ

VSCode の Azure Functions 拡張、または Azure Functions Core Tools でデプロイ。

```bash
func azure functionapp publish <your-function-app-name>
```

### 5. 環境変数を設定

Azure ポータルの Function App → **設定** → **環境変数**（旧：構成）で、上記5つの環境変数を登録。

### 6. Slack の Event Subscription を設定

Slack アプリ管理画面の「Event Subscriptions」で：

1. 「Enable Events」をオンにする
2. Request URL に Function のエンドポイントを指定：
   ```
   https://<your-function-app-name>.azurewebsites.net/api/translator_slackbot?code=<function-key>
   ```
3. 「Subscribe to bot events」で以下を追加：
   - `message.channels`（パブリックチャンネル）
   - `message.im`（DM）
4. 保存 → Slack アプリをワークスペースに再インストール

### 7. Bot をチャンネルに招待して動作確認

翻訳対象のチャンネルに Bot を招待（`/invite @<BotName>`）し、日本語/英語でメッセージを投稿して、スレッドに翻訳が返ってくることを確認。

## ローカル開発

`local.settings.json`（gitignore 対象）に環境変数をセットして：

```bash
pip install -r requirements.txt
func start
```

## ファイル構成

```
azure-openai/
├── function_app.py       # Azure Functions エントリポイント
├── requirements.txt      # Python 依存ライブラリ
├── host.json             # Azure Functions ホストランタイム設定
└── README.md             # 本ドキュメント
```

## 実装のポイント

- **言語検出と翻訳を同じ GPT 呼び出しで完結**（`detect_language` と `translate_text` の2回呼び出し。コスト重視ならシステムプロンプトで1回にまとめることも可能）
- **Bot 自身の発言・重複イベント除外**: `processed_events` セットで ts を管理。Functions インスタンスが再起動すると揮発するので、厳密な重複防止が必要な場合は Redis/Cosmos DB 等に置き換えが必要
- **スレッド返信**: `thread_ts` を元メッセージの `ts` に設定することで、翻訳結果を元メッセージのスレッドとして投稿
