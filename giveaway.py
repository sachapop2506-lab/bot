import discord
from discord import app_commands
from discord.ext import commands, tasks
import json, os, random
from datetime import datetime, timedelta, timezone
from utils import data_path

GIVEAWAYS_FILE = data_path("giveaways.json")

# ---------- FILE ---------- #

def load_giveaways():
    if os.path.exists(GIVEAWAYS_FILE):
        with open(GIVEAWAYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_giveaways(data):
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_duration(s: str):
    s = s.lower().strip()
    units = {"s":1,"sec":1,"m":60,"min":60,"h":3600,"d":86400}
    for u in units:
        if s.endswith(u):
            return int(s[:-len(u)]) * units[u]
    raise ValueError("Format invalide (10m, 2h, 1d)")

# ---------- EMBED ---------- #

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
        embed.description = ", ".join(f"<@{w}>" for w in gw["winner_ids"]) or "😔 Aucun"
        embed.add_field(name="⏳ Claim", value=f"<t:{int(gw['claim_deadline'])}:R>", inline=False)
    else:
        embed.description = "Clique pour participer"
        embed.timestamp = datetime.fromtimestamp(gw["end_time"], tz=timezone.utc)

    await message.edit(embed=embed)

# ---------- PARTICIPATION + MANAGE ---------- #

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 Participer", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, _):
        data = load_giveaways()
        key = str(interaction.message.id)
        gw = data[key]

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

    @discord.ui.button(label="⚙️ Gérer", style=discord.ButtonStyle.gray)
    async def manage(self, interaction: discord.Interaction, _):
        data = load_giveaways()
        key = str(interaction.message.id)
        gw = data[key]

        if str(interaction.user.id) != gw["host_id"]:
            return await interaction.response.send_message("❌ Non autorisé", ephemeral=True)

        view = ManageParticipantsView(gw)
        view.update_select()

        await interaction.response.send_message(
            "⚙️ Gestion participants", view=view, ephemeral=True
        )

# ---------- PAGINATION ---------- #

class ManageParticipantsView(discord.ui.View):
    def __init__(self, gw):
        super().__init__(timeout=120)
        self.gw = gw
        self.page = 0

    def get_page(self):
        p = self.gw["participants"]
        return p[self.page*25:(self.page+1)*25], len(p)

    def update_select(self):
        self.clear_items()
        page_data, total = self.get_page()

        options = [discord.SelectOption(label=uid, value=uid) for uid in page_data]
        self.add_item(RemoveSelect(self.gw, options))

        if self.page > 0:
            self.add_item(PrevButton())
        if (self.page+1)*25 < total:
            self.add_item(NextButton())

    async def refresh(self, interaction):
        self.update_select()
        await interaction.response.edit_message(view=self)

class RemoveSelect(discord.ui.Select):
    def __init__(self, gw, options):
        super().__init__(placeholder="Retirer", options=options)
        self.gw = gw

    async def callback(self, interaction: discord.Interaction):
        data = load_giveaways()
        key = str(interaction.message.id)
        gw = data[key]

        uid = self.values[0]
        if uid in gw["participants"]:
            gw["participants"].remove(uid)

        save_giveaways(data)

        channel = interaction.client.get_channel(int(gw["channel_id"]))
        msg = await channel.fetch_message(int(gw["message_id"]))
        await update_embed(interaction.client, gw, msg)

        await interaction.response.send_message(f"✅ <@{uid}> retiré", ephemeral=True)

class NextButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="➡️")

    async def callback(self, interaction):
        self.view.page += 1
        await self.view.refresh(interaction)

class PrevButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⬅️")

    async def callback(self, interaction):
        self.view.page -= 1
        await self.view.refresh(interaction)

# ---------- CLAIM ---------- #

class ClaimButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Claim", style=discord.ButtonStyle.blurple)
    async def claim(self, interaction: discord.Interaction, _):
        data = load_giveaways()
        key = str(interaction.message.id)
        gw = data[key]

        if str(interaction.user.id) not in gw["winner_ids"]:
            return await interaction.response.send_message("❌ Pas gagnant", ephemeral=True)

        if datetime.now(tz=timezone.utc).timestamp() > gw["claim_deadline"]:
            return await interaction.response.send_message("❌ Expiré", ephemeral=True)

        gw["claimed"].append(str(interaction.user.id))
        save_giveaways(data)

        await interaction.response.send_message("✅ Claim OK", ephemeral=True)

# ---------- END + REROLL ---------- #

async def end_giveaway(bot, key, data):
    gw = data[key]
    guild = bot.get_guild(int(gw["guild_id"]))

    pool = []
    for uid in gw["participants"]:
        member = guild.get_member(int(uid))
        if not member:
            continue
        pool.append(uid)
        if gw["bonus_role"] and discord.utils.get(member.roles, id=int(gw["bonus_role"])):
            pool.append(uid)

    winners = random.sample(pool, min(gw["winners"], len(pool))) if pool else []

    gw["ended"] = True
    gw["winner_ids"] = winners
    gw["claimed"] = []
    gw["rerolled"] = []
    gw["claim_deadline"] = (datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])).timestamp()

    save_giveaways(data)

    channel = bot.get_channel(int(gw["channel_id"]))
    msg = await channel.fetch_message(int(gw["message_id"]))
    await msg.edit(view=ClaimButton())
    await update_embed(bot, gw, msg)

# ---------- LOOP ---------- #

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

                blacklist = set(gw["winner_ids"] + gw["rerolled"])
                pool = [u for u in gw["participants"] if u not in blacklist]

                if not pool:
                    continue

                new = random.choice(pool)

                gw["winner_ids"] = [new]
                gw["claimed"] = []
                gw["rerolled"].extend(unclaimed)
                gw["claim_deadline"] = (datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])).timestamp()

                save_giveaways(data)

                channel = self.bot.get_channel(int(gw["channel_id"]))
                await channel.send(f"🔄 Nouveau gagnant : <@{new}>")

                msg = await channel.fetch_message(int(gw["message_id"]))
                await msg.edit(view=ClaimButton())
                await update_embed(self.bot, gw, msg)

    # ---------- CREATE ---------- #

    @app_commands.command(name="giveaway_create")
    async def create(self, interaction: discord.Interaction, prix: str, durée: str, gagnants: int, role_bonus: discord.Role = None, claim: str = "10m"):
        try:
            seconds = parse_duration(durée)
            claim_seconds = parse_duration(claim)
        except:
            return await interaction.response.send_message("❌ Format invalide", ephemeral=True)

        end_time = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)

        embed = discord.Embed(title=f"🎁 {prix}", description="Clique pour participer")
        embed.timestamp = end_time

        msg = await interaction.channel.send(embed=embed, view=GiveawayView())

        data = load_giveaways()
        data[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(interaction.channel_id),
            "guild_id": str(interaction.guild_id),
            "host_id": str(interaction.user.id),
            "prize": prix,
            "winners": gagnants,
            "participants": [],
            "ended": False,
            "end_time": end_time.timestamp(),
            "bonus_role": str(role_bonus.id) if role_bonus else None,
            "claim_time": claim_seconds
        }

        save_giveaways(data)
        await interaction.response.send_message("✅ Créé", ephemeral=True)

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))
    bot.add_view(GiveawayView())
    bot.add_view(ClaimButton())
