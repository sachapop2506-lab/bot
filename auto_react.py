import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio

class FakeMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fakeban", description="Fake ban un utilisateur")
    @app_commands.describe(user="Utilisateur à troll")
    async def fakeban(self, interaction: discord.Interaction, user: discord.Member):
        
        # message fake ban
        embed = discord.Embed(
            title="🚨 Bannissement",
            description=f"{user.mention} a été banni du serveur.",
            color=0xe74c3c
        )

        await interaction.response.send_message(embed=embed)

        # attente
        await asyncio.sleep(2)

        # message troll
        await interaction.followup.send(
            f"😂 non je rigole {user.mention}"
        )

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(FakeMod(bot))
