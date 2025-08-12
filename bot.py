# bot.py
import os
import json
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from utils.data_updater import update_all_data, get_random_leetcode_problem
from commands import dsa, resources, challenge

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "1440"))

logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id: {bot.user.id})")
    # Kick off periodic updater
    if not periodic_update.is_running():
        periodic_update.start()

# Fixed command names to match the actual function names
@bot.command(name="dsa")
async def dsa_command(ctx, *, topic: str):
    """Get DSA topic information. Usage: !dsa binary search"""
    await dsa.handle_dsa(ctx, topic)

@bot.command(name="resources")
async def resources_command(ctx, *, topic: str):
    """Get resources for a topic. Usage: !resources arrays"""
    await resources.handle_resources(ctx, topic)

@bot.command(name="challenge")
async def challenge_command(ctx):
    """Get a random LeetCode problem. Usage: !challenge"""
    await challenge.handle_challenge(ctx)

# Add help command
@bot.command(name="help_dsa")
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(title="DSA Master Bot Commands", color=0x3498DB)
    embed.add_field(name="!dsa <topic>", value="Get detailed info about a DSA topic", inline=False)
    embed.add_field(name="!resources <topic>", value="Get learning resources for a topic", inline=False)
    embed.add_field(name="!challenge", value="Get a random LeetCode problem", inline=False)
    embed.add_field(name="Examples", value="!dsa binary search\n!resources arrays\n!challenge", inline=False)
    await ctx.send(embed=embed)

async def run_update_in_executor():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, update_all_data)

# Scheduler using discord tasks
@tasks.loop(minutes=UPDATE_INTERVAL_MINUTES)
async def periodic_update():
    logging.info("Periodic update started: scraping Notion & enrichment sources.")
    try:
        await run_update_in_executor()
        logging.info("Periodic update finished successfully.")
    except Exception as e:
        logging.error(f"Periodic update failed: {e}")

# run initial update before connecting
async def pre_run_update():
    logging.info("Performing initial data update...")
    try:
        await run_update_in_executor()
        logging.info("Initial update completed successfully.")
    except Exception as e:
        logging.error(f"Initial update failed: {e}")

if __name__ == "__main__":
    asyncio.run(pre_run_update())
    bot.run(TOKEN)