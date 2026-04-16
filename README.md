# Translator Slack App

**オフショアチームと日本側メンバーのコミュニケーションを支援する Slack 翻訳 Bot** です。

Slack チャンネルに投稿されたメッセージを自動で翻訳し、**元メッセージのスレッド内**に翻訳結果を返信します。

- **日本語で投稿** → Bot が**英語に翻訳してスレッド返信**
- **英語で投稿** → Bot が**日本語に翻訳してスレッド返信**

投稿者は普段通り母国語で書くだけでよく、相手はスレッドを開けば翻訳された内容を確認できます。チャンネルのメインタイムラインは元の発言のみで保たれるため、通知の重複や会話の混線も起きません。

## このプロジェクトについて

オフショア開発体制での日本メンバーとのコミュニケーションロスを減らすことを目的に開発しました。Slack の Events API + Azure Functions で構築しています。

本リポジトリには**2つの実装バージョン**が保存されています。当初 Azure Translator API で構築しましたが、翻訳精度・モデル選択の柔軟性を求めて Azure OpenAI へ移行しました。学習・比較用に旧版も残しています。

## 2つのバージョン

| ディレクトリ | 翻訳エンジン | 状態 | 特徴 |
|---|---|---|---|
| [`azure-openai/`](./azure-openai/) | Azure OpenAI (GPT-4o 等) | **現行版（推奨）** | 高い翻訳精度、モデル選択可、コンテキスト考慮 |
| [`azure-translator/`](./azure-translator/) | Azure Translator API v3 | 旧版（参考） | シンプル、低コスト、無料枠あり |

### なぜ移行したか

- **精度**: Azure Translator は一般的な翻訳は得意だが、IT用語やチーム固有の文脈（プロジェクト名、略語、カジュアルな言い回し）で誤訳が目立った。GPT-4o はコンテキストを汲んだ自然な翻訳が可能
- **モデル選択の柔軟性**: Azure OpenAI なら GPT-4o / GPT-4o-mini / o1 などモデルを切替可能。コストと精度のバランスをチーム要件に合わせて調整できる
- **プロンプト制御**: システムプロンプトで「チームの技術用語は訳さない」「敬語で統一」等の制約を与えられる

### どちらを選ぶべきか

- **精度重視・チーム固有用語を扱う** → `azure-openai/`
- **コスト最優先・シンプルな汎用翻訳で十分** → `azure-translator/`

## 共通アーキテクチャ

<img width="1647" height="553" alt="image" src="https://github.com/user-attachments/assets/1b48507f-73fa-4953-8c9c-b99df9d7463c" />


> ⚠️ 上図は**初期構想時のイメージ図**です。実装では、Bot は新規メッセージではなく元メッセージの**スレッド内**に翻訳結果を返信します。また、現行版では Translator の代わりに Azure OpenAI を利用しています。

```
Slack ──(Events API)──▶ Azure Functions (Python v2)
                              │
                              ├──▶ 翻訳エンジン
                              │    （Azure OpenAI or Azure Translator）
                              │
                              └──▶ Slack chat.postMessage
                                   （元メッセージのスレッドに返信）
```

- **Azure Functions (Python v2 programming model)** でイベント受信・処理
- Slack の `message.channels` / `message.im` イベントをサブスクライブ
- Bot 自身の発言・重複イベントは除外（インメモリの `processed_events` セットで管理）
- 翻訳結果は `thread_ts` 指定でスレッド返信として投稿

## 技術スタック

| レイヤー | 技術 |
|---|---|
| ランタイム | Python 3.x / Azure Functions v2 |
| Slack 連携 | Slack Events API / slack_sdk |
| 翻訳（現行） | Azure OpenAI Service (GPT-4o 等) |
| 翻訳（旧版） | Azure Translator API v3 |
| デプロイ | Azure Functions（VSCode 拡張 or `func` CLI） |

## セットアップ

各バージョンの README を参照してください。

- [Azure OpenAI 版のセットアップ手順](./azure-openai/README.md)
- [Azure Translator 版のセットアップ手順](./azure-translator/README.md)

Slack アプリ側の設定は両バージョンで共通です。下記の手順を参照してください。

---

## Slack アプリの設定手順（共通）

両バージョンで共通の Slack 側の設定です。

### 1. Slack アプリを作成

<https://api.slack.com/apps> にアクセスし「**Create New App**」→「**From scratch**」を選択。App Name と Workspace を指定して作成します。

### 2. OAuth スコープを設定

「**OAuth & Permissions**」ページで以下の Bot Token Scope を追加します：

- `chat:write` — メッセージ投稿
- `users:read` — ユーザー情報取得

設定後「**Install to Workspace**」でアプリをワークスペースにインストールし、表示される **Bot Token（`xoxb-...`）** を控えておきます（環境変数 `SLACK_BOT_TOKEN` に設定）。

### 3. Bot User ID を取得

以下のコマンドで Bot のユーザー ID を取得します。

```bash
curl -X POST \
  -H "Authorization: Bearer xoxb-<your-bot-token>" \
  https://slack.com/api/auth.test
```

レスポンスの `user_id`（例：`U12345678`）を環境変数 `SLACK_BOT_USER_ID` に設定します。

### 4. Event Subscription を設定

「**Event Subscriptions**」ページで以下を設定します。

1. 「**Enable Events**」をオンにする
2. **Request URL** に Azure Functions の関数 URL を入力

   関数 URL は Azure ポータルの Function App → 該当関数 → **「コードとテスト」** 画面の **「関数の URL の取得」** ボタンから取得できます（`code` クエリ付きの完全 URL がコピーされます）。

   <img width="537" height="142" alt="image" src="https://github.com/user-attachments/assets/495d4468-8687-46ac-bfa8-ffc724585a2f" />


3. 「**Subscribe to bot events**」で以下を追加：
   - `message.channels` — パブリックチャンネルのメッセージ
   - `message.im` — DM のメッセージ
4. 保存後、再度「**Install to Workspace**」でワークスペースに再インストールして権限を反映

### 5. Bot をチャンネルに招待

翻訳対象の Slack チャンネルで `/invite @<BotName>` を実行し、Bot を招待します。以降、そのチャンネルでの日本語・英語の投稿が自動で翻訳され、スレッドに返信されます。
