import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import random
import asyncio
from datetime import datetime, timedelta, timezone
from utils import data_path

GIVEAWAYS_FILE = data_path("giveaways.json")


def load_giveaways() -> dict:
    if os.path.exists(GIVEAWAYS_FILE):
        with open(GIVEAWAYS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_giveaways(data: dict):
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def parse_duration(duration_str: str) -> int:
    """Convert duration string like 10s, 5m, 2h, 1d to seconds."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration_str[-1].lower()
    if unit not in units:
        raise ValueError(f"Unité invalide: {unit}. Utilisez s, m, h ou d.")
    try:
        value = int(duration_str[:-1])
    except ValueError:
        raise ValueError("Format invalide. Exemple: 10m, 2h, 1d")
    return value * units[unit]


class ParticipateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎉 Participer",
        style=discord.ButtonStyle.green,
        custom_id="giveaway_participate",
    )
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaways = load_giveaways()
        key = str(interaction.message.id)

        if key not in giveaways:
            await interaction.response.send_message("❌ Ce giveaway est introuvable.", ephemeral=True)
            return

        gw = giveaways[key]

        if gw.get("ended"):
            await interaction.response.send_message("❌ Ce giveaway est terminé.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        participants = gw.get("participants", [])

        if user_id in participants:
            participants.remove(user_id)
            giveaways[key]["participants"] = participants
            save_giveaways(giveaways)
            await interaction.response.send_message(
                "✅ Tu t'es **retiré** du giveaway.", ephemeral=True
            )
        else:
            participants.append(user_id)
            giveaways[key]["participants"] = participants
            save_giveaways(giveaways)
            await interaction.response.send_message(
                "🎉 Tu es maintenant **inscrit** au giveaway !", ephemeral=True
            )

        await update_giveaway_embed(interaction.client, giveaways[key], interaction.message)


async def update_giveaway_embed(bot: commands.Bot, gw: dict, message: discord.Message = None):
    channel = bot.get_channel(int(gw["channel_id"]))
    if not channel:
        return
    if not message:
        try:
            message = await channel.fetch_message(int(gw["message_id"]))
        except Exception:
            return

    end_ts = int(gw["end_time"])
    participant_count = len(gw.get("participants", []))

    embed = discord.Embed(
        title=f"🎁 GIVEAWAY — {gw['prize']}",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Gagnant(s)", value=str(gw["winners"]), inline=True)
    embed.add_field(name="Participants", value=str(participant_count), inline=True)
    embed.add_field(name="Organisé par", value=f"<@{gw['host_id']}>", inline=True)

    if gw.get("ended"):
        winners = gw.get("winner_ids", [])
        if winners:
            winner_mentions = ", ".join(f"<@{w}>" for w in winners)
            embed.description = f"🏆 **Gagnant(s) :** {winner_mentions}"
        else:
            embed.description = "😔 Personne n'a participé."
        embed.set_footer(text="Giveaway terminé")
        embed.color = discord.Color.red()
    else:
        embed.description = "Clique sur le bouton pour participer !"
        embed.set_footer(text=f"Se termine le")
        embed.timestamp = datetime.fromtimestamp(end_ts, tz=timezone.utc)

    try:
        await message.edit(embed=embed)
    except Exception:
        pass


async def end_giveaway(bot: commands.Bot, key: str, giveaways: dict):
    gw = giveaways[key]
    if gw.get("ended"):
        return

    participants = gw.get("participants", [])
    num_winners = min(gw["winners"], len(participants))
    winner_ids = random.sample(participants, num_winners) if num_winners > 0 else []

    giveaways[key]["ended"] = True
    giveaways[key]["winner_ids"] = winner_ids
    save_giveaways(giveaways)

    channel = bot.get_channel(int(gw["channel_id"]))
    if not channel:
        return

    try:
        message = await channel.fetch_message(int(gw["message_id"]))
        await update_giveaway_embed(bot, giveaways[key], message)
    except Exception:
        pass

    if winner_ids:
        winner_mentions = ", ".join(f"<@{w}>" for w in winner_ids)
        await channel.send(
            f"🎉 Félicitations {winner_mentions} ! Vous avez gagné **{gw['prize']}** !"
        )
    else:
        await channel.send(f"😔 Personne n'a participé au giveaway **{gw['prize']}**.")


class GiveawayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=10)
    async def check_giveaways(self):
        giveaways = load_giveaways()
        now = datetime.now(tz=timezone.utc).timestamp()
        changed = False
        for key, gw in giveaways.items():
            if not gw.get("ended") and now >= gw["end_time"]:
                await end_giveaway(self.bot, key, giveaways)
                changed = True
                giveaways = load_giveaways()
        if changed:
            save_giveaways(giveaways)

    @check_giveaways.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    giveaway_group = app_commands.Group(name="giveaway", description="Système de giveaway")

    @giveaway_group.command(name="créer", description="Créer un giveaway")
    @app_commands.describe(
        prix="Le prix du giveaway",
        durée="Durée du giveaway (ex: 10m, 2h, 1d)",
        gagnants="Nombre de gagnants",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def creer(
        self,
        interaction: discord.Interaction,
        prix: str,
        durée: str,
        gagnants: int = 1,
    ):
        try:
            seconds = parse_duration(durée)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        if gagnants < 1:
            await interaction.response.send_message("❌ Il faut au moins 1 gagnant.", ephemeral=True)
            return

        end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)

        embed = discord.Embed(
            title=f"🎁 GIVEAWAY — {prix}",
            description="Clique sur le bouton pour participer !",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Gagnant(s)", value=str(gagnants), inline=True)
        embed.add_field(name="Participants", value="0", inline=True)
        embed.add_field(name="Organisé par", value=interaction.user.mention, inline=True)
        embed.set_footer(text="Se termine le")
        embed.timestamp = end_time

        await interaction.response.send_message("✅ Giveaway créé !", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=ParticipateButton())

        giveaways = load_giveaways()
        giveaways[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(interaction.channel_id),
            "guild_id": str(interaction.guild_id),
            "prize": prix,
            "winners": gagnants,
            "host_id": str(interaction.user.id),
            "end_time": end_time.timestamp(),
            "participants": [],
            "ended": False,
        }
        save_giveaways(giveaways)

    @giveaway_group.command(name="terminer", description="Terminer un giveaway immédiatement")
    @app_commands.describe(message_id="L'ID du message du giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def terminer(self, interaction: discord.Interaction, message_id: str):
        giveaways = load_giveaways()
        if message_id not in giveaways:
            await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)
            return
        if giveaways[message_id].get("ended"):
            await interaction.response.send_message("❌ Ce giveaway est déjà terminé.", ephemeral=True)
            return

        await interaction.response.send_message("✅ Giveaway terminé !", ephemeral=True)
        await end_giveaway(self.bot, message_id, giveaways)

    @giveaway_group.command(name="relancer", description="Choisir un nouveau gagnant pour un giveaway terminé")
    @app_commands.describe(message_id="L'ID du message du giveaway")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def relancer(self, interaction: discord.Interaction, message_id: str):
        giveaways = load_giveaways()
        if message_id not in giveaways:
            await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)
            return

        gw = giveaways[message_id]
        participants = gw.get("participants", [])
        if not participants:
            await interaction.response.send_message("❌ Aucun participant.", ephemeral=True)
            return

        num_winners = min(gw["winners"], len(participants))
        new_winners = random.sample(participants, num_winners)
        giveaways[message_id]["winner_ids"] = new_winners
        save_giveaways(giveaways)

        winner_mentions = ", ".join(f"<@{w}>" for w in new_winners)
        await interaction.response.send_message(
            f"🎉 Nouveau(x) gagnant(s) : {winner_mentions} pour **{gw['prize']}** !"
        )

    @giveaway_group.command(name="participants", description="Voir les participants d'un giveaway")
    @app_commands.describe(message_id="L'ID du message du giveaway")
    async def participants(self, interaction: discord.Interaction, message_id: str):
        giveaways = load_giveaways()
        if message_id not in giveaways:
            await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)
            return

        gw = giveaways[message_id]
        p_list = gw.get("participants", [])

        embed = discord.Embed(
            title=f"Participants — {gw['prize']}",
            color=discord.Color.blurple(),
        )
        if p_list:
            embed.description = "\n".join(f"<@{uid}>" for uid in p_list)
        else:
            embed.description = "Aucun participant pour l'instant."
        embed.set_footer(text=f"{len(p_list)} participant(s)")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @giveaway_group.command(
        name="retirer",
        description="Retirer un membre d'un giveaway (créateur du giveaway uniquement)",
    )
    @app_commands.describe(
        message_id="L'ID du message du giveaway",
        membre="Le membre à retirer",
    )
    async def retirer(
        self,
        interaction: discord.Interaction,
        message_id: str,
        membre: discord.Member,
    ):
        giveaways = load_giveaways()
        if message_id not in giveaways:
            await interaction.response.send_message("❌ Giveaway introuvable.", ephemeral=True)
            return

        gw = giveaways[message_id]

        if str(interaction.user.id) != gw.get("host_id"):
            await interaction.response.send_message(
                "❌ Seul la personne ayant créé ce giveaway peut retirer des membres.", ephemeral=True
            )
            return

        if gw.get("ended"):
            await interaction.response.send_message("❌ Ce giveaway est déjà terminé.", ephemeral=True)
            return

        participants = gw.get("participants", [])
        user_id = str(membre.id)

        if user_id not in participants:
            await interaction.response.send_message(
                f"❌ {membre.mention} ne participe pas à ce giveaway.", ephemeral=True
            )
            return

        participants.remove(user_id)
        giveaways[message_id]["participants"] = participants
        save_giveaways(giveaways)

        try:
            channel = self.bot.get_channel(int(gw["channel_id"]))
            msg = await channel.fetch_message(int(message_id))
            await update_giveaway_embed(self.bot, giveaways[message_id], msg)
        except Exception:
            pass

        await interaction.response.send_message(
            f"✅ {membre.mention} a été retiré du giveaway **{gw['prize']}**.", ephemeral=True
        )

    @creer.error
    @terminer.error
    @relancer.error
    async def giveaway_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ Tu n'as pas la permission `Gérer le serveur`.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
    bot.add_view(ParticipateButton())
