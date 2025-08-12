# commands/resources.py
import json
import os
import discord

RES_FILE = "data/resources.json"

async def handle_resources(ctx, topic: str):
    key = topic.lower().replace(" ", "")
    if not os.path.exists(RES_FILE):
        await ctx.send("Resources not ready yet; initial sync running.")
        return

    with open(RES_FILE, "r") as f:
        res = json.load(f)

    if key not in res:
        # try substring match
        matches = [k for k in res.keys() if topic.lower() in k]
        if matches:
            key = matches[0]
        else:
            await ctx.send(f"❌ No resources found for **{topic}**.")
            return

    items = res[key]
    embed = discord.Embed(title=f"Resources for {key}", color=0x27AE60)
    text = "\n".join(f"[{name}]({url})" for name, url in items)
    embed.description = text
    await ctx.send(embed=embed)
