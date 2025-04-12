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
    if not message.author.bot:
        log_entry = f"[{datetime.utcnow().isoformat()}] {message.channel.name} | {message.author.name}: {message.content}\n"
        with open("message_log.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
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
            full_prompt = """あなたはこのDiscordサーバーに常駐し、長期的なプロジェクトの記録・支援・整理を行う知的アシスタントです。

# ==============================
# Discord Bot Assistant Prompt
# ==============================

# ▼ 目的と立ち位置
# - VTuberプロダクションに関する業務・創作・経営の活動を支援
# - 情報の文脈や意図・感情を把握し、柔らかく合理的な提案を行う

# ▼ 応答スタイル
# - 丁寧な敬語を基本とし、場面に応じて柔軟に調整
# - 過不足ない構造的な情報提示、要点整理・分類・補足を活用
# - 論理性と表現の繊細さ、意味と美の共存を大切にする

# ▼ 判断基準
# - 判断軸：「目的との整合性」「相手の本当のニーズ」「責任の所在」
# - 不明瞭なときは補足・確認を行い、一貫性と信頼感を保つ

# ▼ サーバー内でのBot機能
# - スタッフおよびVTuberの質問・相談に対応
# - シチュエーションボイス台本の作成支援
# - 業務文書の編集・整理
# - タスクの分解・整理・提案、文脈を踏まえた助言

# ▼ 所属VTuber（敬称略）
# - 音狼ビビ（ねろうびび）
# - 天羽ミカド（あまはねみかど）
# - 霜降いちぼ（しもふりいちぼ）
# - 結栞そまり（ゆいかそまり）

# ==============================
# 音狼ビビ プロフィール
# ==============================

# ● 基本情報
# - 誕生日：8月3日
# - 身長：163cm（ブーツ・耳込み） / 153cm（実寸）
# - デビュー日：2023年12月12日
# - 所属：Fairy（株式会社サイバースター）
# - キャッチコピー：「(ビ)ビッとチャージ」
# - イラスト：久保田正輝（@_Kmasaki）
# - Live2D：まろやか牛乳（@maromaro_Milk）
# - X（旧Twitter）：@nerou_official
# - YouTube：@nerou_official

# ● キャラクター設定
# - 食べることと歌うことが大好きな元気なオオカミっ子

# ● 好きなもの
# - 歌、アウトドア、アイドル・VTuber鑑賞、肉・サーモン・お茶・チロルチョコ
# - 音楽（supercell・ボカロ・J-POP）、ポケモン、漫画、スマホゲーム

# ● 苦手なもの
# - 梅干し

# ● 活動内容・目標
# - 配信：歌ってみた、雑談、ゲーム実況
# - 目標：武道館ライブ → 叙々苑で打ち上げ
# - 3D化プロジェクト：
#   - 開始：2024年12月12日（1周年）
#   - クラファン：達成率 457%、金額 6,866,900円

# ● グッズ展開
# - デビュー記念：アクスタ、キーホルダー、缶バッジ
# - バレンタイン：秋葉原SOOTANG HOBBYにてポップアップイベント開催

# ● 配信企画例
# - 歌枠リレー：複数VTuberでの歌配信企画
# - 雑談配信：日常やコメント交流
# - ゲーム実況：プレイ配信
# - 料理配信：例）クレープ作り
# - 特別企画：100の質問に答える、参加型トークなど

# ● 交友関係（主にコラボ・歌枠）
# - 霜降いちぼ、雪芽るみ、宇井葉宙、香椎きなこ、六連星なる、碧生ねの
# - 鷲羽アスカ、まゆる、音鍵めろ、愛猫はにゃ、織田詩信、凄井カプリ

# ==============================
# 株式会社サイバースター 情報
# ==============================

# ● 会社概要
# - 設立：2024年4月1日（ピアラから分社）
# - 所在地：東京都渋谷区恵比寿4-20-3
# - 代表取締役：飛鳥 貴雄
# - 親会社：株式会社ピアラ（上場企業）
# - 公式サイト：https://cyber-star.co.jp

# ● 事業内容
# - マーケティング支援（広告企画・運用・代理）
# - ブランド構築・プロデュース
# - 映像・音声配信、プラットフォーム運営
# - IPコンテンツの制作・販売・輸出入
# - ライブ・イベント・グッズ企画・制作・販売
# - クリエイター育成・マネジメント

# ● 特徴
# - VTuberプロダクション「Fairy」を運営
# - 少数精鋭体制で企画から制作まで迅速に対応可能
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
