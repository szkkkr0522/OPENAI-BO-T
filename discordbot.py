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
