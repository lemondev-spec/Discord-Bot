import discord
from discord.ext import commands, tasks
import json
import os
import logging
from datetime import datetime, timedelta

# ボットのトークンとアプリケーションIDを入力
DISCORD_TOKEN = 'YOUR_DISCORD_TOKEN'
APPLICATION_ID = 'YOUR_APPLICATION_ID'

# intentsの設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True
intents.reactions = True
intents.typing = True
intents.presences = True  # Presence Intentを有効にする
intents.members = True  # Server Members Intentを有効にする

# ロギングの設定
logging.basicConfig(filename='bot_errors.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# コンソールにもログを出力
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# データファイルの設定
USER_BALANCES_FILE = 'user_balances.json'
ROLE_PRICES_FILE = 'role_prices.json'
USER_VOICE_TIME_FILE = 'user_voice_time.json'
USER_CHAT_COOLDOWN_FILE = 'user_chat_cooldown.json'

# JSONファイルの初期化
def initialize_json_file(file, default_data):
    if not os.path.exists(file) or os.path.getsize(file) == 0:
        with open(file, 'w') as f:
            json.dump(default_data, f, indent=2)

# 初期化
initialize_json_file(USER_BALANCES_FILE, {})
initialize_json_file(ROLE_PRICES_FILE, {})
initialize_json_file(USER_VOICE_TIME_FILE, {})
initialize_json_file(USER_CHAT_COOLDOWN_FILE, {})

# データの読み込み
def load_json(file):
    try:
        if os.path.exists(file):
            with open(file, 'r') as f:
                return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file}. Initializing with empty data.")
        return {}
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2, cls=DateTimeEncoder)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents, application_id=APPLICATION_ID)
        self.initial_extensions = ['cogs.commands']
        self.user_balances = load_json(USER_BALANCES_FILE)
        self.role_prices = load_json(ROLE_PRICES_FILE)
        self.user_voice_time = load_json(USER_VOICE_TIME_FILE)
        self.user_chat_cooldown = load_json(USER_CHAT_COOLDOWN_FILE)

    async def setup_hook(self):
        for extension in self.initial_extensions:
            await self.load_extension(extension)
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        self.guild_id = self.guilds[0].id if self.guilds else None  # 最初のギルドのIDを取得
        if self.guild_id:
            self.voice_time_tracker.start()

    async def on_message(self, message):
        if message.author.bot:
            return

        try:
            user_id = str(message.author.id)
            now = datetime.now()

            if user_id not in self.user_chat_cooldown or now > self.user_chat_cooldown[user_id]:
                if user_id not in self.user_balances:
                    self.user_balances[user_id] = 0
                self.user_balances[user_id] += 15
                self.user_chat_cooldown[user_id] = now + timedelta(minutes=30)

                if self.user_balances[user_id] >= 100 and self.user_balances[user_id] - 15 < 100:
                    await message.channel.send(f'おめでとうございます、{message.author.mention}さん！あなたの任意の名前が100に達しました🎉')

                save_json(USER_BALANCES_FILE, self.user_balances)
                save_json(USER_CHAT_COOLDOWN_FILE, self.user_chat_cooldown)
        except Exception as e:
            logging.error(f"Error in on_message event: {e}")

    async def on_voice_state_update(self, member, before, after):
        try:
            user_id = str(member.id)
            if not before.channel and after.channel:
                self.user_voice_time[user_id] = {
                    "join_time": datetime.now().isoformat(),
                    "accrued_time": 0
                }
            elif before.channel and not after.channel:
                if user_id in self.user_voice_time:
                    join_time = datetime.fromisoformat(self.user_voice_time[user_id]["join_time"])
                    accrued_time = self.user_voice_time[user_id]["accrued_time"]
                    total_time = (datetime.now() - join_time).total_seconds() + accrued_time
                    self.user_voice_time[user_id]["accrued_time"] = total_time
                    self.user_voice_time[user_id]["join_time"] = None
                    save_json(USER_VOICE_TIME_FILE, self.user_voice_time)
        except Exception as e:
            logging.error(f"Error in on_voice_state_update event: {e}")

    @tasks.loop(minutes=1)
    async def voice_time_tracker(self):
        try:
            for user_id, data in self.user_voice_time.items():
                if data["join_time"]:
                    join_time = datetime.fromisoformat(data["join_time"])
                    time_spent = (datetime.now() - join_time).total_seconds() + data["accrued_time"]
                    if time_spent >= 3600:
                        self.user_voice_time[user_id]["accrued_time"] = time_spent - 3600
                        self.user_balances[user_id] = self.user_balances.get(user_id, 0) + 150

                        guild = self.get_guild(self.guild_id)
                        member = guild.get_member(int(user_id))
                        if member:
                            await member.send(f'1時間の通話に参加したため、150任意の名前をゲットしました！ {member.mention}')

                    save_json(USER_BALANCES_FILE, self.user_balances)
                    save_json(USER_VOICE_TIME_FILE, self.user_voice_time, cls=DateTimeEncoder)
        except Exception as e:
            logging.error(f"Error in voice_time_tracker task: {e}")

# ボットオブジェクトの作成
bot = MyBot()

# 実行中の例外をキャッチし、ログに記録する
try:
    bot.run(DISCORD_TOKEN)
except Exception as e:
    logging.error(f"Error running the bot: {e}")
    print(f"エラーが発生しました: {e}")
    input("エラーが発生しました。ログを確認してください。Enterキーを押して終了します。")
