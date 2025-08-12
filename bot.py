# bot.py
import os
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# Correctly read the interval in hours and convert to minutes for the task
UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "24"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id: {bot.user.id})")
    logging.info("DSA Master Bot is now online and ready.")
    # Start the periodic update task only after the bot is ready
    if not periodic_update.is_running():
        periodic_update.start()

# --- Command definitions remain the same ---
@bot.command(name="dsa")
async def dsa_command(ctx, *, topic: str):
    await dsa.handle_dsa(ctx, topic)

@bot.command(name="resources")
async def resources_command(ctx, *, topic: str):
    await resources.handle_resources(ctx, topic)

@bot.command(name="challenge")
async def challenge_command(ctx):
    await challenge.handle_challenge(ctx)

@bot.command(name="help_dsa")
async def help_command(ctx):
    embed = discord.Embed(title="DSA Master Bot Commands", color=0x3498DB)
    embed.add_field(name="!dsa <topic>", value="Get detailed info about a DSA topic", inline=False)
    embed.add_field(name="!resources <topic>", value="Get learning resources for a topic", inline=False)
    embed.add_field(name="!challenge", value="Get a random LeetCode problem", inline=False)
    await ctx.send(embed=embed)

# --- Task loop and main execution block ---
async def run_update_in_executor(force=False):
    loop = asyncio.get_running_loop()
    # Use run_in_executor to run the blocking update function
    await loop.run_in_executor(None, update_all_data, force)

# Run the task every N hours as defined in your environment
@tasks.loop(hours=UPDATE_INTERVAL_HOURS)
async def periodic_update():
    logging.info("Periodic update check started.")
    try:
        await run_update_in_executor()
        logging.info("Periodic update check finished.")
    except Exception as e:
        logging.error(f"Periodic update failed: {e}")

async def main():
    # Perform the initial data update only if necessary
    logging.info("Performing initial data check before starting the bot...")
    from utils.data_updater import update_all_data
    # On the first run, force an update if data doesn't exist.
    update_all_data(force_update=not os.path.exists("data/dsa_topics.json"))
    logging.info("Initial data check completed.")

    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    from commands import dsa, resources, challenge
    from utils.data_updater import update_all_data
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shut down by user.")