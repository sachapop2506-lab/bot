import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
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

    # Sync commandes
@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"{len(synced)} commandes slash synchronisées")
    print("------")


@bot.command(name="hello")
async def hello(ctx):
    await ctx.send(f"Hey {ctx.author.mention}! 👋")


@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! 🏓 Latency: {latency}ms")


@bot.command(name="info")
async def info(ctx):
    embed = discord.Embed(
        title="Bot Info",
        description="A simple Discord bot built with discord.py",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Server", value=ctx.guild.name, inline=True)
    embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)


@bot.command(name="roll")
async def roll(ctx, sides: int = 6):
    import random
    result = random.randint(1, sides)
    await ctx.send(f"🎲 Rolled a d{sides}: **{result}**")


@bot.command(name="say")
@commands.has_permissions(manage_messages=True)
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)


@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🧹 Cleared {amount} messages.")
    await msg.delete(delay=3)


@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def sync(ctx):
    bot.tree.clear_commands(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} commandes slash synchronisées !")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use that command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument provided.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")




        


if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")
    bot.run(TOKEN)
