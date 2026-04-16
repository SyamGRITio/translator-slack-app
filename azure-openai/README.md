# Azure OpenAI 版（現行版）

Azure OpenAI Service（GPT-4o 等）を使って Slack メッセージを翻訳する Azure Functions 実装です。

> プロジェクト全体の概要・旧版（Azure Translator 版）との比較は [ルート README](../README.md) を参照してください。
> Slack アプリ側の設定手順は [ルート README の「Slack アプリの設定手順（共通）」](../README.md#slack-アプリの設定手順共通) を参照してください。

## 必要な環境変数

Azure Functions の**アプリケーション設定**に以下を登録します。

| 環境変数 | 用途 | 取得方法 |
|---|---|---|
| `OPENAI_ENDPOINT` | Azure OpenAI のエンドポイント URL | Azure OpenAI リソースの「キーとエンドポイント」 |
| `OPENAI_KEY` | Azure OpenAI の API キー | 同上 |
| `OPENAI_DEPLOYMENT` | デプロイメント名 | Azure AI Foundry のデプロイ画面で作成したデプロイ名 |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（`xoxb-...`） | [Slack 設定手順](../README.md#slack-アプリの設定手順共通) 参照 |
| `SLACK_BOT_USER_ID` | Slack Bot のユーザー ID（`U...`） | [Slack 設定手順](../README.md#slack-アプリの設定手順共通) 参照 |

## セットアップ手順

### 1. Azure OpenAI リソースを準備

1. Azure ポータルで Azure OpenAI リソースを作成
2. Azure AI Foundry（旧 Azure OpenAI Studio）で任意のモデル（例：`gpt-4o`）をデプロイ
3. デプロイ名をメモ（これが `OPENAI_DEPLOYMENT` の値）
4. 「キーとエンドポイント」画面から Endpoint と Key を控える

### 2. Azure Functions へデプロイ

VSCode の Azure Functions 拡張、または Azure Functions Core Tools でデプロイします。

```bash
func azure functionapp publish <your-function-app-name>
```

### 3. 環境変数を設定

Azure ポータルの Function App → **設定** → **環境変数**（旧：構成）で、上記5つの環境変数を登録します。

### 4. Slack 側の設定

[ルート README の「Slack アプリの設定手順（共通）」](../README.md#slack-アプリの設定手順共通) に従って Slack アプリを作成・Event Subscription を設定してください。Request URL には本 Azure Functions の関数 URL を指定します。

### 5. 動作確認

翻訳対象の Slack チャンネルに Bot を招待し、日本語・英語でメッセージを投稿して、スレッドに翻訳が返ってくることを確認します。

## ローカル開発

`local.settings.json`（gitignore 対象）に環境変数をセットして起動します。

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

- **言語検出と翻訳を GPT 呼び出しで実施**（`detect_language` と `translate_text` の2回呼び出し。コスト重視ならシステムプロンプトで1回にまとめることも可能）
- **Bot 自身の発言・重複イベント除外**: `processed_events` セットで ts を管理。Functions インスタンスが再起動すると揮発するので、厳密な重複防止が必要な場合は Redis / Cosmos DB 等に置き換えが必要
- **スレッド返信**: `thread_ts` を元メッセージの `ts` に設定することで、翻訳結果を元メッセージのスレッドとして投稿
