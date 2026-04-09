import os
import discord
from discord import app_commands
from discord.ext import commands

# 🔑 Token depuis Railway
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# 🎭 Rôle autorisé (modifiable avec /setrole)
ROLE_ID = None

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Bot prêt
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées")
    except Exception as e:
        print(e)

    print(f"🤖 Connecté en tant que {bot.user}")

# 🔒 Vérifie admin (chef)
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

# ✨ Commande principale
@bot.tree.command(name="sachatouille", description="Hommage à Sachatouille")
async def sachatouille(interaction: discord.Interaction):
    global ROLE_ID

    if ROLE_ID is None:
        await interaction.response.send_message(
            "⚠️ Aucun rôle configuré. Utilise /setrole",
            ephemeral=True
        )
        return

    user_roles = [role.id for role in interaction.user.roles]

    if ROLE_ID in user_roles:
        await interaction.response.send_message(
            "✨ Gloire éternelle à Sachatouille, maître incontesté de la chatouille cosmique ! ✨"
        )
    else:
        await interaction.response.send_message(
            "❌ Tu n'as pas le rôle nécessaire.",
            ephemeral=True
        )

# 👑 Commande admin pour définir le rôle
@bot.tree.command(name="setrole", description="Définir le rôle autorisé")
@app_commands.describe(role="Le rôle autorisé")
async def setrole(interaction: discord.Interaction, role: discord.Role):
    global ROLE_ID

    if not is_admin(interaction):
        await interaction.response.send_message(
            "❌ Seul un admin peut utiliser cette commande.",
            ephemeral=True
        )
        return

    ROLE_ID = role.id

    await interaction.response.send_message(
        f"✅ Rôle autorisé défini : {role.name}"
    )

# 🚀 Lancement
if TOKEN is None:
    print("❌ ERREUR : Le token est introuvable (DISCORD_BOT_TOKEN)")
else:
    bot.run(TOKEN)
