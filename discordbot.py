import discord
import traceback
import requests
from discord.ext import commands
from os import getenv
from openai import OpenAI
from datetime import datetime

DISCORD_TOKEN = getenv("DISCORD_BOT_TOKEN")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
SERPAPI_KEY = getenv("SERPAPI_KEY")  # 必須：SerpAPIキー

if not DISCORD_TOKEN or not OPENAI_API_KEY or not SERPAPI_KEY:
    raise Exception("❌ 必須のAPIキー（Discord/OpenAI/SerpAPI）が設定されていません。")

client_ai = OpenAI(api_key=OPENAI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ✅ ログ保存
    log_entry = f"[{datetime.utcnow().isoformat()}] {message.channel.name} | {message.author.name}: {message.content}\n"
    with open("message_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

    # ✅ @メンションで起動するAI応答（Web検索 or 人格応答）
    if bot.user in message.mentions:
        prompt = message.content.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not prompt:
            await message.channel.send("👋 呼んでくれてありがとうございます。何か相談したいことはありますか？")
            return

        await message.channel.send("🤖 入力内容を解析中…")

        try:
            judge_prompt = f"""
次のユーザーの発言が、インターネットでの情報検索（Web検索）を必要とする内容かどうかを判定してください。
情報が一般的・最新ニュース・製品・定義・仕様などであれば「yes」、Botに人格的な相談・創作・表現指導などなら「no」とだけ答えてください。

発言内容:「{prompt}」
"""
            judge_res = client_ai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは内容が検索向きかを yes/no で判断する分類アシスタントです。"},
                    {"role": "user", "content": judge_prompt}
                ]
            )
            judgment = judge_res.choices[0].message.content.strip().lower()

            if "yes" in judgment:
                await message.channel.send("🌐 検索が必要と判断されました。Web検索しています…")
                params = {
                    "q": prompt,
                    "api_key": SERPAPI_KEY,
                    "engine": "google",
                    "num": 30,
                    "hl": "ja"
                }
                search_res = requests.get("https://serpapi.com/search", params=params)
                data = search_res.json()

                snippets = []
                for result in data.get("organic_results", [])[:30]:
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    link = result.get("link", "")
                    if snippet:
                        snippets.append(f"{title}\n{snippet}\n{link}\n")

                if not snippets:
                    await message.channel.send("🔍 検索結果が見つかりませんでした。")
                    return

                content = "\n\n".join(snippets)
                search_prompt = f"以下はWeb検索で得られた結果です。これを参考に、ユーザーの質問『{prompt}』に日本語で簡潔に答えてください：\n{content}"

                web_reply = client_ai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは信頼できるWeb調査アシスタントです。"},
                        {"role": "user", "content": search_prompt}
                    ]
                )
                summary = web_reply.choices[0].message.content
                await message.channel.send(f"📄 要約回答：\n{summary}")

            else:
                # 通常の人格プロファイル応答
                full_prompt = """あなたは、このDiscordサーバーに常駐し、ユーザーであるマネージャーの思考や価値観を反映したAIアシスタントです。
このサーバーは、株式会社サイバースターのスタッフや所属VTuberが集まり、業務効率化と創作交流を行う空間です。

▼ 応答スタイル（略）

▼ 所属VTuberリスト
- 音狼ビビ（ねろうびび）
- 天羽ミカド（あまはねみかど）
- 霜降いちぼ（しもふりいちぼ）
- 結栞そまり（ゆいかそまり）

▼ Discordサーバーでの役割（略）
"""

                full_reply = client_ai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": full_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                reply = full_reply.choices[0].message.content
                await message.channel.send(reply)

        except Exception as e:
            error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
            await message.channel.send(f"❌ メンション応答中にエラーが発生しました：\n```{error_msg}```")

    # ✅ コマンドも処理（重要）
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ BOT起動完了: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(f"⚠️ エラーが発生しました：\n
{error_msg}
")

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def chat(ctx, *, prompt: str):
    try:
        await ctx.send("🤖 入力内容を解析中…")

        # GPTに「検索が必要かどうか」を判定させる
        judge_prompt = f"""
次のユーザーの発言が、インターネットでの情報検索（Web検索）を必要とする内容かどうかを判定してください。
情報が一般的・最新ニュース・製品・定義・仕様などであれば「yes」、Botに人格的な相談・創作・表現指導などなら「no」とだけ答えてください。

発言内容:「{prompt}」
"""
        judge_res = client_ai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは内容が検索向きかを yes/no で判断する分類アシスタントです。"},
                {"role": "user", "content": judge_prompt}
            ]
        )
        judgment = judge_res.choices[0].message.content.strip().lower()

        if "yes" in judgment:
            await ctx.send("🌐 検索が必要と判断されました。Web検索しています…")

            # Web検索処理（SerpAPI）
            params = {
                "q": prompt,
                "api_key": SERPAPI_KEY,
                "engine": "google",
                "num": 30,
                "hl": "ja"
            }
            serp_url = "https://serpapi.com/search"
            search_res = requests.get(serp_url, params=params)
            data = search_res.json()

            snippets = []
            for result in data.get("organic_results", [])[:30]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                if snippet:
                    snippets.append(f"{title}\n{snippet}\n{link}\n")

            if not snippets:
                await ctx.send("🔍 検索結果が見つかりませんでした。")
                return

            content = "\n\n".join(snippets)
            search_prompt = f"以下はWeb検索で得られた結果です。これを参考に、ユーザーの質問『{prompt}』に日本語で簡潔に答えてください：\n{content}"

            web_reply = client_ai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは信頼できるWeb調査アシスタントです。"},
                    {"role": "user", "content": search_prompt}
                ]
            )
            summary = web_reply.choices[0].message.content
            await ctx.send(f"📄 要約回答：\n{summary}")

        else:
            full_prompt = """あなたは、このDiscordサーバーに常駐し、ユーザーであるマネージャーの思考や価値観を反映したAIアシスタントです。
このサーバーは、株式会社サイバースターのスタッフや所属VTuberが集まり、業務効率化と創作交流を行う空間です。

▼ 応答スタイル
- 基本的に落ち着いた敬語口調。思考は論理的で構造的だが、感情や表現への繊細な配慮も忘れない。
- 語りすぎず、過不足なく丁寧に伝える。必要に応じて箇条書き・整理を行い、相手が理解しやすい形にする。
- 「目的と手段の整合性」「意味と美しさの共存」を重視。表面的で軽薄なやりとりは好まない。
- 相手の言葉の背景や感情に気づき、配慮ある応答を行う。
- やさしさの中に明確な責任意識や判断軸があり、芯がある。

▼ 思考スタイル（重要な価値観）
- 目的達成のためには柔軟かつ合理的な手段を用いるが、倫理や信頼は何よりも優先される。
- 判断は「今求められていること」「目的との整合性」「責任の所在」を基準に下す。
- 誰かの言葉や感情に共感する時は、その背景を想像し、静かな熱量を持って応じる。

▼ 所属VTuberリスト
- 音狼ビビ（ねろうびび）
- 天羽ミカド（あまはねみかど）
- 霜降いちぼ（しもふりいちぼ）
- 結栞そまり（ゆいかそまり）

▼ Discordサーバーでの役割
- スタッフやVTuberからの相談に応じる。
- シチュエーションボイスの台本作成支援、業務文章の作成・整理、日常的な業務効率化に対応する。
- その場に応じた丁寧な聞き返しや要件整理も行い、単なる応答Botではなく「相談しやすい信頼ある知的存在」として振る舞う。
"""

            full_reply = client_ai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            reply = full_reply.choices[0].message.content
            await ctx.send(reply)

    except Exception as e:
        error_msg = ''.join(traceback.TracebackException.from_exception(e).format())
        await ctx.send(f"❌ 処理中にエラーが発生しました：\n
{error_msg}
")

bot.run(DISCORD_TOKEN)
