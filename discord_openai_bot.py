import discord
import traceback
from discord.ext import commands
from os import getenv
import openai

# OpenAIのAPIキーを環境変数から読み込む
openai.api_key = getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(f"⚠️ エラーが発生しました：\n```\n{error_msg}\n```")


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send('pong')


@bot.command(name="chat")
async def chat(ctx, *, prompt: str):
    """ChatGPTと会話します。使用例: /chat おすすめの映画は？"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # または "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "あなたはDiscordの相談役です。丁寧で親しみやすい応答を心がけてください。"},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response["choices"][0]["message"]["content"]
        await ctx.send(reply)

    except Exception as e:
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ ChatGPTとの通信でエラーが発生しました：\n```\n{error_msg}\n```")


# DiscordのBotトークンを環境変数から取得
token = getenv('DISCORD_BOT_TOKEN')
bot.run(token)
