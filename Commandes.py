import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from googletrans import Translator

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

translator = Translator()

# ✅ Traduction
@tree.command(name="translate", description="Traduire un texte")
async def translate(interaction: discord.Interaction, texte: str, langue: str):
    try:
        traduction = translator.translate(texte, dest=langue)
        await interaction.response.send_message(
            f"🌍 Traduction ({langue}) : {traduction.text}"
        )
    except:
        await interaction.response.send_message("❌ Erreur de traduction")

# ⏱️ Minuteur
@tree.command(name="timer", description="Créer un minuteur")
async def timer(interaction: discord.Interaction, secondes: int):
    await interaction.response.send_message(f"⏳ Timer lancé pour {secondes} secondes !")
    
    await asyncio.sleep(secondes)
    
    await interaction.followup.send(f"⏰ Temps écoulé ! ({secondes}s)")

# 📊 Sondage
@tree.command(name="poll", description="Créer un sondage")
async def poll(interaction: discord.Interaction, question: str):
    message = await interaction.response.send_message(f"📊 **{question}**", fetch_reply=True)
    
    await message.add_reaction("👍")
    await message.add_reaction("👎")

# Sync des commandes
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {bot.user}")

bot.run("TON_TOKEN_ICI")
