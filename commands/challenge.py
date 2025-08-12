# commands/challenge.py
import discord
from utils.data_updater import get_random_leetcode_problem

async def handle_challenge(ctx):
    p = get_random_leetcode_problem()
    if not p:
        await ctx.send("Couldn't fetch LeetCode problem right now — try again later.")
        return

    embed = discord.Embed(title=f"🎯 {p['title']}", description=f"Difficulty: {p['difficulty']}", color=0xE67E22)
    embed.add_field(name="Link", value=p["url"], inline=False)
    await ctx.send(embed=embed)
