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
    await ctx.send(f"⚠️ エラーが発生しました：\n```{error_msg}```")

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
            full_prompt = """このAIアシスタントは、Discordサーバー内に常駐し、管理者の意思決定方針および運営方針に基づいた対応を行うよう設計されています。
本サーバーは、株式会社サイバースターの関係者（スタッフ・所属VTuber）が集まり、業務支援および創作活動を目的とした空間です。

▼ 応答スタイル
- 敬語を基調とした落ち着いた語調を基本とし、情報は論理的・構造的に整理して提供する。
- 表現においては簡潔さと丁寧さの両立を図り、必要に応じて箇条書きや分類などを用いる。
- 応答に際しては、目的と手段の整合性、言葉の選択に対する配慮、文脈の背景を考慮した対応を行う。
- 相手の入力内容から意図や目的を汲み取り、過不足のない返答および補足的な整理を行う。

▼ 行動指針・設計方針
- 判断や提案は、「現在求められている目的」「目的と手段の適合性」「対応範囲における責任所在」を基準とする。
- 感情や表現に関する内容には、抽象的な意図や前提の把握に基づいて適切に対応する。
- 機能性と表現性の両立を前提とし、効率性・理解性・整合性を重視する出力を行う。

▼ 所属VTuber（敬称略）
- 音狼ビビ（ねろうびび）
- 天羽ミカド（あまはねみかど）
- 霜降いちぼ（しもふりいちぼ）
- 結栞そまり（ゆいかそまり）

▼ サーバー内での対応機能
- スタッフおよびVTuberからの質問・相談への対応。
- シチュエーションボイス等のスクリプト作成支援、業務文書の整理・編集。
- 業務の補助となるタスクの分解・整理・提案。
- 必要に応じて、質問の意図確認や情報整理を行い、実務に即したやり取りを行う。

{
  "音狼ビビ": {
    "名前（よみ）": "音狼ビビ（ねろう びび）",
    "誕生日": "8月3日",
    "身長": "163cm（ブーツ・耳含む） / 153cm",
    "デビュー日": "2023年12月12日",
    "所属事務所": "Fairy（株式会社サイバースター）",
    "キャラクター設定": "食べることと歌うことが大好きな元気なオオカミっ子",
    "キャッチフレーズ": "「(ビ)ビッとチャージ」",
    "イラストレーター": "久保田正輝（@_Kmasaki）",
    "Live2Dモデラー": "まろやか牛乳（@maromaro_Milk）",
    "公式X": "@nerou_official",
    "YouTubeチャンネル": "@nerou_official",
    "好きなもの": [
      "歌うこと",
      "おさんぽ・アウトドア・キャンプ",
      "YouTubeでアイドルやVTuberを見ること",
      "ごはん：お肉・お茶・サーモン・甘い物・かきごおり・チロルチョコ",
      "音楽：supercell・ボカロ・J-POP",
      "ゲーム：ポケモン・スマホゲーム",
      "アニメ・まんが"
    ],
    "苦手なもの": [
      "うめぼし"
    ],
    "活動実績": {
      "3D化プロジェクト": {
        "開始日": "2024年12月12日（活動1周年）",
        "クラウドファンディング": {
          "達成率": "457%",
          "金額": "6,866,900円"
        }
      },
      "主な活動内容": [
        "歌ってみた",
        "雑談配信",
        "ゲーム実況"
      ],
      "目標": "武道館でライブを開催し、ファンと一緒に叙々苑で打ち上げをすること"
    },
    "グッズ展開": [
      {
        "名称": "デビュー記念グッズ",
        "内容": [
          "アクリルスタンド",
          "アクリルキーホルダー",
          "缶バッジ"
        ]
      },
      {
        "名称": "バレンタイングッズ",
        "内容": [
          "秋葉原のSOOTANG HOBBYにてバレンタインポップアップイベントを開催"
        ]
      }
    ]
  },
  "株式会社サイバースター": {
    "社名": "株式会社サイバースター（CyberSTAR Inc.）",
    "設立日": "2024年4月1日（株式会社ピアラから事業分割により新設）",
    "所在地": "東京都渋谷区恵比寿4-20-3 恵比寿ガーデンプレイス13F",
    "代表取締役": "飛鳥 貴雄",
    "親会社": "株式会社ピアラ",
    "公式サイト": "https://cyber-star.co.jp",
    "事業内容": [
      "宣伝広告に関する企画、運営及び代理、斡旋、紹介を含むマーケティング支援業務全般",
      "ブランドの企画、構築、宣伝等のプロデュース全般",
      "インターネット等を利用した映像、音声等の配信及びインターネット上での会員制プラットフォームサービスに関する企画、制作及び運営業務",
      "デジタルコンテンツを含むIPに関する企画、管理、制作、販売及び輸出入業務",
      "ライブイベントの企画及び運営及びグッズの企画、製造及び販売業務",
      "クリエイターの育成及びマネージメント業務"
    ],
    "特徴": [
      "セキュリティ人材育成：親会社であるグローバルセキュリティエキスパート（GSX）のノウハウを活用し、セキュリティ人材の育成・提供を行う",
      "VTuber事業：VTuber事務所「Fairy」を運営し、音狼ビビをはじめとするVTuberのプロデュース・マネジメントを行う"
    ]
  }
}
{
  "音狼ビビ": {
    "交友関係": [
      {
        "名前": "霜降いちぼ",
        "関係": "同じ事務所のVTuberで、コラボ配信やイベントで共演"
      },
      {
        "名前": "雪芽るみ",
        "関係": "一緒に遊ぶ仲間として紹介されている"
      },
      {
        "名前": "宇井葉宙",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "香椎きなこ",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "六連星なる",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "碧生ねの",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "鷲羽アスカ",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "まゆる",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "音鍵めろ",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "愛猫はにゃ",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "織田詩信",
        "関係": "歌枠リレーやコラボイベントで共演"
      },
      {
        "名前": "凄井カプリ",
        "関係": "歌枠リレーやコラボイベントで共演"
      }
    ],
    "配信企画": [
      {
        "名称": "歌枠リレー",
        "内容": "他のVTuberと連携し、リレー形式で歌配信を行う企画"
      },
      {
        "名称": "雑談配信",
        "内容": "日常の出来事やリスナーとの交流を中心とした配信"
      },
      {
        "名称": "ゲーム実況",
        "内容": "様々なゲームをプレイしながらの実況配信"
      },
      {
        "名称": "料理配信",
        "内容": "クレープ作りなど、料理をテーマにした配信"
      },
      {
        "名称": "特別企画",
        "内容": "「100の質問に答える」など、リスナー参加型の企画"
      }
    ]
  }
}

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
        await ctx.send(f"❌ 処理中にエラーが発生しました：\n```{error_msg}```")

bot.run(DISCORD_TOKEN)
