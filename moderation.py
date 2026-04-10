import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import asyncio
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from utils import data_path

WARNS_FILE = data_path("warns.json")

URL_PATTERN = re.compile(
    r"(https?://|www\.)\S+|discord\.gg/\S+",
    re.IGNORECASE
)

MAX_MESSAGES = 5
SPAM_WINDOW = 5
MAX_WARNS = 3
BAN_DURATION = 3600


def load_warns() -> dict:
    if os.path.exists(WARNS_FILE):
        with open(WARNS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_warns(data: dict):
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_warn_count(guild_id: str, user_id: str) -> int:
    warns = load_warns()
    return len(warns.get(guild_id, {}).get(user_id, []))


def add_warn(guild_id: str, user_id: str, reason: str, mod_id: str) -> int:
    warns = load_warns()
    warns.setdefault(guild_id, {}).setdefault(user_id, [])
    warns[guild_id][user_id].append({
        "reason": reason,
        "mod_id": mod_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    })
    save_warns(warns)
    return len(warns[guild_id][user_id])


def clear_warns(guild_id: str, user_id: str):
    warns = load_warns()
    if guild_id in warns and user_id in warns[guild_id]:
        warns[guild_id][user_id] = []
        save_warns(warns)


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam_tracker: dict[str, list[float]] = defaultdict(list)

    def is_staff(self, member: discord.Member) -> bool:
        return (
            member.guild_permissions.manage_messages
            or member.guild_permissions.administrator
        )

    async def apply_warn(self, member: discord.Member, reason: str, mod_id: str, channel: discord.TextChannel = None):
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        count = add_warn(guild_id, user_id, reason, mod_id)

        try:
            await member.send(
                f"⚠️ Tu as reçu un avertissement sur **{member.guild.name}**.\n"
                f"Raison : **{reason}**\n"
                f"Avertissements : **{count}/{MAX_WARNS}**"
            )
        except discord.Forbidden:
            pass

        if channel:
            await channel.send(
                f"⚠️ {member.mention} a reçu un avertissement. ({count}/{MAX_WARNS}) — {reason}",
                delete_after=8,
            )

        if count >= MAX_WARNS:
            clear_warns(guild_id, user_id)
            try:
                await member.send(
                    f"🔨 Tu as été banni temporairement de **{member.guild.name}** pour 1 heure "
                    f"(3 avertissements atteints)."
                )
            except discord.Forbidden:
                pass

            try:
                await member.ban(
                    reason=f"3 avertissements atteints (dernier: {reason})",
                    delete_message_days=0,
                )
            except discord.Forbidden:
                if channel:
                    await channel.send("❌ Je n'ai pas la permission de bannir ce membre.", delete_after=5)
                return

            if channel:
                await channel.send(
                    f"🔨 {member.mention} a été banni pour 1 heure (3 avertissements atteints).",
                    delete_after=10,
                )

            await asyncio.sleep(BAN_DURATION)
            try:
                await member.guild.unban(member, reason="Ban temporaire expiré")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if self.is_staff(message.author):
            return

        deleted = False

        if URL_PATTERN.search(message.content):
            try:
                await message.delete()
                deleted = True
            except discord.Forbidden:
                pass
            asyncio.create_task(
                self.apply_warn(message.author, "Envoi de lien interdit", str(self.bot.user.id), message.channel)
            )
            return

        key = f"{message.guild.id}:{message.author.id}"
        now = message.created_at.timestamp()
        self.spam_tracker[key] = [t for t in self.spam_tracker[key] if now - t < SPAM_WINDOW]
        self.spam_tracker[key].append(now)

        if len(self.spam_tracker[key]) > MAX_MESSAGES:
            self.spam_tracker[key] = []
            try:
                await message.delete()
                deleted = True
            except discord.Forbidden:
                pass

            async def purge_spam():
                def is_spam(m):
                    return m.author == message.author
                try:
                    await message.channel.purge(limit=MAX_MESSAGES + 2, check=is_spam)
                except Exception:
                    pass

            asyncio.create_task(purge_spam())
            asyncio.create_task(
                self.apply_warn(message.author, "Spam détecté", str(self.bot.user.id), message.channel)
            )

    mod_group = app_commands.Group(name="mod", description="Commandes de modération")

    @mod_group.command(name="warn", description="Avertir un membre")
    @app_commands.describe(membre="Le membre à avertir", raison="Raison de l'avertissement")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.bot:
            await interaction.response.send_message("❌ Impossible d'avertir un bot.", ephemeral=True)
            return
        if self.is_staff(membre):
            await interaction.response.send_message("❌ Impossible d'avertir un membre du staff.", ephemeral=True)
            return

        await interaction.response.send_message("⏳ Avertissement en cours...", ephemeral=True)
        asyncio.create_task(
            self.apply_warn(membre, raison, str(interaction.user.id), interaction.channel)
        )

    @mod_group.command(name="warns", description="Voir les avertissements d'un membre")
    @app_commands.describe(membre="Le membre à vérifier")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warns(self, interaction: discord.Interaction, membre: discord.Member):
        data = load_warns()
        user_warns = data.get(str(interaction.guild_id), {}).get(str(membre.id), [])

        embed = discord.Embed(
            title=f"Avertissements de {membre}",
            color=discord.Color.orange() if user_warns else discord.Color.green(),
        )
        if user_warns:
            for i, w in enumerate(user_warns, 1):
                ts = w.get("timestamp", "")[:10]
                embed.add_field(
                    name=f"Warn #{i} — {ts}",
                    value=w.get("reason", "Aucune raison"),
                    inline=False,
                )
        else:
            embed.description = "✅ Aucun avertissement."
        embed.set_footer(text=f"{len(user_warns)}/{MAX_WARNS} avertissements")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @mod_group.command(name="clearwarns", description="Effacer les avertissements d'un membre")
    @app_commands.describe(membre="Le membre dont on efface les warns")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clearwarns(self, interaction: discord.Interaction, membre: discord.Member):
        clear_warns(str(interaction.guild_id), str(membre.id))
        await interaction.response.send_message(
            f"✅ Avertissements de {membre.mention} réinitialisés.", ephemeral=True
        )

    @warn.error
    @warns.error
    @clearwarns.error
    async def mod_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Permission `Gérer les messages` requise.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
