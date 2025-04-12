import discord
import openai
import traceback
from discord.ext import commands
from os import getenv

# 環境変数からトークンとAPIキーを取得
DISCORD_TOKEN = getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")

# どちらかが設定されていなければ停止
if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise Exception("❌ DISCORD_BOT_TOKEN または OPENAI_API_KEY が設定されていません。")

# OpenAI初期化
openai.api_key = OPENAI_API_KEY

# Discord Botの初期化
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ BOT起動完了: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(f"⚠️ エラーが発生しました：\n```{error_msg}```")

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def chat(ctx, *, prompt: str):
    """ChatGPTと会話します。使用例: /chat 今日の天気は？"""
    try:
        await ctx.send("💬 ChatGPTに問い合わせ中...")
        response = openai.ChatCompletion.create(
            model="gpt-4",  # または "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "あなたはユーザーの相談に乗る親しみやすいAIです。"},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        await ctx.send(reply)
    except Exception as e:
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ ChatGPTとの通信エラー：\n```{error_msg}```")

# Botの実行
bot.run(DISCORD_TOKEN)
