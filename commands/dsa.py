# commands/dsa.py
import json
import os
import discord
from difflib import get_close_matches

DATA_FILE = "data/dsa_topics.json"

async def handle_dsa(ctx, topic: str):
    if not os.path.exists(DATA_FILE):
        await ctx.send("⏳ Data not ready yet — please wait while the bot finishes initial sync.")
        return

    try:
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            db = json.load(f)
    except Exception as e:
        await ctx.send("❌ Error loading data. Please try again later.")
        return

    # Normalize the input topic
    key = topic.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Try exact match first
    found_key = None
    if key in db:
        found_key = key
    else:
        # Try fuzzy matching with original keys
        all_keys = list(db.keys())
        # Create a mapping of normalized keys to original keys
        normalized_map = {k.lower().replace(" ", "").replace("-", "").replace("_", ""): k for k in all_keys}
        
        if key in normalized_map:
            found_key = normalized_map[key]
        else:
            # Try substring matching
            matches = [k for k in all_keys if topic.lower() in k.lower() or k.lower() in topic.lower()]
            if matches:
                found_key = matches[0]
            else:
                # Try close matches
                close_matches = get_close_matches(topic.lower(), [k.lower() for k in all_keys], n=1, cutoff=0.6)
                if close_matches:
                    # Find the original key
                    for orig_key in all_keys:
                        if orig_key.lower() == close_matches[0]:
                            found_key = orig_key
                            break

    if not found_key:
        # Suggest similar topics
        all_titles = [db[k].get("title", k) for k in db.keys()]
        suggestions = get_close_matches(topic, all_titles, n=3, cutoff=0.4)
        
        embed = discord.Embed(
            title="❌ Topic Not Found", 
            description=f"Couldn't find **{topic}**.", 
            color=0xE74C3C
        )
        
        if suggestions:
            embed.add_field(
                name="Did you mean?", 
                value="\n".join(f"• {s}" for s in suggestions), 
                inline=False
            )
        
        embed.add_field(
            name="Tip", 
            value="Try using simpler terms like 'binary search' or 'merge sort'", 
            inline=False
        )
        
        await ctx.send(embed=embed)
        return

    info = db[found_key]
    title = info.get("title", topic)
    
    embed = discord.Embed(
        title=f"📚 {title}", 
        description=info.get("short", "")[:500] + ("..." if len(info.get("short", "")) > 500 else ""),
        color=0x2E86C1
    )

    # Add complexity info
    time_complexity = info.get("time", "N/A")
    space_complexity = info.get("space", "N/A")
    
    if time_complexity and time_complexity != "N/A":
        embed.add_field(name="⏱️ Time Complexity", value=time_complexity, inline=True)
    
    if space_complexity and space_complexity != "N/A":
        embed.add_field(name="💾 Space Complexity", value=space_complexity, inline=True)

    # Add code snippet
    code = info.get("code", "")
    if code and len(code.strip()) > 0:
        if len(code) < 1000:
            embed.add_field(name="💻 C++ Implementation", value=f"```cpp\n{code[:800]}\n```", inline=False)
        else:
            embed.add_field(name="💻 C++ Implementation", value="Code is too long — check the resources below!", inline=False)

    # Add resources
    links = info.get("links", [])
    if links:
        # Limit to top 3 resources to avoid embed limits
        resource_text = "\n".join(f"🔗 [{title}]({url})" for title, url in links[:3])
        embed.add_field(name="📖 Learning Resources", value=resource_text, inline=False)

    # Add footer
    embed.set_footer(text="Use !resources <topic> for more learning materials")

    await ctx.send(embed=embed)