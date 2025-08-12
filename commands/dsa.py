# commands/dsa.py
import json
import os
import discord

DATA_FILE = "data/dsa_topics.json"

async def handle_dsa(ctx, topic: str):
    key = topic.lower().replace(" ", "")
    if not os.path.exists(DATA_FILE):
        await ctx.send("Data not ready yet — please wait while the bot finishes initial sync.")
        return

    with open(DATA_FILE, "r") as f:
        db = json.load(f)

    if key not in db:
        # try fuzzy match small fallback
        matches = [k for k in db.keys() if topic.lower() in k]
        if matches:
            key = matches[0]
        else:
            await ctx.send(f"❌ Topic **{topic}** not found. Try simpler name or check `!resources {topic}`.")
            return

    info = db[key]
    embed = discord.Embed(title=info.get("title", topic), description=info.get("short", ""), color=0x2E86C1)
    embed.add_field(name="Time Complexity", value=info.get("time", "N/A"), inline=False)
    embed.add_field(name="Space Complexity", value=info.get("space", "N/A"), inline=False)

    code = info.get("code", "")
    if code:
        # keep code field short, else attach as file
        if len(code) < 1000:
            embed.add_field(name="C++ Snippet", value=f"```cpp\n{code}\n```", inline=False)
        else:
            embed.add_field(name="C++ Snippet", value="Code is long — see top resources.", inline=False)

    links = info.get("links", [])
    if links:
        value = "\n".join(f"[{t}]({u})" for t, u in links[:3])
        embed.add_field(name="Top Resources", value=value, inline=False)

    await ctx.send(embed=embed)
