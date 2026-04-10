import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from utils import data_path

LOGS_CONFIG_FILE = data_path("logs_config.json")


def load_config() -> dict:
    if os.path.exists(LOGS_CONFIG_FILE):
        with open(LOGS_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(LOGS_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def get_log_channel(guild: discord.Guild) -> discord.TextChannel | None:
    config = load_config()
    channel_id = config.get(str(guild.id), {}).get("channel_id")
    if not channel_id:
        return None
    return guild.get_channel(int(channel_id))


class LogsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        channel = await get_log_channel(message.guild)
        if not channel:
            return

        embed = discord.Embed(
            title="🗑️ Message supprimé",
            color=discord.Color.red(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Auteur", value=message.author.mention, inline=True)
        embed.add_field(name="Salon", value=message.channel.mention, inline=True)
        embed.add_field(
            name="Contenu",
            value=message.content[:1024] if message.content else "*Aucun texte*",
            inline=False,
        )
        embed.set_footer(text=f"ID utilisateur: {message.author.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot:
            return
        if before.content == after.content:
            return
        channel = await get_log_channel(before.guild)
        if not channel:
            return

        embed = discord.Embed(
            title="✏️ Message modifié",
            color=discord.Color.orange(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Auteur", value=before.author.mention, inline=True)
        embed.add_field(name="Salon", value=before.channel.mention, inline=True)
        embed.add_field(name="Avant", value=before.content[:512] or "*Vide*", inline=False)
        embed.add_field(name="Après", value=after.content[:512] or "*Vide*", inline=False)
        embed.set_footer(text=f"ID utilisateur: {before.author.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        channel = await get_log_channel(guild)
        if not channel:
            return

        embed = discord.Embed(
            title="🔨 Membre banni",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Membre", value=f"{user} ({user.mention})", inline=True)

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                embed.add_field(name="Banni par", value=entry.user.mention, inline=True)
                if entry.reason:
                    embed.add_field(name="Raison", value=entry.reason, inline=False)
        except discord.Forbidden:
            pass

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"ID: {user.id}")
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        channel = await get_log_channel(guild)
        if not channel:
            return

        embed = discord.Embed(
            title="✅ Membre débanni",
            color=discord.Color.green(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Membre", value=f"{user} ({user.id})", inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await get_log_channel(member.guild)
        if not channel:
            return

        try:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if entry.target.id == member.id:
                    embed = discord.Embed(
                        title="👢 Membre expulsé",
                        color=discord.Color.orange(),
                        timestamp=datetime.now(tz=timezone.utc),
                    )
                    embed.add_field(name="Membre", value=f"{member} ({member.mention})", inline=True)
                    embed.add_field(name="Expulsé par", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Raison", value=entry.reason, inline=False)
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text=f"ID: {member.id}")
                    await channel.send(embed=embed)
                    return
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            title="👋 Membre parti",
            color=discord.Color.greyple(),
            timestamp=datetime.now(tz=timezone.utc),
        )
        embed.add_field(name="Membre", value=f"{member} ({member.id})", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        channel = await get_log_channel(before.guild)
        if not channel:
            return

        before_roles = set(before.roles)
        after_roles = set(after.roles)
        added = after_roles - before_roles
        removed = before_roles - after_roles

        if added or removed:
            embed = discord.Embed(
                title="🎭 Rôles modifiés",
                color=discord.Color.blurple(),
                timestamp=datetime.now(tz=timezone.utc),
            )
            embed.add_field(name="Membre", value=after.mention, inline=True)
            if added:
                embed.add_field(name="Ajoutés", value=", ".join(r.mention for r in added), inline=False)
            if removed:
                embed.add_field(name="Retirés", value=", ".join(r.mention for r in removed), inline=False)
            embed.set_footer(text=f"ID: {after.id}")
            await channel.send(embed=embed)

        elif before.nick != after.nick:
            embed = discord.Embed(
                title="📝 Pseudo modifié",
                color=discord.Color.blurple(),
                timestamp=datetime.now(tz=timezone.utc),
            )
            embed.add_field(name="Membre", value=after.mention, inline=True)
            embed.add_field(name="Avant", value=before.nick or before.name, inline=True)
            embed.add_field(name="Après", value=after.nick or after.name, inline=True)
            embed.set_footer(text=f"ID: {after.id}")
            await channel.send(embed=embed)

    log_group = app_commands.Group(name="logs", description="Système de logs")

    @log_group.command(name="salon", description="Définir le salon des logs")
    @app_commands.describe(salon="Le salon où envoyer les logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def salon(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        config[str(interaction.guild_id)] = {"channel_id": str(salon.id)}
        save_config(config)
        await interaction.response.send_message(
            f"✅ Les logs seront envoyés dans {salon.mention} !", ephemeral=True
        )

    @salon.error
    async def logs_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Permission `Administrateur` requise.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(LogsCog(bot))
