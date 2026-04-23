import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from utils import data_path
import random

# -------- MESSAGES -------- #
WELCOME_MESSAGES = [
    "🔥 {user} spawn dans l’arène ! Préparez-vous au chaos !",
    "🎮 {user} rejoint la bataille ! Qui va survivre ?",
    "💥 Un nouveau challenger apparaît : {user} !",
    "⚡ {user} entre dans la game… ça va faire mal !",
    "🏆 {user} débarque pour tout casser !",
    "🎯 {user} a rejoint la partie… objectif : domination !",
    "🧨 Attention ! {user} vient de spawn !",
    "👾 {user} rejoint le combat… ready ?",
]

LEAVE_MESSAGES = [
    "💀 {user} a été éliminé de l’arène...",
    "🥀 {user} rage quit… dommage !",
    "⚡ {user} quitte la game… une défaite ?",
    "👻 {user} a disparu dans le néant...",
    "🪦 {user} n’a pas survécu au combat...",
    "🚪 {user} a quitté le serveur… fuite stratégique ?",
    "💔 {user} abandonne la partie...",
]

# -------- FICHIER -------- #
WELCOME_FILE = data_path("welcome_config.json")


def load_config() -> dict:
    if os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(WELCOME_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -------- COG -------- #
class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------- CONFIG -------- #
    @app_commands.command(name="config-bienvenue", description="Configurer les salons arrivée/départ")
    @app_commands.describe(
        salon_bienvenue="Salon pour les arrivées",
        salon_depart="Salon pour les départs"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def config_bienvenue(
        self,
        interaction: discord.Interaction,
        salon_bienvenue: discord.TextChannel,
        salon_depart: discord.TextChannel
    ):
        config = load_config()

        config[str(interaction.guild_id)] = {
            "welcome_channel": salon_bienvenue.id,
            "leave_channel": salon_depart.id
        }

        save_config(config)

        await interaction.response.send_message(
            f"✅ Bienvenue → {salon_bienvenue.mention}\n❌ Départ → {salon_depart.mention}",
            ephemeral=True
        )

    @config_bienvenue.error
    async def config_bienvenue_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Permission `Administrateur` requise.",
                ephemeral=True
            )

    # -------- ARRIVÉE -------- #
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        guild_config = config.get(str(member.guild.id))
        if not guild_config:
            return

        channel_id = guild_config.get("welcome_channel")
        if not channel_id:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        message = random.choice(WELCOME_MESSAGES).format(user=member.mention)

        embed = discord.Embed(
            title="🎮 NOUVEAU BRAWLER !",
            description=message,
            color=discord.Color.orange()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"👥 Joueur #{member.guild.member_count}")

        await channel.send(embed=embed)

    # -------- DÉPART -------- #
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = load_config()
        guild_config = config.get(str(member.guild.id))
        if not guild_config:
            return

        channel_id = guild_config.get("leave_channel")
        if not channel_id:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        message = random.choice(LEAVE_MESSAGES).format(user=member.name)

        embed = discord.Embed(
            title="💀 BRAWLER HORS JEU",
            description=message,
            color=discord.Color.red()
        )

        await channel.send(embed=embed)


# -------- SETUP -------- #
async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
