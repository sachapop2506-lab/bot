import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from googletrans import Translator

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    # 🌍 Traduction
    @app_commands.command(name="translate", description="Traduire un texte")
    @app_commands.describe(texte="Texte à traduire", langue="Langue cible (ex: en, fr, es)")
    async def translate(self, interaction: discord.Interaction, texte: str, langue: str):
        try:
            result = self.translator.translate(texte, dest=langue)
            await interaction.response.send_message(
                f"🌍 Traduction ({langue}) : {result.text}"
            )
        except:
            await interaction.response.send_message("❌ Erreur de traduction")

    # ⏱️ Minuteur
    @app_commands.command(name="timer", description="Créer un minuteur")
    @app_commands.describe(secondes="Durée en secondes")
    async def timer(self, interaction: discord.Interaction, secondes: int):
        await interaction.response.send_message(
            f"⏳ Timer lancé pour {secondes} secondes !"
        )

        await asyncio.sleep(secondes)

        await interaction.followup.send(
            f"⏰ {interaction.user.mention} Temps écoulé ! ({secondes}s)"
        )

    # 📊 Sondage
    @app_commands.command(name="poll", description="Créer un sondage")
    @app_commands.describe(question="Question du sondage")
    async def poll(self, interaction: discord.Interaction, question: str):
        await interaction.response.send_message(f"📊 **{question}**")

        message = await interaction.original_response()

        await message.add_reaction("👍")
        await message.add_reaction("👎")


async def setup(bot):
    await bot.add_cog(Utils(bot))
