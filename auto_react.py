import discord
from discord import app_commands
from discord.ext import commands
import json
import os
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

class AutoReact(commands.GroupCog, name="autoreact"):
    def __init__(self, bot):
        self.bot = bot

    # 🔥 FIX IMPORTANT
    async def cog_load(self):
        self.bot.tree.add_command(self.__class__)

    # ─── COMMANDES ─────────────────────────

    @app_commands.command(name="ajouter")
    async def ajouter(self, interaction: discord.Interaction, salon: discord.TextChannel, emojis: str = None, message: str = None):
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

    @app_commands.command(name="retirer")
    async def retirer(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        ar = config.get(str(interaction.guild_id), {}).get("autoreact", {})

        if str(salon.id) not in ar:
            await interaction.response.send_message("❌ Rien à retirer", ephemeral=True)
            return

        del ar[str(salon.id)]
        save_config(config)

        await interaction.response.send_message("✅ Retiré", ephemeral=True)

    @app_commands.command(name="liste")
    async def liste(self, interaction: discord.Interaction):
        config = load_config()
        ar = config.get(str(interaction.guild_id), {}).get("autoreact", {})

        if not ar:
            await interaction.response.send_message("❌ Aucun config", ephemeral=True)
            return

        msg = ""
        for channel_id, data in ar.items():
            channel = interaction.guild.get_channel(int(channel_id))
            name = channel.mention if channel else f"Salon supprimé ({channel_id})"
            msg += f"{name} → {' '.join(data.get('emojis', []))}\n"

        await interaction.response.send_message(msg)

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

        key = f"{message.guild.id}-{message.channel.id}"
        now = time.time()

        if key in cooldowns and now - cooldowns[key] < channel_config.get("cooldown", 5):
            return

        cooldowns[key] = now

        for emoji in channel_config.get("emojis", []):
            try:
                await message.add_reaction(emoji)
            except:
                pass

        if channel_config.get("message"):
            msg = channel_config["message"].replace("{user}", message.author.mention)
            await message.channel.send(msg)

async def setup(bot):
    await bot.add_cog(AutoReact(bot))
