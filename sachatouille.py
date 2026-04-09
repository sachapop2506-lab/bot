import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")  # Railway
ROLE_ID = None  # sera modifié dynamiquement

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(e)
    print(f"Connecté en tant que {bot.user}")

# 🔒 Vérifie si l'utilisateur est admin (chef)
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# 📜 Commande /sachatouille
@bot.tree.command(name="sachatouille", description="Hommage à Sachatouille")
async def sachatouille(interaction: discord.Interaction):
    global ROLE_ID

    if ROLE_ID is None:
        await interaction.response.send_message(
            "⚠️ Aucun rôle configuré. Utilise /setrole",
            ephemeral=True
        )
        return

    role_ids = [role.id for role in interaction.user.roles]

    if ROLE_ID in role_ids:
        await interaction.response.send_message(
            "✨ Gloire éternelle à Sachatouille, maître incontesté de la chatouille cosmique ! ✨"
        )
    else:
        await interaction.response.send_message(
            "❌ Tu n'as pas le rôle nécessaire.",
            ephemeral=True
        )

# 👑 Commande pour définir le rôle
@bot.tree.command(name="setrole", description="Définir le rôle autorisé")
@app_commands.describe(role="Le rôle autorisé à utiliser /sachatouille")
async def setrole(interaction: discord.Interaction, role: discord.Role):
    global ROLE_ID

    if not is_admin(interaction):
        await interaction.response.send_message(
            "❌ Seul un chef (admin) peut utiliser cette commande.",
            ephemeral=True
        )
        return

    ROLE_ID = role.id

    await interaction.response.send_message(
        f"✅ Le rôle autorisé est maintenant : {role.name}"
    )

bot.run(TOKEN)
