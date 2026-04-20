import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- EVENTS ---------- #

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Slash commands synced.")
    print("------")

# ---------- COMMANDES ---------- #

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hey {ctx.author.mention}! 👋")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms")

@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title="Bot Info",
        description="A simple Discord bot",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Server", value=ctx.guild.name)
    embed.add_field(name="Members", value=ctx.guild.member_count)
    await ctx.send(embed=embed)

@bot.command()
async def roll(ctx, sides: int = 6):
    import random
    await ctx.send(f"🎲 {random.randint(1, sides)}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"✅ {len(synced)} commandes synchronisées !")

# ---------- ERROR ---------- #

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ {error}")

# ---------- LOAD COGS ---------- #

async def load_extensions():
    extensions = [
        "giveaway",
        "ticket",
        "moderation",
        "welcome",
        "invites",
        "levels",
        "logs",
        "brawlstars",
        "fun"
    ]

    for ext in extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded {ext}")
        except Exception as e:
            print(f"❌ Error loading {ext}: {e}")

# ---------- MAIN ---------- #

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
