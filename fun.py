import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from utils import data_path

FUN_CONFIG_FILE = data_path("fun_config.json")


def load_config() -> dict:
    if os.path.exists(FUN_CONFIG_FILE):
        with open(FUN_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(FUN_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


SACHATOUILLE_MESSAGES = [
    "👑 **Gloire à Sachatouille**, le plus grand, le plus puissant, l'inégalable !",
    "✨ Que son nom soit gravé dans les étoiles : **SACHATOUILLE** !",
    "🌟 Le légendaire **Sachatouille** règne en maître absolu sur ce serveur !",
    "🏆 **Sachatouille** — une légende vivante, un mythe incarné, un dieu parmi les mortels !",
    "🔥 Trembles, mortels ! **Sachatouille** a parlé !",
]

import random


class FunCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.route_state: dict[str, dict] = {}

    # ─── Sachatouille ───────────────────────────────────────────────

    @app_commands.command(name="sachatouille", description="Gloire à Sachatouille !")
    async def sachatouille(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild_id)
        role_id = config.get(guild_id, {}).get("sachatouille_role")

        if role_id:
            role = interaction.guild.get_role(int(role_id))
            if role and role not in interaction.user.roles:
                await interaction.response.send_message(
                    f"❌ Tu dois avoir le rôle {role.mention} pour utiliser cette commande.",
                    ephemeral=True,
                )
                return

        message = random.choice(SACHATOUILLE_MESSAGES)
        embed = discord.Embed(
            title="⚜️ GLOIRE À SACHATOUILLE ⚜️",
            description=message,
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Invoqué par {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    sachatouille_group = app_commands.Group(
        name="sachatouille-config", description="Configuration de la commande Sachatouille"
    )

    @sachatouille_group.command(name="role", description="Définir le rôle requis pour /sachatouille")
    @app_commands.describe(role="Le rôle autorisé à utiliser /sachatouille")
    @app_commands.checks.has_permissions(administrator=True)
    async def sachatouille_role(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        config.setdefault(str(interaction.guild_id), {})["sachatouille_role"] = str(role.id)
        save_config(config)
        await interaction.response.send_message(
            f"✅ Seuls les membres avec {role.mention} peuvent utiliser `/sachatouille`.",
            ephemeral=True,
        )

    @sachatouille_group.command(name="supprimer-role", description="Retirer la restriction de rôle sur /sachatouille")
    @app_commands.checks.has_permissions(administrator=True)
    async def sachatouille_remove_role(self, interaction: discord.Interaction):
        config = load_config()
        config.get(str(interaction.guild_id), {}).pop("sachatouille_role", None)
        save_config(config)
        await interaction.response.send_message(
            "✅ Tout le monde peut maintenant utiliser `/sachatouille`.", ephemeral=True
        )

    # ─── Route de l'infini ──────────────────────────────────────────

    route_group = app_commands.Group(
        name="route", description="Route de l'infini — comptez dans l'ordre !"
    )

    @route_group.command(name="salon", description="Définir le salon de la route de l'infini")
    @app_commands.describe(salon="Le salon dédié au comptage")
    @app_commands.checks.has_permissions(administrator=True)
    async def route_salon(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        config.setdefault(str(interaction.guild_id), {})["route_channel"] = str(salon.id)
        save_config(config)
        await interaction.response.send_message(
            f"✅ Salon de la route de l'infini : {salon.mention}", ephemeral=True
        )

    @route_group.command(name="role-erreur", description="Rôle donné à celui qui fait une erreur")
    @app_commands.describe(role="Le rôle de la honte")
    @app_commands.checks.has_permissions(administrator=True)
    async def route_role(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        config.setdefault(str(interaction.guild_id), {})["route_fail_role"] = str(role.id)
        save_config(config)
        await interaction.response.send_message(
            f"✅ Le rôle {role.mention} sera donné à celui qui fait une erreur.", ephemeral=True
        )

    @route_group.command(name="score", description="Voir le meilleur score atteint")
    async def route_score(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild_id)
        best = config.get(guild_id, {}).get("route_best", 0)
        state = self.route_state.get(guild_id, {})
        current = state.get("count", 0)
        await interaction.response.send_message(
            f"🛣️ **Route de l'infini**\n"
            f"Compteur actuel : **{current}**\n"
            f"🏆 Meilleur score : **{best}**"
        )

    # ─── Auto-react ─────────────────────────────────────────────────

    import discord
from discord import app_commands
from discord.ext import commands
import time

# cooldown en mémoire
cooldowns = {}

class AutoReact(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    autoreact_group = app_commands.Group(
        name="autoreact",
        description="Réactions automatiques sur les messages d'un salon"
    )

    @autoreact_group.command(name="ajouter", description="Ajouter auto-react ou message")
    @app_commands.describe(
        salon="Le salon concerné",
        emojis="Les emojis séparés par des espaces",
        message="Message automatique à envoyer"
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_ajouter(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        emojis: str = None,
        message: str = None
    ):
        if not emojis and not message:
            await interaction.response.send_message(
                "❌ Tu dois fournir des emojis ou un message.",
                ephemeral=True
            )
            return

        emoji_list = emojis.strip().split() if emojis else []

        config = load_config()
        guild_data = config.setdefault(str(interaction.guild_id), {})
        autoreacts = guild_data.setdefault("autoreact", {})

        autoreacts[str(salon.id)] = {
            "emojis": emoji_list,
            "message": message,
            "cooldown": 5  # secondes (modifiable)
        }

        save_config(config)

        await interaction.response.send_message(
            f"✅ Config ajoutée sur {salon.mention}",
            ephemeral=True
        )

    @autoreact_group.command(name="retirer", description="Retirer auto-react")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def autoreact_retirer(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        autoreacts = config.get(str(interaction.guild_id), {}).get("autoreact", {})

        if str(salon.id) not in autoreacts:
            await interaction.response.send_message(
                f"❌ Aucun auto-react sur {salon.mention}.",
                ephemeral=True
            )
            return

        del autoreacts[str(salon.id)]
        save_config(config)

        await interaction.response.send_message(
            f"✅ Auto-react retiré de {salon.mention}",
            ephemeral=True
        )

    @autoreact_group.command(name="liste", description="Liste des auto-react")
    async def autoreact_liste(self, interaction: discord.Interaction):
        config = load_config()
        autoreacts = config.get(str(interaction.guild_id), {}).get("autoreact", {})

        if not autoreacts:
            await interaction.response.send_message(
                "❌ Aucun auto-react configuré.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="⚡ Auto-reacts configurés",
            color=discord.Color.blurple()
        )

        for channel_id, data in autoreacts.items():
            channel = interaction.guild.get_channel(int(channel_id))
            name = channel.mention if channel else f"Salon supprimé ({channel_id})"

            emojis = " ".join(data.get("emojis", [])) or "Aucun"
            message = data.get("message") or "Aucun"

            embed.add_field(
                name=name,
                value=f"**Emojis :** {emojis}\n**Message :** {message}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)
        # Auto-react
        autoreacts = guild_config.get("autoreact", {})
        if str(message.channel.id) in autoreacts:
            for emoji in autoreacts[str(message.channel.id)]:
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    pass

        route_channel_id = guild_config.get("route_channel")

        if not route_channel_id:
            return
        if str(message.channel.id) != route_channel_id:
            return

        state = self.route_state.setdefault(guild_id, {"count": 0, "last_user": None})

        content = message.content.strip()

        # Only accept plain integers
        if not content.isdigit():
            await message.delete()
            return

        number = int(content)
        expected = state["count"] + 1

        # Same person twice in a row
        if str(message.author.id) == state.get("last_user"):
            await self._fail(message, guild_config, state, guild_id, config,
                             reason="Tu ne peux pas compter deux fois de suite !")
            return

        # Wrong number
        if number != expected:
            await self._fail(message, guild_config, state, guild_id, config,
                             reason=f"Le prochain nombre était **{expected}**, pas {number} !")
            return

        # Correct
        state["count"] = number
        state["last_user"] = str(message.author.id)

        # Update best score
        if number > guild_config.get("route_best", 0):
            config.setdefault(guild_id, {})["route_best"] = number
            save_config(config)

        await message.add_reaction("✅")

    async def _fail(
        self,
        message: discord.Message,
        guild_config: dict,
        state: dict,
        guild_id: str,
        config: dict,
        reason: str,
    ):
        best = guild_config.get("route_best", 0)
        reached = state["count"]
        state["count"] = 0
        state["last_user"] = None

        await message.add_reaction("❌")
        await message.channel.send(
            f"💥 {message.author.mention} a cassé la route de l'infini ! {reason}\n"
            f"Score atteint : **{reached}** | Meilleur score : **{best}**\n"
            f"On repart de **1** !"
        )

        fail_role_id = guild_config.get("route_fail_role")
        if fail_role_id:
            role = message.guild.get_role(int(fail_role_id))
            if role:
                try:
                    await message.author.add_roles(role, reason="Erreur route de l'infini")
                except discord.Forbidden:
                    pass


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
