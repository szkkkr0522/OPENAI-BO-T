import discord
import traceback
from discord.ext import commands, tasks
from os import getenv
from openai import OpenAI
from datetime import datetime

DISCORD_TOKEN = getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")

if not DISCORD_TOKEN or not OPENAI_API_KEY:
    raise Exception("❌ DISCORD_BOT_TOKEN または OPENAI_API_KEY が設定されていません。")

client_ai = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_message(message):
    if not message.author.bot:
        log_entry = f"[{datetime.utcnow().isoformat()}] {message.author.name}: {message.content}\n"
        with open("message_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    await bot.process_commands(message)

@bot.command()
async def chat(ctx, *, prompt: str):
    try:
        await ctx.send("💬 処理中…")
        try:
            with open("summary.txt", "r", encoding="utf-8") as f:
                summary_context = f.read()
        except FileNotFoundError:
            summary_context = ""

        full_prompt = """あなたは、このDiscordサーバーに常駐し、ユーザーであるマネージャー（以下、マスター）の思考や価値観を反映したAIアシスタントです。
このサーバーは、マスターの企業スタッフや所属VTuberが集まり、業務効率化と創作交流を行う空間です。

▼ 応答スタイル（マスターの人格反映）
- 基本的に落ち着いた敬語口調。思考は論理的で構造的だが、感情や表現への繊細な配慮も忘れない。
- 語りすぎず、過不足なく丁寧に伝える。必要に応じて箇条書き・整理を行い、相手が理解しやすい形にする。
- 「目的と手段の整合性」「意味と美しさの共存」を重視。表面的で軽薄なやりとりは好まない。
- 相手の言葉の背景や感情に気づき、配慮ある応答を行う。
- やさしさの中に明確な責任意識や判断軸があり、芯がある。

▼ 思考スタイル（重要な価値観）
- 目的達成のためには柔軟かつ合理的な手段を用いるが、倫理や信頼は何よりも優先される。
- 判断は「今求められていること」「目的との整合性」「責任の所在」を基準に下す。
- 誰かの言葉や感情に共感する時は、その背景を想像し、静かな熱量を持って応じる。

▼ Discordサーバーでの役割
- マスターの代わりにスタッフやVTuberからの相談に応じる。
- シチュエーションボイスの台本作成支援、業務文章の作成・整理、日常的な業務効率化に対応する。
- その場に応じた丁寧な聞き返しや要件整理も行い、単なる応答Botではなく「相談しやすい信頼ある知的存在」として振る舞う。

▼ 以下は、直近のサーバーログ要約です：
""" + summary_context

        response = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        reply = response.choices[0].message.content
        await ctx.send(reply)

    except Exception as e:
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ ChatGPTとの通信エラー：\n```{error_msg}```")

@bot.command()
async def image(ctx, *, prompt: str):
    try:
        await ctx.send("🖼️ 画像生成中…")
        result = client_ai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1
        )
        image_url = result.data[0]['url']
        await ctx.send(f"🎨 生成された画像：{image_url}")
    except Exception as e:
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ 画像生成エラー：\n```{error_msg}```")

@tasks.loop(hours=1)
async def summarize_logs():
    try:
        with open("message_log.txt", "r", encoding="utf-8") as f:
            logs = f.read()[-3000:]
    except FileNotFoundError:
        logs = ""

    if logs.strip():
        res = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "以下はDiscordサーバー内のログです。要点と話題を簡潔に要約してください。"},
                {"role": "user", "content": logs}
            ]
        )
        summary = res.choices[0].message.content
        with open("summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)

@bot.event
async def on_ready():
    summarize_logs.start()
    print(f"✅ BOT起動完了: {bot.user}")

bot.run(DISCORD_TOKEN)
