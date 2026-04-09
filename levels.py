import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
import time

XP_FILE = os.path.join(os.path.dirname(__file__), "xp_data.json")
LEVELS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "levels_config.json")

XP_MIN = 15
XP_MAX = 25
XP_COOLDOWN = 60


def xp_for_next_level(level: int) -> int:
    return (level + 1) * 100


def get_level_info(total_xp: int):
    level = 0
    xp = total_xp
    while True:
        needed = xp_for_next_level(level)
        if xp < needed:
            return level, xp, needed
        xp -= needed
        level += 1


def load_xp() -> dict:
    if os.path.exists(XP_FILE):
        with open(XP_FILE, "r") as f:
            return json.load(f)
    return {}


def save_xp(data: dict):
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    if os.path.exists(LEVELS_CONFIG_FILE):
        with open(LEVELS_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(LEVELS_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


class LevelsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns: dict[str, float] = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        key = f"{message.guild.id}:{message.author.id}"
        now = time.time()

        if now - self.cooldowns.get(key, 0) < XP_COOLDOWN:
            return
        self.cooldowns[key] = now

        xp_earned = random.randint(XP_MIN, XP_MAX)
        data = load_xp()
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        data.setdefault(guild_id, {})
        old_total = data[guild_id].get(user_id, 0)
        new_total = old_total + xp_earned
        data[guild_id][user_id] = new_total
        save_xp(data)

        old_level, _, _ = get_level_info(old_total)
        new_level, _, _ = get_level_info(new_total)

        if new_level > old_level:
            config = load_config()
            guild_config = config.get(guild_id, {})
            channel_id = guild_config.get("levelup_channel")
            channel = message.guild.get_channel(int(channel_id)) if channel_id else message.channel

            if channel:
                await channel.send(
                    f"🎉 Félicitations {message.author.mention} ! Tu passes au **niveau {new_level}** !"
                )

            rewards = guild_config.get("rewards", {})
            role_id = rewards.get(str(new_level))
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role:
                    try:
                        await message.author.add_roles(role, reason=f"Niveau {new_level} atteint")
                    except discord.Forbidden:
                        pass

    levels_group = app_commands.Group(name="niveau", description="Système de niveaux")

    @levels_group.command(name="voir", description="Voir ton niveau ou celui d'un membre")
    @app_commands.describe(membre="Le membre à vérifier (laisse vide pour toi)")
    async def voir(self, interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        data = load_xp()
        total_xp = data.get(str(interaction.guild_id), {}).get(str(target.id), 0)
        level, current_xp, needed_xp = get_level_info(total_xp)

        embed = discord.Embed(
            title=f"Niveau de {target.display_name}",
            color=discord.Color.gold(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Niveau", value=str(level), inline=True)
        embed.add_field(name="XP total", value=str(total_xp), inline=True)
        embed.add_field(
            name="Progression",
            value=f"{current_xp}/{needed_xp} XP",
            inline=True,
        )

        bar_filled = int((current_xp / needed_xp) * 10)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        embed.add_field(name="Barre", value=f"`{bar}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @levels_group.command(name="classement", description="Voir le classement XP du serveur")
    async def classement(self, interaction: discord.Interaction):
        data = load_xp()
        guild_data = data.get(str(interaction.guild_id), {})

        if not guild_data:
            await interaction.response.send_message("❌ Aucune donnée XP pour ce serveur.", ephemeral=True)
            return

        sorted_users = sorted(guild_data.items(), key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(
            title="🏆 Classement XP",
            color=discord.Color.gold(),
        )
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (user_id, total_xp) in enumerate(sorted_users):
            level, _, _ = get_level_info(total_xp)
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"Membre inconnu"
            medal = medals[i] if i < 3 else f"**#{i+1}**"
            lines.append(f"{medal} {name} — Niveau {level} ({total_xp} XP)")

        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed)

    @levels_group.command(name="recompenses", description="Voir les récompenses de rôles par niveau")
    async def recompenses(self, interaction: discord.Interaction):
        config = load_config()
        rewards = config.get(str(interaction.guild_id), {}).get("rewards", {})

        if not rewards:
            await interaction.response.send_message("❌ Aucune récompense configurée.", ephemeral=True)
            return

        embed = discord.Embed(title="🎁 Récompenses par niveau", color=discord.Color.blurple())
        for level, role_id in sorted(rewards.items(), key=lambda x: int(x[0])):
            role = interaction.guild.get_role(int(role_id))
            role_mention = role.mention if role else "Rôle supprimé"
            embed.add_field(name=f"Niveau {level}", value=role_mention, inline=True)
        await interaction.response.send_message(embed=embed)

    @levels_group.command(name="salon", description="Définir le salon des messages de level up")
    @app_commands.describe(salon="Le salon pour les annonces de niveau")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def salon(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        config.setdefault(str(interaction.guild_id), {})["levelup_channel"] = str(salon.id)
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de level up défini : {salon.mention}", ephemeral=True)

    @levels_group.command(name="ajouter-recompense", description="Ajouter une récompense de rôle à un niveau")
    @app_commands.describe(niveau="Le niveau requis", role="Le rôle à attribuer")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ajouter_recompense(self, interaction: discord.Interaction, niveau: int, role: discord.Role):
        config = load_config()
        config.setdefault(str(interaction.guild_id), {}).setdefault("rewards", {})[str(niveau)] = str(role.id)
        save_config(config)
        await interaction.response.send_message(
            f"✅ Rôle {role.mention} attribué au niveau **{niveau}**.", ephemeral=True
        )

    @levels_group.command(name="retirer-recompense", description="Retirer une récompense de rôle")
    @app_commands.describe(niveau="Le niveau dont retirer la récompense")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def retirer_recompense(self, interaction: discord.Interaction, niveau: int):
        config = load_config()
        rewards = config.get(str(interaction.guild_id), {}).get("rewards", {})
        if str(niveau) not in rewards:
            await interaction.response.send_message(f"❌ Aucune récompense au niveau {niveau}.", ephemeral=True)
            return
        del rewards[str(niveau)]
        save_config(config)
        await interaction.response.send_message(f"✅ Récompense du niveau {niveau} supprimée.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LevelsCog(bot))
