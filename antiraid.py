import discord
from discord.ext import commands
from datetime import datetime, timedelta

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # STOCKAGE
        self.deletions = {}
        self.creations = {}

        # CONFIG
        self.DELETE_LIMIT = 3   # nb suppressions
        self.CREATE_LIMIT = 3   # nb créations
        self.TIME_WINDOW = 10   # secondes

    # ================= DELETE DETECTION ================= #

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user

            if user.bot:
                return

            now = datetime.utcnow()

            if user.id not in self.deletions:
                self.deletions[user.id] = []

            self.deletions[user.id].append(now)

            # nettoyer ancien
            self.deletions[user.id] = [
                t for t in self.deletions[user.id]
                if now - t < timedelta(seconds=self.TIME_WINDOW)
            ]

            if len(self.deletions[user.id]) >= self.DELETE_LIMIT:
                await self.handle_raid(guild, user, "SUPPRESSION DE SALONS")

                # RESTORE SALON
                try:
                    if isinstance(channel, discord.TextChannel):
                        await guild.create_text_channel(name=channel.name)
                    elif isinstance(channel, discord.VoiceChannel):
                        await guild.create_voice_channel(name=channel.name)
                except:
                    pass

    # ================= CREATE DETECTION ================= #

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            user = entry.user

            if user.bot:
                return

            now = datetime.utcnow()

            if user.id not in self.creations:
                self.creations[user.id] = []

            self.creations[user.id].append(now)

            self.creations[user.id] = [
                t for t in self.creations[user.id]
                if now - t < timedelta(seconds=self.TIME_WINDOW)
            ]

            if len(self.creations[user.id]) >= self.CREATE_LIMIT:
                await self.handle_raid(guild, user, "SPAM DE SALONS")

                # DELETE salon créé
                try:
                    await channel.delete()
                except:
                    pass

    # ================= ACTION RAID ================= #

    async def handle_raid(self, guild, user, reason):
        try:
            await guild.ban(user, reason=f"Raid détecté: {reason}")
        except:
            try:
                await guild.kick(user, reason=f"Raid détecté: {reason}")
            except:
                pass

        # sécuriser le bot (retirer perms dangereuses temporairement)
        bot_member = guild.get_member(self.bot.user.id)

        if bot_member:
            try:
                await bot_member.edit(roles=[])
            except:
                pass

        print(f"[ANTI-RAID] {user} puni pour {reason}")

# ================= SETUP ================= #

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
