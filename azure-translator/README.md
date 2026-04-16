# Azure Translator 版（旧版・参考）

Azure AI Translator API v3 を使って Slack メッセージを翻訳する Azure Functions 実装です。
当初バージョンで、現在は [`azure-openai/`](../azure-openai/) 版へ移行済みです。

> プロジェクト全体の概要・現行版（Azure OpenAI 版）との比較は [ルート README](../README.md) を参照してください。

## この版を選ぶ場合

- コスト最優先（Azure Translator は月 200 万文字まで無料枠あり）
- 一般的な翻訳で十分で、チーム固有の用語や文脈理解は不要
- シンプルなREST API 呼び出しで完結する構成にしたい

## 必要な環境変数

Azure Functions の**アプリケーション設定**に以下を登録します。

| 環境変数 | 用途 | 取得方法 |
|---|---|---|
| `TRANSLATOR_ENDPOINT` | Translator API のエンドポイント | Azure Translator リソースの「Keys and Endpoint」 |
| `TRANSLATOR_KEY` | Translator API のキー | 同上 |
| `TRANSLATOR_REGION` | Translator リソースのリージョン | リソース作成時のリージョン（例：`japaneast`） |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（`xoxb-...`） | Slack アプリの「OAuth & Permissions」 |
| `SLACK_BOT_USER_ID` | Slack Bot のユーザー ID（`U...`） | 下記 `auth.test` API 参照 |

## セットアップ手順

### 1. Azure Translator リソースを作成

Azure ポータルで「Translator」リソースを作成し、Keys / Endpoint / Region を取得。

### 2. Slack アプリを作成・OAuth 設定

[azure-openai 版の README](../azure-openai/README.md#1-slack-アプリを作成) と同じ手順。必要な Bot Token Scope：

- `chat:write`
- `users:read`

### 3. Bot User ID を取得

```bash
curl -X POST \
  -H "Authorization: Bearer xoxb-<your-bot-token>" \
  https://slack.com/api/auth.test
```

レスポンスの `user_id` を `SLACK_BOT_USER_ID` に設定。

### 4. Azure Functions へデプロイ

```bash
func azure functionapp publish <your-function-app-name>
```

### 5. 環境変数を設定

Azure ポータルの Function App → 環境変数で、上記5つの環境変数を登録。

### 6. Slack の Event Subscription を設定

Request URL に：
```
https://<your-function-app-name>.azurewebsites.net/api/translator_slackbot?code=<function-key>
```

Subscribe to bot events：
- `message.channels`
- `message.im`

### 7. 動作確認

Bot をチャンネルに招待し、日本語/英語メッセージで翻訳されることを確認。

## ローカル開発

```bash
pip install -r requirements.txt
func start
```

## ファイル構成

```
azure-translator/
├── function_app.py       # Azure Functions エントリポイント（Translator API 呼び出し）
├── requirements.txt      # Python 依存ライブラリ（requests のみ）
├── host.json             # Azure Functions ホストランタイム設定
└── README.md             # 本ドキュメント
```

## 実装のポイント

- **言語検出**: Translator の `/detect?api-version=3.0` エンドポイントで ISO 639-1 コードを取得
- **翻訳**: `/translate?api-version=3.0&to={target_lang}` で翻訳。検出言語が `en` なら日本語へ、それ以外は英語へ固定
- **SDK 不使用**: `requests` で直接 REST API を叩くシンプル構成
- **ヘッダー**: `Ocp-Apim-Subscription-Key` と `Ocp-Apim-Subscription-Region` が Azure Translator 固有
