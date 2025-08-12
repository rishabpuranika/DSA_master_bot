# commands/challenge.py
import discord
import asyncio
from utils.data_updater import get_random_leetcode_problem

async def handle_challenge(ctx):
    # Show loading message
    loading_msg = await ctx.send("🎯 Fetching a random LeetCode problem...")
    
    try:
        # Get problem in a separate thread to avoid blocking
        loop = asyncio.get_event_loop()
        problem = await loop.run_in_executor(None, get_random_leetcode_problem)
        
        if not problem:
            await loading_msg.edit(content="❌ Couldn't fetch LeetCode problem right now — try again later.")
            return

        # Create embed
        difficulty_colors = {
            "Easy": 0x00B74A,    # Green
            "Medium": 0xFFB800,   # Orange  
            "Hard": 0xFF2D55      # Red
        }
        
        difficulty = problem.get('difficulty', 'Unknown')
        color = difficulty_colors.get(difficulty, 0x007ACC)
        
        embed = discord.Embed(
            title=f"🎯 {problem['title']}", 
            description=f"**Difficulty:** {difficulty}",
            color=color,
            url=problem['url']
        )
        
        embed.add_field(
            name="🔗 Solve Now", 
            value=f"[Click here to solve on LeetCode]({problem['url']})", 
            inline=False
        )
        
        # Add difficulty-based encouragement
        encouragements = {
            "Easy": "Great for warming up! 🚀",
            "Medium": "Perfect for skill building! 💪",
            "Hard": "Challenge mode activated! 🔥"
        }
        
        if difficulty in encouragements:
            embed.add_field(
                name="💡 Tip", 
                value=encouragements[difficulty], 
                inline=False
            )
        
        embed.set_footer(text="Good luck! Use !challenge for another problem.")
        
        await loading_msg.edit(content="", embed=embed)
        
    except Exception as e:
        await loading_msg.edit(content="❌ Something went wrong while fetching the problem. Please try again!")
        print(f"Challenge command error: {e}")