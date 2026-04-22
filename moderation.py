import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import asyncio
from datetime import datetime, timezone
from collections import defaultdict
from utils import data_path

WARNS_FILE = data_path("warns.json")
ALLOWED_LINKS_FILE = data_path("allowed_links.json")

URL_PATTERN = re.compile(
    r"(https?://|www\.)\S+|discord\.gg/\S+",
    re.IGNORECASE
)

MAX_MESSAGES = 5
SPAM_WINDOW = 5
MAX_WARNS = 3
BAN_DURATION = 3600


# ---------- WARNS ---------- #

def load_warns() -> dict:
    if os.path.exists(WARNS_FILE):
        with open(WARNS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_warns(data: dict):
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)


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


# ---------- ALLOWED LINKS ---------- #

def load_allowed_links() -> dict:
    if os.path.exists(ALLOWED_LINKS_FILE):
        with open(ALLOWED_LINKS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_allowed_links(data: dict):
    with open(ALLOWED_LINKS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_allowed_links(guild_id: str) -> list:
    data = load_allowed_links()
    return data.get(guild_id, [])


def add_allowed_link(guild_id: str, link: str):
    data = load_allowed_links()
    data.setdefault(guild_id, [])
    if link not in data[guild_id]:
        data[guild_id].append(link)
    save_allowed_links(data)


def remove_allowed_link(guild_id: str, link: str):
    data = load_allowed_links()
    if guild_id in data and link in data[guild_id]:
        data[guild_id].remove(link)
        save_allowed_links(data)


# ---------- COG ---------- #

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam_tracker = defaultdict(list)

    def is_staff(self, member: discord.Member) -> bool:
        return (
            member.guild_permissions.manage_messages
            or member.guild_permissions.administrator
        )

    async def apply_warn(self, member, reason, mod_id, channel=None):
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        count = add_warn(guild_id, user_id, reason, mod_id)

        try:
            await member.send(
                f"⚠️ Avertissement sur **{member.guild.name}**\n"
                f"Raison : **{reason}**\n"
                f"{count}/{MAX_WARNS}"
            )
        except:
            pass

        if channel:
            await channel.send(
                f"⚠️ {member.mention} averti ({count}/{MAX_WARNS}) — {reason}",
                delete_after=8
            )

        if count >= MAX_WARNS:
            clear_warns(guild_id, user_id)

            try:
                await member.ban(reason="3 warns", delete_message_days=0)
            except:
                return

            if channel:
                await channel.send(
                    f"🔨 {member.mention} banni 1h (3 warns)",
                    delete_after=10
                )

            await asyncio.sleep(BAN_DURATION)

            try:
                await member.guild.unban(member)
            except:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        if self.is_staff(message.author):
            return

        # -------- ANTI LINK -------- #
        if URL_PATTERN.search(message.content):
            allowed = get_allowed_links(str(message.guild.id))

            if any(site in message.content.lower() for site in allowed):
                return

            try:
                await message.delete()
            except:
                pass

            asyncio.create_task(
                self.apply_warn(
                    message.author,
                    "Lien interdit",
                    str(self.bot.user.id),
                    message.channel
                )
            )
            return

        # -------- ANTI SPAM -------- #
        key = f"{message.guild.id}:{message.author.id}"
        now = message.created_at.timestamp()

        self.spam_tracker[key] = [
            t for t in self.spam_tracker[key]
            if now - t < SPAM_WINDOW
        ]
        self.spam_tracker[key].append(now)

        if len(self.spam_tracker[key]) > MAX_MESSAGES:
            self.spam_tracker[key] = []

            try:
                await message.delete()
            except:
                pass

            asyncio.create_task(
                self.apply_warn(
                    message.author,
                    "Spam",
                    str(self.bot.user.id),
                    message.channel
                )
            )

# ---------- COMMANDES ---------- #

class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spam_tracker = defaultdict(list)

    def is_staff(self, member: discord.Member) -> bool:
        return (
            member.guild_permissions.manage_messages
            or member.guild_permissions.administrator
        )

    # -------- GROUP -------- #
    mod_group = app_commands.Group(name="mod", description="Modération")

    # -------- LINKS -------- #

    @mod_group.command(name="allowlink")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def allowlink(self, interaction, site: str):
        site = site.lower().replace("https://", "").replace("http://", "").strip("/")
        add_allowed_link(str(interaction.guild_id), site)

        await interaction.response.send_message(
            f"✅ Autorisé : `{site}`",
            ephemeral=True
        )

    @mod_group.command(name="removelink")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def removelink(self, interaction, site: str):
        site = site.lower().replace("https://", "").replace("http://", "").strip("/")
        remove_allowed_link(str(interaction.guild_id), site)

        await interaction.response.send_message(
            f"🗑️ Retiré : `{site}`",
            ephemeral=True
        )

    @mod_group.command(name="listlinks")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def listlinks(self, interaction):
        links = get_allowed_links(str(interaction.guild_id))

        if not links:
            await interaction.response.send_message("❌ Aucun site.", ephemeral=True)
            return

        await interaction.response.send_message(
            "🔗 Sites autorisés :\n" + "\n".join(f"- {l}" for l in links),
            ephemeral=True
        )

    # -------- WARNS -------- #

    @mod_group.command(name="warn")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warn(self, interaction, member: discord.Member, reason: str):
        await interaction.response.defer(ephemeral=True)

        await self.apply_warn(
            member,
            reason,
            str(interaction.user.id),
            interaction.channel
        )

        await interaction.followup.send(
            f"⚠️ {member.mention} a été averti.",
            ephemeral=True
        )

    @mod_group.command(name="warns")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def warns_cmd(self, interaction, member: discord.Member):
        warns = load_warns()
        guild_id = str(interaction.guild_id)
        user_id = str(member.id)

        user_warns = warns.get(guild_id, {}).get(user_id, [])

        if not user_warns:
            await interaction.response.send_message(
                "✅ Aucun avertissement.",
                ephemeral=True
            )
            return

        msg = "\n".join(
            f"{i+1}. {w['reason']}" for i, w in enumerate(user_warns)
        )

        await interaction.response.send_message(
            f"⚠️ Warns de {member.mention} :\n{msg}",
            ephemeral=True
        )

    @mod_group.command(name="clearwarns")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clearwarns_cmd(self, interaction, member: discord.Member):
        clear_warns(str(interaction.guild_id), str(member.id))

        await interaction.response.send_message(
            f"🧹 Warns de {member.mention} supprimés.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
