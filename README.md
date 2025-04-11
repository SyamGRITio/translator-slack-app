プロジェクト概要
このリポジトリには、Azure Functionsと統合されたSlack BOTが含まれています。このBOTは、Azure Translator APIを使用して、メッセージをリアルタイムで翻訳します。英語と日本語間の翻訳をサポートし、BOT自身の発言を再翻訳しないような仕組みも備えています。

ファイル構成
├── .funcignore           # Azure Functionsデプロイ時に無視するファイルやディレクトリを指定。
├── .gitignore            # Gitでバージョン管理から除外するファイルやディレクトリを指定。
├── function_app.py       # 翻訳機能を実行するAzure Functionのメインコード。
├── host.json             # Azure Functionsホストランタイムの設定ファイル。
├── local.settings.json   # Azure Functions用のローカル環境変数設定。
├── requirements.txt      # Pythonの依存ライブラリを記載したファイル。
├── __pycache__/          # Pythonのバイトコードキャッシュ（自動生成される）。
├── .vscode/              # VSCode用のプロジェクト設定:
│   ├── extensions.json   # 推奨拡張機能のリスト。
│   ├── launch.json       # デバッグ設定ファイル。
│   ├── settings.json     # VSCode固有の設定。
│   ├── tasks.json        # タスクのビルドや自動化の設定。



機能
- Azure Translator APIを活用したリアルタイム翻訳。
- Slack BOT統合によるシームレスなメッセージ処理。
- BOT自身の発言を無視し、不要な翻訳を防止。
- Azure Functionsと簡単に統合可能。


セットアップ手順
1. Slack BOTのセットアップ
1.1 アプリを作成
- Slack API管理ページにアクセスして、新しいアプリを作成します。
- **「Create New App」**をクリック。
- **「From scratch」**を選択し、以下を入力：- App Name: アプリ名（例: MySlackBot）。
- Workspace: BOTをインストールするワークスペースを選択。


1.2 OAuth & Permissionsの設定
- アプリ管理ページの左メニューから**「OAuth & Permissions」**セクションを選択。
- 以下のスコープを追加：- commands
- chat:write
- users:read

- 保存後、**「Install App to Workspace」**をクリックしてアプリをワークスペースにインストール。
- インストールが成功すると**Bot Token（xoxb-...）**が表示されます。このトークンを記録してください。

1.3 イベントサブスクリプションの設定
- アプリ管理ページの左メニューから**「Event Subscriptions」**セクションを選択。
- **「Enable Events」**をオンにする。
- **「Request URL」**にAzure関数アプリのエンドポイントを入力：https://<your-function-app-name>.azurewebsites.net/api/translator_slackbot

- **「Subscribe to Bot Events」**で以下のイベントを追加：- message.channels（パブリックチャネル用）
- message.im（DM用）

- 保存して設定を適用します。


2. SLACK_BOT_TOKENとSLACK_BOT_USER_IDの取得
- ターミナルまたはコマンドプロンプトで以下のコマンドを実行：curl -X POST \
-H "Authorization: Bearer xoxb-<your-bot-token>" \
https://slack.com/api/auth.test

- レスポンス例：{
  "ok": true,
  "url": "https://your-workspace.slack.com/",
  "team": "Your Team Name",
  "user": "Your Bot Name",
  "team_id": "T12345678",
  "user_id": "U12345678"
}

- user_idの値（例: U12345678）をSLACK_BOT_USER_IDとして環境変数に設定します。


3. Azure Functionsのセットアップ
- function_app.pyをAzure Functionsにデプロイします。
- Azureポータルで以下の環境変数を設定：- SLACK_BOT_TOKEN: SlackのBot Token。
- SLACK_BOT_USER_ID: Slack APIで取得したBOTのユーザーID。
- TRANSLATOR_ENDPOINT: Azure Translator APIのエンドポイント。
- TRANSLATOR_KEY: Azure Translator APIのキー。
- TRANSLATOR_REGION: Azure Translator APIのリージョン。



4. 動作確認
- SlackのワークスペースでBOTにメッセージを送信し、翻訳が正しく行われることを確認します。
- 必要に応じてAzureポータルのログを確認し、エラーがないかチェックします。


依存ライブラリのインストール
requirements.txtに記載された依存ライブラリをインストールしてください：
pip install -r requirements.txt



開発およびデバッグ
- VSCode設定: .vscodeフォルダには以下が含まれています：- launch.json: デバッグ設定。
- settings.json: VSCode用の設定。
- tasks.json: 自動化タスクの設定。

- デバッグを活用し、ローカル環境での動作確認が可能です。

