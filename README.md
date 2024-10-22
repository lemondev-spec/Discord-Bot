# Discord Bot - 任意の通貨名管理ボット

このDiscordボットは、サーバーメンバー間での「任意の通貨名」の管理と取引を行うための機能を提供します。

## 機能概要

- **所持金の表示**：ユーザーの現在の所持金を表示します。
- **送金**：指定したユーザーに任意の通貨名を送金します。
- **ロールの購入**：サーバー内の特定のロールを任意の通貨名で購入できます。
- **購入可能なロールのリスト表示**：購入可能なロールとその価格を表示します。
- **ロールの価格設定（管理者のみ）**：特定のロールの価格を設定できます。

## 環境設定

### 必要なツール

- Python 3.8以降
- Discord API トークン

### ライブラリのインストール

以下のコマンドで必要なPythonライブラリをインストールします：

```bash
pip install discord.py

コマンドの使い方
/show_balance
説明：あなたの現在の所持金を表示します。

使用例：

plaintext
コードをコピーする
/show_balance
/transfer_money
説明：指定したユーザーに任意の通貨名を送金します。

使用例：

plaintext
コードをコピーする
/transfer_money @username 100
/buy_role
説明：指定したロールを購入します。

使用例：

plaintext
コードをコピーする
/buy_role ロール名
/list_roles
説明：購入可能なロールとその価格を表示します。

使用例：

plaintext
コードをコピーする
/list_roles
/set_role_price（管理者のみ）
説明：特定のロールの価格を設定します。

使用例：

plaintext
コードをコピーする
/set_role_price ロール名 500
ファイル構成
bot.py：ボットのメインファイル。ボットの設定とイベントハンドラーが含まれています。
cogs/commands.py：コマンド機能が実装されています。
user_balances.json：ユーザーの所持金を管理するためのJSONファイル。
user_chat_cooldown.json：チャットのクールダウン時間を管理するためのJSONファイル。
bot_errors.log：エラーログファイル。
注意事項
セキュリティ：必ずDISCORD_TOKENを外部に公開しないように注意してください。
バックアップ：重要なデータ（user_balances.jsonなど）は定期的にバックアップを取ることをお勧めします。