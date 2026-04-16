# Azure Translator 版（旧版・参考）

Azure AI Translator API v3 を使って Slack メッセージを翻訳する Azure Functions 実装です。
当初バージョンで、現在は [`azure-openai/`](../azure-openai/) 版へ移行済みです。

> プロジェクト全体の概要・現行版（Azure OpenAI 版）との比較は [ルート README](../README.md) を参照してください。
> Slack アプリ側の設定手順は [ルート README の「Slack アプリの設定手順（共通）」](../README.md#slack-アプリの設定手順共通) を参照してください。

## この版を選ぶ場合

- コスト最優先（Azure Translator は月 200 万文字まで無料枠あり）
- 一般的な翻訳で十分で、チーム固有の用語や文脈理解は不要
- シンプルな REST API 呼び出しで完結する構成にしたい

## 必要な環境変数

Azure Functions の**アプリケーション設定**に以下を登録します。

| 環境変数 | 用途 | 取得方法 |
|---|---|---|
| `TRANSLATOR_ENDPOINT` | Translator API のエンドポイント | Azure Translator リソースの「キーとエンドポイント」 |
| `TRANSLATOR_KEY` | Translator API のキー（Key 1 または Key 2） | 同上 |
| `TRANSLATOR_REGION` | Translator リソースのリージョン | リソース作成時のリージョン（例：`japaneast`） |
| `SLACK_BOT_TOKEN` | Slack Bot トークン（`xoxb-...`） | [Slack 設定手順](../README.md#slack-アプリの設定手順共通) 参照 |
| `SLACK_BOT_USER_ID` | Slack Bot のユーザー ID（`U...`） | [Slack 設定手順](../README.md#slack-アプリの設定手順共通) 参照 |

### Translator のキー・エンドポイント・リージョンの取得方法

Azure ポータルで作成した Translator リソースの「**キーとエンドポイント**」画面から、`キー 1`、`場所/地域`、`テキスト翻訳`のエンドポイント URL をそれぞれ環境変数にマッピングします。

<img width="970" height="585" alt="image" src="https://github.com/user-attachments/assets/508d27af-de7e-4412-bfe4-bd037a665fb7" />


## セットアップ手順

### 1. Azure Translator リソースを作成

Azure ポータルで「**Translator**」リソースを作成し、「キーとエンドポイント」から上記3つの値を取得します。

### 2. Azure Functions へデプロイ

```bash
func azure functionapp publish <your-function-app-name>
```

### 3. 環境変数を設定

Azure ポータルの Function App → **環境変数**で、上記5つの環境変数を登録します。

### 4. Slack 側の設定

[ルート README の「Slack アプリの設定手順（共通）」](../README.md#slack-アプリの設定手順共通) に従って Slack アプリを作成・Event Subscription を設定してください。Request URL には本 Azure Functions の関数 URL を指定します。

### 5. 動作確認

Bot をチャンネルに招待し、日本語・英語でメッセージ投稿して翻訳されることを確認します。

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
