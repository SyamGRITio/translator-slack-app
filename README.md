# Translator Slack App

**オフショアチームと日本側メンバーのコミュニケーションを支援する Slack 翻訳 Bot** です。
Slack チャンネル上の発言を自動で日↔英翻訳し、元メッセージのスレッドに翻訳結果を返信します。発言者は通常通り母国語で投稿するだけで、相手はそのスレッドを開けば翻訳された内容を確認できます。

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

Slack アプリ側の設定（Bot 作成・OAuth スコープ・Event Subscription）は両バージョンで共通です。
