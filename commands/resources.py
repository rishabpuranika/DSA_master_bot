# commands/resources.py
import json
import os
import discord
from difflib import get_close_matches

RES_FILE = "data/resources.json"

async def handle_resources(ctx, topic: str):
    if not os.path.exists(RES_FILE):
        await ctx.send("⏳ Resources not ready yet; initial sync running.")
        return

    try:
        with open(RES_FILE, "r", encoding='utf-8') as f:
            res = json.load(f)
    except Exception as e:
        await ctx.send("❌ Error loading resources. Please try again later.")
        return

    # Normalize the input topic
    key = topic.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Try exact match first
    found_key = None
    if key in res:
        found_key = key
    else:
        # Try fuzzy matching
        all_keys = list(res.keys())
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
                    for orig_key in all_keys:
                        if orig_key.lower() == close_matches[0]:
                            found_key = orig_key
                            break

    if not found_key:
        # Suggest similar topics
        suggestions = get_close_matches(topic, list(res.keys()), n=3, cutoff=0.4)
        
        embed = discord.Embed(
            title="❌ Resources Not Found", 
            description=f"No resources found for **{topic}**.",
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
            value="Try !dsa <topic> for detailed information, or use simpler terms.", 
            inline=False
        )
        
        await ctx.send(embed=embed)
        return

    items = res[found_key]
    
    if not items:
        await ctx.send(f"❌ No resources available for **{topic}** yet.")
        return

    embed = discord.Embed(
        title=f"📖 Resources for {found_key.replace('[]', '').replace('()', '').title()}", 
        color=0x27AE60
    )
    
    # Group resources by type
    youtube_links = []
    article_links = []
    other_links = []
    
    for name, url in items:
        if "youtube" in url.lower() or "youtu.be" in url.lower():
            youtube_links.append((name, url))
        elif any(site in url.lower() for site in ["geeksforgeeks", "takeuforward", "leetcode", "codeforces"]):
            article_links.append((name, url))
        else:
            other_links.append((name, url))
    
    # Add sections
    if youtube_links:
        yt_text = "\n".join(f"🎥 [{name}]({url})" for name, url in youtube_links[:3])
        embed.add_field(name="Video Tutorials", value=yt_text, inline=False)
    
    if article_links:
        article_text = "\n".join(f"📄 [{name}]({url})" for name, url in article_links[:3])
        embed.add_field(name="Articles & Practice", value=article_text, inline=False)
    
    if other_links:
        other_text = "\n".join(f"🔗 [{name}]({url})" for name, url in other_links[:2])
        embed.add_field(name="Additional Resources", value=other_text, inline=False)
    
    # If we have more resources, mention it
    total_resources = len(items)
    if total_resources > 8:
        embed.set_footer(text=f"Showing top resources ({total_resources} total available)")
    
    await ctx.send(embed=embed)