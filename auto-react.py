import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import time
from utils import data_path

FUN_CONFIG_FILE = data_path("fun_config.json")

def load_config():
    if os.path.exists(FUN_CONFIG_FILE):
        with open(FUN_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(FUN_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

cooldowns = {}

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.route_state = {}
        self.bot.tree.add_command(self.autoreact_group)

    # ─── AUTOREACT ─────────────────────────

    autoreact_group = app_commands.Group(
        name="autoreact",
        description="Réactions automatiques"
    )

    @autoreact_group.command(name="ajouter")
    async def autoreact_ajouter(self, interaction: discord.Interaction, salon: discord.TextChannel, emojis: str = None, message: str = None):

        if not emojis and not message:
            await interaction.response.send_message("❌ Mets un emoji ou un message", ephemeral=True)
            return

        config = load_config()
        guild = config.setdefault(str(interaction.guild_id), {})
        ar = guild.setdefault("autoreact", {})

        ar[str(salon.id)] = {
            "emojis": emojis.split() if emojis else [],
            "message": message,
            "cooldown": 5
        }

        save_config(config)

        await interaction.response.send_message("✅ Ajouté", ephemeral=True)

    # ─── LISTENER ─────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        config = load_config()
        guild_config = config.get(str(message.guild.id), {})
        channel_config = guild_config.get("autoreact", {}).get(str(message.channel.id))

        if not channel_config:
            return

        # cooldown
        key = f"{message.guild.id}-{message.channel.id}"
        now = time.time()

        if key in cooldowns and now - cooldowns[key] < channel_config.get("cooldown", 5):
            return

        cooldowns[key] = now

        # emojis
        for emoji in channel_config.get("emojis", []):
            try:
                await message.add_reaction(emoji)
            except:
                pass

        # message
        if channel_config.get("message"):
            msg = channel_config["message"]
            msg = msg.replace("{user}", message.author.mention)
            await message.channel.send(msg)

async def setup(bot):
    await bot.add_cog(FunCog(bot))
