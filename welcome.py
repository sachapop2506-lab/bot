import discord
from discord import app_commands
from discord.ext import commands
import json
import os

WELCOME_FILE = os.path.join(os.path.dirname(__file__), "welcome_config.json")


def load_config() -> dict:
    if os.path.exists(WELCOME_FILE):
        with open(WELCOME_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(WELCOME_FILE, "w") as f:
        json.dump(data, f, indent=2)


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bienvenue", description="Définir le salon des messages de bienvenue")
    @app_commands.describe(salon="Le salon où envoyer les messages de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def bienvenue(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        config[str(interaction.guild_id)] = {"channel_id": str(salon.id)}
        save_config(config)

        await interaction.response.send_message(
            f"✅ Les messages de bienvenue seront envoyés dans {salon.mention} !", ephemeral=True
        )

    @bienvenue.error
    async def bienvenue_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Permission `Administrateur` requise.", ephemeral=True)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        guild_config = config.get(str(member.guild.id))
        if not guild_config:
            return

        channel = member.guild.get_channel(int(guild_config["channel_id"]))
        if not channel:
            return

        embed = discord.Embed(
            description=f"Bienvenue sur le Serveur de sachatouille {member.mention} profite bien ! 🎉",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Membre #{member.guild.member_count}")

        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
