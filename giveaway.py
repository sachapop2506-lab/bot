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
    for step in ["🎲 .", "🎲 ..", "🎲 ..."]:
        await asyncio.sleep(0.6)
        await msg.edit(content=step)
    return msg

# ---------------- WINNER UI ---------------- #

async def send_winner_ui(bot, gw, winner_id, data):
    ch = bot.get_channel(int(gw["channel_id"]))

    embed = discord.Embed(
        title="🏆 Nouveau gagnant",
        description=f"🎉 Bravo <@{winner_id}>",
        color=0x00ff00
    )

    embed.add_field(
        name="⏳ Temps pour claim",
        value=f"<t:{int(gw['claim_deadline'])}:R>"
    )

    msg = await ch.send(embed=embed, view=ClaimView())

    # 🔑 on stocke le message pour le claim
    gw["last_winner_message"] = str(msg.id)
    save(data)

# ---------------- CLAIM ---------------- #

class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎁 Claim",
        style=discord.ButtonStyle.green,
        custom_id="gw_claim"
    )
    async def claim(self, i: discord.Interaction, _):
        data = load()
        gw = None

        # retrouver le bon giveaway
        for g in data.values():
            if g.get("last_winner_message") == str(i.message.id):
                gw = g
                break

        if not gw:
            return await i.response.send_message("Erreur", ephemeral=True)

        uid = str(i.user.id)

        if uid not in gw["winner_ids"]:
            return await i.response.send_message("Pas gagnant", ephemeral=True)

        if datetime.now(tz=timezone.utc).timestamp() > gw["claim_deadline"]:
            return await i.response.send_message("Temps expiré", ephemeral=True)

        if uid in gw["claimed"]:
            return await i.response.send_message("Déjà claim", ephemeral=True)

        gw["claimed"].append(uid)
        save(data)

        await i.response.send_message("🎉 Récompense récupérée !", ephemeral=True)

# ---------------- JOIN ---------------- #

class JoinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🎉 Participer",
        style=discord.ButtonStyle.blurple,
        custom_id="gw_join"
    )
    async def join(self, i: discord.Interaction, _):
        data = load()
        gw = data.get(str(i.message.id))

        if not gw:
            return await i.response.send_message("Erreur", ephemeral=True)

        uid = str(i.user.id)

        if uid in gw["participants"]:
            gw["participants"].remove(uid)
        else:
            gw["participants"].append(uid)

        save(data)
        await i.response.send_message("Participation mise à jour", ephemeral=True)

# ---------------- LOGIC ---------------- #

def draw_winner(bot, gw):
    guild = bot.get_guild(int(gw["guild_id"]))
    pool = []

    for uid in gw["participants"]:
        m = guild.get_member(int(uid))
        if not m:
            continue
        pool.append(uid)

    return random.choice(pool) if pool else None

async def process_winner(bot, gw, data):
    ch = bot.get_channel(int(gw["channel_id"]))

    await suspense(ch)

    winner = draw_winner(bot, gw)
    if not winner:
        await ch.send("❌ Aucun participant valide")
        return

    gw["winner_ids"] = [winner]
    gw["claimed"] = []

    gw["claim_deadline"] = (
        datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])
    ).timestamp()

    save(data)

    await send_winner_ui(bot, gw, winner, data)

# ---------------- LOOP ---------------- #

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @tasks.loop(seconds=5)
    async def loop(self):
        data = load()
        now = datetime.now(tz=timezone.utc).timestamp()

        for k, gw in data.items():

            # fin initiale
            if not gw["ended"] and now >= gw["end_time"]:
                gw["ended"] = True
                await process_winner(self.bot, gw, data)

            # reroll auto infini
            elif gw["ended"] and now >= gw["claim_deadline"]:
                if set(gw["winner_ids"]) - set(gw["claimed"]):
                    await process_winner(self.bot, gw, data)

    # ---------------- COMMANDES ---------------- #

    @app_commands.command(name="giveaway_create")
    async def create(self, i: discord.Interaction, prize: str, duration: str):
        seconds = parse(duration)

        msg = await i.channel.send(
            embed=discord.Embed(
                title=f"🎁 {prize}",
                description="Clique pour participer"
            ),
            view=JoinView()
        )

        data = load()
        data[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(i.channel_id),
            "guild_id": str(i.guild_id),
            "host_id": str(i.user.id),
            "participants": [],
            "ended": False,
            "end_time": (datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)).timestamp(),
            "claim_time": 600
        }

        save(data)
        await i.response.send_message("✅ Giveaway créé", ephemeral=True)

    @app_commands.command(name="giveaway_reroll")
    async def reroll(self, i: discord.Interaction, message_id: str):
        data = load()
        gw = data.get(message_id)

        if not gw:
            return await i.response.send_message("Introuvable", ephemeral=True)

        if str(i.user.id) != gw["host_id"]:
            return await i.response.send_message("Pas permission", ephemeral=True)

        await process_winner(self.bot, gw, data)
        await i.response.send_message("🔁 Reroll effectué", ephemeral=True)

# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
    bot.add_view(JoinView())
    bot.add_view(ClaimView())
