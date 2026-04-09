import discord
from discord import app_commands
from discord.ext import commands
import json
import os

INVITES_FILE = os.path.join(os.path.dirname(__file__), "invites_data.json")
INVITES_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "invites_config.json")


def load_data() -> dict:
    if os.path.exists(INVITES_FILE):
        with open(INVITES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(INVITES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_config() -> dict:
    if os.path.exists(INVITES_CONFIG_FILE):
        with open(INVITES_CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data: dict):
    with open(INVITES_CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_invite_count(guild_id: str, user_id: str) -> int:
    data = load_data()
    return data.get(guild_id, {}).get(user_id, 0)


def add_invite(guild_id: str, user_id: str, amount: int = 1):
    data = load_data()
    data.setdefault(guild_id, {})
    data[guild_id][user_id] = data[guild_id].get(user_id, 0) + amount
    if data[guild_id][user_id] < 0:
        data[guild_id][user_id] = 0
    save_data(data)


class InvitesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_cache: dict[int, dict[str, discord.Invite]] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = {inv.code: inv for inv in invites}
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild:
            self.invite_cache.setdefault(invite.guild.id, {})
            self.invite_cache[invite.guild.id][invite.code] = invite

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild and invite.guild.id in self.invite_cache:
            self.invite_cache[invite.guild.id].pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        inviter = None

        try:
            new_invites = await guild.invites()
            new_invite_map = {inv.code: inv for inv in new_invites}
            cached = self.invite_cache.get(guild.id, {})

            for code, new_inv in new_invite_map.items():
                old_inv = cached.get(code)
                if old_inv and new_inv.uses > old_inv.uses:
                    inviter = new_inv.inviter
                    if inviter:
                        add_invite(str(guild.id), str(inviter.id))
                    break

            self.invite_cache[guild.id] = new_invite_map
        except discord.Forbidden:
            pass

        config = load_config()
        guild_config = config.get(str(guild.id))
        if not guild_config:
            return

        channel = guild.get_channel(int(guild_config["channel_id"]))
        if not channel:
            return

        if inviter:
            msg = (
                f"Salut {member.mention} tu as été invité par **{inviter.display_name}** "
                f"merci d'être venu ! 🎉"
            )
        else:
            msg = f"Salut {member.mention} merci d'être venu ! 🎉"

        await channel.send(msg)

    invite_group = app_commands.Group(name="invites", description="Système d'invitations")

    @invite_group.command(name="voir", description="Voir le nombre d'invitations d'un membre")
    @app_commands.describe(membre="Le membre à vérifier (laisse vide pour toi)")
    async def voir(self, interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        count = get_invite_count(str(interaction.guild_id), str(target.id))

        embed = discord.Embed(
            description=f"🔗 **{target.display_name}** a **{count}** invitation(s).",
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @invite_group.command(name="reset", description="Réinitialiser les invitations")
    @app_commands.describe(membre="Le membre à réinitialiser (laisse vide pour tout le monde)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reset(self, interaction: discord.Interaction, membre: discord.Member = None):
        data = load_data()
        guild_id = str(interaction.guild_id)

        if membre:
            if guild_id in data and str(membre.id) in data[guild_id]:
                data[guild_id][str(membre.id)] = 0
                save_data(data)
            await interaction.response.send_message(
                f"✅ Invitations de {membre.mention} réinitialisées.", ephemeral=True
            )
        else:
            data[guild_id] = {}
            save_data(data)
            await interaction.response.send_message(
                "✅ Invitations de tout le monde réinitialisées.", ephemeral=True
            )

    @invite_group.command(name="salon", description="Choisir le salon pour les messages d'invitation")
    @app_commands.describe(salon="Le salon où envoyer les messages")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def salon(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        config[str(interaction.guild_id)] = {"channel_id": str(salon.id)}
        save_config(config)
        await interaction.response.send_message(
            f"✅ Les messages d'invitation seront envoyés dans {salon.mention} !", ephemeral=True
        )

    @reset.error
    @salon.error
    async def invites_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Permission `Gérer le serveur` requise.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(InvitesCog(bot))
