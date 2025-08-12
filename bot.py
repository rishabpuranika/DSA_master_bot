# bot.py
import os
import logging
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "1440"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user} (id: {bot.user.id})")
    logging.info("DSA Master Bot is now online and ready.")

# --- All command definitions remain the same ---
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


# This function will be called by the task loop
async def run_update_in_executor():
    loop = asyncio.get_running_loop()
    # Use run_in_executor to avoid blocking the bot's event loop
    await loop.run_in_executor(None, update_all_data)

@tasks.loop(minutes=UPDATE_INTERVAL_MINUTES)
async def periodic_update():
    logging.info("Periodic update started: Generating data with AI.")
    try:
        await run_update_in_executor()
        logging.info("Periodic update finished successfully.")
    except Exception as e:
        logging.error(f"Periodic update failed: {e}")

# --- MODIFIED: Main execution block ---
async def main():
    # Perform the initial data update first
    logging.info("Performing initial data update before starting the bot...")
    from utils.data_updater import update_all_data
    update_all_data()
    logging.info("Initial update completed successfully.")

    # Now, start the bot and the periodic task loop
    async with bot:
        periodic_update.start()
        await bot.start(TOKEN)

if __name__ == "__main__":
    # This setup ensures the initial update runs, then the bot logs in,
    # and the scheduled task waits for its next interval.
    from commands import dsa, resources, challenge
    from utils.data_updater import update_all_data
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot shut down by user.")