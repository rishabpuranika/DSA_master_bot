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

@bot.command()
async def dsa_cmd(ctx, *, topic: str):
    await dsa.handle_dsa(ctx, topic)

@bot.command()
async def resources_cmd(ctx, *, topic: str):
    await resources.handle_resources(ctx, topic)

@bot.command()
async def challenge_cmd(ctx):
    await challenge.handle_challenge(ctx)

async def run_update_in_executor():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, update_all_data)

# Scheduler using discord tasks
@tasks.loop(minutes=UPDATE_INTERVAL_MINUTES)
async def periodic_update():
    logging.info("Periodic update started: scraping Notion & enrichment sources.")
    await run_update_in_executor()
    logging.info("Periodic update finished.")

# run initial update before connecting
async def pre_run_update():
    logging.info("Performing initial data update...")
    await run_update_in_executor()
    logging.info("Initial update done.")

if __name__ == "__main__":
    asyncio.run(pre_run_update())
    bot.run(TOKEN)
