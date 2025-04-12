import discord
import traceback
from discord.ext import commands
from os import getenv
from openai import OpenAI

# 環境変数からAPIキーを取得
DISCORD_TOKEN = getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")

# トークンまたはAPIキーが未設定の場合は停止
if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise Exception("❌ DISCORD_BOT_TOKEN または OPENAI_API_KEY が設定されていません。")

# OpenAIクライアントを初期化（v1.0以降の新仕様）
client_ai = OpenAI(api_key=OPENAI_API_KEY)

# Discord Botの初期化
intents = discord.Intents.default()
intents.message_content = True  # メッセージ読み取りを有効に
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ BOT起動完了: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    # エラーを詳細表示（Discord上に送信）
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(f"⚠️ エラーが発生しました：\n```{error_msg}```")

@bot.command()
async def ping(ctx):
    # シンプルな応答確認
    await ctx.send('pong')

@bot.command()
async def chat(ctx, *, prompt: str):
    """ChatGPTと会話します。使用例: /chat 今日の天気は？"""
    try:
        await ctx.send("💬 ChatGPTに問い合わせ中...")

        # OpenAI (v1.0以降) にチャットリクエストを送信
        response = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",  # 安定して使えるモデル（必要に応じてgpt-4に変更可能）
            messages=[
                {"role": "system", "content": "あなたはユーザーの相談に乗る親しみやすいAIです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # 応答を取り出して送信
        reply = response.choices[0].message.content
        await ctx.send(reply)

    except Exception as e:
        # OpenAIとの通信で発生したエラーを表示
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ ChatGPTとの通信エラー：\n```{error_msg}```")

# Botの起動
bot.run(DISCORD_TOKEN)
