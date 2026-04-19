import discord
from discord.ext import commands, tasks
from discord import app_commands
import json, os, random, asyncio
from datetime import datetime, timedelta, timezone

FILE = "giveaways.json"

# ---------------- STORAGE ---------------- #

def load():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse(s: str):
    s = s.lower().strip()
    units = {"s":1,"m":60,"h":3600,"d":86400}
    for u in units:
        if s.endswith(u):
            return int(s[:-1]) * units[u]
    raise ValueError("Format: 10m / 2h / 1d")

# ---------------- ANIMATION ---------------- #

async def suspense(channel):
    msg = await channel.send("🎲 Tirage...")
    for step in ["🎲 .","🎲 ..","🎲 ..."]:
        await asyncio.sleep(0.5)
        await msg.edit(content=step)

# ---------------- EMBED ---------------- #

async def update_embed(bot, gw, msg):
    guild = bot.get_guild(int(gw["guild_id"]))

    members = [guild.get_member(int(uid)) for uid in gw["participants"] if guild.get_member(int(uid))]

    e = discord.Embed(
        title=f"🎁 {gw['prize']}",
        description="Clique pour participer 🎉",
        color=0xFFD700
    )

    e.add_field(name="👥 Participants", value=f"**{len(members)}**", inline=True)
    e.add_field(name="🏆 Gagnants", value=f"**{gw['winners']}**", inline=True)

    if gw.get("bonus_role"):
        e.add_field(name="🎭 Bonus", value=f"<@&{gw['bonus_role']}> (x2 chances)", inline=False)

    if not gw["ended"]:
        e.add_field(name="⏳ Fin", value=f"<t:{int(gw['end_time'])}:R>", inline=False)

    preview = "\n".join(f"• {m.mention}" for m in members[:5]) or "Personne"
    e.add_field(name="👀 Aperçu", value=preview, inline=False)

    await msg.edit(embed=e)

# ---------------- WINNER UI ---------------- #

async def send_winner_ui(bot, gw, winners, data):
    ch = bot.get_channel(int(gw["channel_id"]))
    ts = int(gw["claim_deadline"])

    mentions = " ".join(f"<@{w}>" for w in winners)

    await ch.send(f"🎉 {mentions} vous avez gagné !")

    embed = discord.Embed(
        title="🏆 Gagnant(s)",
        description=mentions,
        color=0x00ff00
    )

    embed.add_field(
        name="⏳ Claim",
        value=f"<t:{ts}:F>\n<t:{ts}:R>"
    )

    msg = await ch.send(embed=embed, view=ClaimView())

    gw["last_winner_message"] = str(msg.id)
    gw["reminder_sent"] = False
    save(data)

# ---------------- CLAIM ---------------- #

class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Claim", style=discord.ButtonStyle.green, custom_id="gw_claim")
    async def claim(self, i: discord.Interaction, _):
        data = load()

        gw = None
        for g in data.values():
            if g.get("last_winner_message") == str(i.message.id):
                gw = g
                break

        if not gw:
            return await i.response.send_message("Erreur", ephemeral=True)

        uid = str(i.user.id)

        if uid not in gw["winner_ids"]:
            return await i.response.send_message("Pas gagnant", ephemeral=True)

        if uid in gw["claimed"]:
            return await i.response.send_message("Déjà claim", ephemeral=True)

        gw["claimed"].append(uid)
        save(data)

        embed = discord.Embed(
            title="🎉 GG !",
            description=f"Bravo <@{uid}> tu as gagné **{gw['prize']}** !",
            color=0x2ecc71
        )

        await i.channel.send(embed=embed)
        await i.response.send_message("Claim réussi", ephemeral=True)

# ---------------- VIEW ---------------- #

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 Join", style=discord.ButtonStyle.green, custom_id="gw_join")
    async def join(self, i: discord.Interaction, _):
        data = load()
        gw = data.get(str(i.message.id))

        uid = str(i.user.id)

        if uid in gw["participants"]:
            gw["participants"].remove(uid)
        else:
            gw["participants"].append(uid)

        save(data)
        await update_embed(i.client, gw, i.message)
        await i.response.send_message("OK", ephemeral=True)

    @discord.ui.button(label="⚙️ Manage", style=discord.ButtonStyle.gray, custom_id="gw_manage")
    async def manage(self, i: discord.Interaction, _):
        data = load()
        gw = data.get(str(i.message.id))

        if str(i.user.id) != gw["host_id"]:
            return await i.response.send_message("No permission", ephemeral=True)

        gw["_guild"] = i.guild
        view = ManageView(gw)
        view.build()

        await i.response.send_message("Manage", view=view, ephemeral=True)

# ---------------- MANAGE ---------------- #

class ManageView(discord.ui.View):
    def __init__(self, gw):
        super().__init__(timeout=120)
        self.gw = gw
        self.page = 0

    def build(self):
        self.clear_items()
        guild = self.gw["_guild"]

        page = self.gw["participants"][self.page*25:(self.page+1)*25]

        options = []
        for uid in page:
            m = guild.get_member(int(uid))
            if m:
                options.append(discord.SelectOption(label=m.display_name, value=uid))
            else:
                options.append(discord.SelectOption(label=f"User {uid}", value=uid))

        self.add_item(RemoveSelect(self.gw, options))

    async def refresh(self, i):
        self.build()
        await i.response.edit_message(view=self)

class RemoveSelect(discord.ui.Select):
    def __init__(self, gw, options):
        super().__init__(placeholder="Retirer", options=options)
        self.gw = gw

    async def callback(self, i):
        data = load()
        gw = data[self.gw["message_id"]]

        uid = self.values[0]

        if uid in gw["participants"]:
            gw["participants"].remove(uid)

        save(data)

        ch = i.client.get_channel(int(gw["channel_id"]))
        msg = await ch.fetch_message(int(gw["message_id"]))
        await update_embed(i.client, gw, msg)

        await i.response.send_message("Retiré", ephemeral=True)

# ---------------- LOGIC ---------------- #

def draw_winners(bot, gw):
    guild = bot.get_guild(int(gw["guild_id"]))
    pool = []

    for uid in gw["participants"]:
        m = guild.get_member(int(uid))
        if not m:
            continue

        pool.append(uid)

        if gw.get("bonus_role") and discord.utils.get(m.roles, id=int(gw["bonus_role"])):
            pool.append(uid)

    return random.sample(pool, min(gw["winners"], len(pool))) if pool else []

async def process_winner(bot, gw, data):
    ch = bot.get_channel(int(gw["channel_id"]))
    await suspense(ch)

    winners = draw_winners(bot, gw)

    if not winners:
        await ch.send("❌ Aucun participant")
        return

    gw["winner_ids"] = winners
    gw["claimed"] = []
    gw["claim_deadline"] = (datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])).timestamp()

    save(data)
    await send_winner_ui(bot, gw, winners, data)

# ---------------- LOOP ---------------- #

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @tasks.loop(seconds=5)
    async def loop(self):
        data = load()
        now = datetime.now(tz=timezone.utc).timestamp()

        for gw in data.values():

            if not gw["ended"] and now >= gw["end_time"]:
                gw["ended"] = True
                await process_winner(self.bot, gw, data)

            elif gw["ended"] and now >= gw["claim_deadline"]:
                if set(gw["winner_ids"]) - set(gw["claimed"]):
                    await process_winner(self.bot, gw, data)

    # ---------------- COMMANDES ---------------- #

    @app_commands.command(name="giveaway_create")
    async def create(
        self,
        i: discord.Interaction,
        prize: str,
        duration: str,
        winners: int,
        claim: str,
        role_bonus: discord.Role = None
    ):
        seconds = parse(duration)
        claim_s = parse(claim)

        msg = await i.channel.send(
            embed=discord.Embed(title=f"🎁 {prize}", description="Clique pour participer"),
            view=GiveawayView()
        )

        data = load()
        data[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(i.channel_id),
            "guild_id": str(i.guild_id),
            "host_id": str(i.user.id),
            "prize": prize,
            "participants": [],
            "winners": winners,
            "bonus_role": str(role_bonus.id) if role_bonus else None,
            "ended": False,
            "end_time": (datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)).timestamp(),
            "claim_time": claim_s
        }

        save(data)
        await update_embed(self.bot, data[str(msg.id)], msg)

        await i.response.send_message("Giveaway créé", ephemeral=True)

# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
    bot.add_view(GiveawayView())
    bot.add_view(ClaimView())
