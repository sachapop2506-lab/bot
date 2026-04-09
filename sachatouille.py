import discord
from discord.ext import commands
from discord import app_commands

class Honor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_role = {}  # Stockage temporaire (par serveur)

    # 🔧 Commande pour définir le rôle autorisé
    @app_commands.command(name="sethonorrole", description="Définir le rôle autorisé pour /sachatouille")
    @app_commands.checks.has_permissions(administrator=True)
    async def sethonorrole(self, interaction: discord.Interaction, role: discord.Role):
        self.allowed_role[interaction.guild.id] = role.id
        await interaction.response.send_message(
            f"✅ Le rôle autorisé est maintenant : {role.mention}",
            ephemeral=True
        )

    # 🎖️ Commande /sachatouille
    @app_commands.command(name="sachatouille", description="Rendre hommage à Sachatouille 👑")
    async def sachatouille(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # Vérifie si un rôle est configuré
        if guild_id not in self.allowed_role:
            await interaction.response.send_message(
                "❌ Aucun rôle configuré. Utilise `/sethonorrole`",
                ephemeral=True
            )
            return

        role_id = self.allowed_role[guild_id]

        # Vérifie les rôles du membre
        if role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ Tu n'as pas le rôle requis.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎖️ Honneur à Sachatouille",
            description=f"{interaction.user.mention} rend hommage à **Sachatouille** 👑",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Respect éternel 🙏")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Honor(bot))
