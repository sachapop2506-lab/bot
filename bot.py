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


# ─── LOAD EXTENSIONS ─────────────────────────

async def main():
    async with bot:
        await bot.load_extension("giveaway")
        await bot.load_extension("ticket")
        await bot.load_extension("moderation")
        await bot.load_extension("welcome")
        await bot.load_extension("invites")
        await bot.load_extension("levels")
        await bot.load_extension("logs")
        await bot.load_extension("brawlstars")
        await bot.load_extension("auto_react")
        await bot.load_extension("fun")

        await bot.start(TOKEN)


# ─── READY + SYNC ─────────────────────────

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"{len(synced)} commandes slash synchronisées")
    print("------")


# ─── COMMANDES CLASSIQUES ─────────────────────────

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong 🏓 {latency}ms")


@bot.command()
async def hello(ctx):
    await ctx.send(f"Hey {ctx.author.mention} 👋")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 {amount} messages supprimés")
    await msg.delete(delay=3)


# ─── ERROR HANDLER ─────────────────────────

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Permissions manquantes.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argument manquant: `{error.param.name}`")
    else:
        await ctx.send(f"❌ Erreur: {error}")


# ─── RUN ─────────────────────────

if not TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN manquant")

asyncio.run(main())
