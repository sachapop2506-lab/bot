import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import random
from datetime import datetime, timedelta, timezone
from utils import data_path

GIVEAWAYS_FILE = data_path("giveaways.json")


# ---------------- FILE ---------------- #

def load_giveaways():
    if os.path.exists(GIVEAWAYS_FILE):
        with open(GIVEAWAYS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_giveaways(data):
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def parse_duration(s: str):
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(s[:-1]) * units[s[-1]]


# ---------------- BUTTONS ---------------- #

class ParticipateButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.green, custom_id="gw_join")
    async def join(self, interaction: discord.Interaction, _):
        data = load_giveaways()
        key = str(interaction.message.id)

        if key not in data:
            return await interaction.response.send_message("❌ Introuvable", ephemeral=True)

        gw = data[key]

        if gw["ended"]:
            return await interaction.response.send_message("❌ Terminé", ephemeral=True)

        uid = str(interaction.user.id)

        if uid in gw["participants"]:
            gw["participants"].remove(uid)
            msg = "❌ Retiré"
        else:
            gw["participants"].append(uid)
            msg = "✅ Inscrit"

        save_giveaways(data)
        await interaction.response.send_message(msg, ephemeral=True)
        await update_embed(interaction.client, gw, interaction.message)


class ClaimButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Claim", style=discord.ButtonStyle.blurple, custom_id="gw_claim")
    async def claim(self, interaction: discord.Interaction, _):
        data = load_giveaways()
        key = str(interaction.message.id)

        if key not in data:
            return await interaction.response.send_message("❌ Introuvable", ephemeral=True)

        gw = data[key]

        if str(interaction.user.id) not in gw.get("winner_ids", []):
            return await interaction.response.send_message("❌ Pas gagnant", ephemeral=True)

        if datetime.now(tz=timezone.utc).timestamp() > gw["claim_deadline"]:
            return await interaction.response.send_message("❌ Expiré", ephemeral=True)

        if str(interaction.user.id) in gw["claimed"]:
            return await interaction.response.send_message("❌ Déjà fait", ephemeral=True)

        gw["claimed"].append(str(interaction.user.id))
        save_giveaways(data)

        await interaction.response.send_message("✅ Claim réussi", ephemeral=True)


# ---------------- EMBED ---------------- #

async def update_embed(bot, gw, message=None):
    channel = bot.get_channel(int(gw["channel_id"]))
    if not message:
        message = await channel.fetch_message(int(gw["message_id"]))

    embed = discord.Embed(title=f"🎁 {gw['prize']}", color=discord.Color.gold())

    embed.add_field(name="👥 Participants", value=len(gw["participants"]))
    embed.add_field(name="🏆 Gagnants", value=gw["winners"])

    if gw.get("bonus_role"):
        embed.add_field(name="🎭 Bonus", value=f"<@&{gw['bonus_role']}>")

    if gw["ended"]:
        if gw["winner_ids"]:
            embed.description = ", ".join(f"<@{w}>" for w in gw["winner_ids"])
        else:
            embed.description = "😔 Aucun"

        embed.add_field(
            name="⏳ Claim",
            value=f"<t:{int(gw['claim_deadline'])}:R>",
            inline=False
        )

        embed.add_field(
            name="🔄 Rerolls",
            value=str(len(gw.get("rerolled", []))),
            inline=True
        )
    else:
        embed.description = "Clique pour participer"
        embed.timestamp = datetime.fromtimestamp(gw["end_time"], tz=timezone.utc)

    await message.edit(embed=embed)


# ---------------- END ---------------- #

async def end_giveaway(bot, key, data):
    gw = data[key]
    guild = bot.get_guild(int(gw["guild_id"]))

    weighted = []

    for uid in gw["participants"]:
        member = guild.get_member(int(uid))
        if not member:
            continue

        weighted.append(uid)

        if gw["bonus_role"] and discord.utils.get(member.roles, id=int(gw["bonus_role"])):
            weighted.append(uid)

    winners = random.sample(weighted, min(gw["winners"], len(weighted))) if weighted else []

    gw["ended"] = True
    gw["winner_ids"] = winners
    gw["claimed"] = []
    gw["rerolled"] = []
    gw["claim_deadline"] = (
        datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])
    ).timestamp()

    save_giveaways(data)

    channel = bot.get_channel(int(gw["channel_id"]))
    msg = await channel.fetch_message(int(gw["message_id"]))

    await msg.edit(view=ClaimButton())
    await update_embed(bot, gw, msg)


# ---------------- COG ---------------- #

class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @tasks.loop(seconds=10)
    async def loop(self):
        data = load_giveaways()
        now = datetime.now(tz=timezone.utc).timestamp()

        for key, gw in data.items():

            if not gw["ended"] and now >= gw["end_time"]:
                await end_giveaway(self.bot, key, data)

            elif gw["ended"] and now >= gw["claim_deadline"]:

                unclaimed = list(set(gw["winner_ids"]) - set(gw["claimed"]))

                if not unclaimed:
                    continue

                guild = self.bot.get_guild(int(gw["guild_id"]))

                blacklist = set(gw["winner_ids"] + gw["rerolled"])

                pool = []

                for uid in gw["participants"]:
                    if uid in blacklist:
                        continue

                    member = guild.get_member(int(uid))
                    if not member:
                        continue

                    pool.append(uid)

                    if gw["bonus_role"] and discord.utils.get(member.roles, id=int(gw["bonus_role"])):
                        pool.append(uid)

                if not pool:
                    continue

                new = random.choice(pool)

                gw["winner_ids"] = [new]
                gw["claimed"] = []
                gw["rerolled"].extend(unclaimed)
                gw["claim_deadline"] = (
                    datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])
                ).timestamp()

                save_giveaways(data)

                channel = self.bot.get_channel(int(gw["channel_id"]))
                await channel.send(f"🔄 Nouveau gagnant : <@{new}>")

                msg = await channel.fetch_message(int(gw["message_id"]))
                await msg.edit(view=ClaimButton())
                await update_embed(self.bot, gw, msg)

    # -------- CREATE -------- #

    @app_commands.command(name="giveaway_create")
    async def create(
        self,
        interaction: discord.Interaction,
        prix: str,
        durée: str,
        gagnants: int,
        role_bonus: discord.Role = None,
        claim: str = "10m"
    ):
        seconds = parse_duration(durée)
        claim_seconds = parse_duration(claim)

        end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)

        embed = discord.Embed(title=f"🎁 {prix}", description="Clique pour participer")
        embed.timestamp = end_time

        msg = await interaction.channel.send(embed=embed, view=ParticipateButton())

        data = load_giveaways()
        data[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(interaction.channel_id),
            "guild_id": str(interaction.guild_id),
            "prize": prix,
            "winners": gagnants,
            "end_time": end_time.timestamp(),
            "participants": [],
            "ended": False,
            "bonus_role": str(role_bonus.id) if role_bonus else None,
            "claim_time": claim_seconds,
        }

        save_giveaways(data)
        await interaction.response.send_message("✅ Giveaway créé", ephemeral=True)


# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
    bot.add_view(ParticipateButton())
    bot.add_view(ClaimButton())


async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawayCog(bot))
    bot.add_view(ParticipateButton())
