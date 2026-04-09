import discord
from discord import app_commands
from discord.ext import commands

TOKEN = "TON_TOKEN_ICI"
ROLE_ID = 1487798711466725406  # Remplace par l'ID du rôle autorisé

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(e)
    print(f"Connecté en tant que {bot.user}")

@bot.tree.command(name="sachatouille", description="Hommage à Sachatouille")
async def sachatouille(interaction: discord.Interaction):
    role_ids = [role.id for role in interaction.user.roles]

    if 1487798711466725406 in role_ids:
        await interaction.response.send_message(
            "✨ Gloire éternelle à Sachatouille, maître incontesté de la chatouille cosmique ! ✨"
        )
    else:
        await interaction.response.send_message(
            "❌ Tu n'as pas le rôle nécessaire pour invoquer Sachatouille.",
            ephemeral=True
        )

bot.run(TOKEN)
