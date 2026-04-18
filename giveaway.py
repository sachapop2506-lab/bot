import discord
from discord import app_commands
from discord.ext import commands, tasks
import json, os, random
from datetime import datetime, timedelta, timezone
from utils import data_path

FILE = data_path("giveaways.json")


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
            return int(s[:-len(u)]) * units[u]
    raise ValueError("Format: 10m / 2h / 1d")


# ---------------- EMBED ---------------- #

async def update(bot, gw, msg=None):
    ch = bot.get_channel(int(gw["channel_id"]))
    if not msg:
        msg = await ch.fetch_message(int(gw["message_id"]))

    e = discord.Embed(title=f"🎁 {gw['prize']}", color=0xFFD700)
    e.add_field(name="👥 Participants", value=len(gw["participants"]))
    e.add_field(name="🏆 Winners", value=gw["winners"])

    if gw.get("bonus_role"):
        e.add_field(name="🎭 Bonus", value=f"<@&{gw['bonus_role']}>")

    if gw["ended"]:
        e.description = ", ".join(f"<@{w}>" for w in gw["winner_ids"]) or "None"
        e.add_field(name="⏳ Claim", value=f"<t:{int(gw['claim_deadline'])}:R>")

    else:
        e.description = "Clique pour participer"
        e.timestamp = datetime.fromtimestamp(gw["end_time"], tz=timezone.utc)

    await msg.edit(embed=e)


# ---------------- MAIN VIEW ---------------- #

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 Join", style=discord.ButtonStyle.green, custom_id="gw_join")
    async def join(self, i: discord.Interaction, _):
        data = load()
        gw = data[str(i.message.id)]
        uid = str(i.user.id)

        if uid in gw["participants"]:
            gw["participants"].remove(uid)
        else:
            gw["participants"].append(uid)

        save(data)
        await i.response.send_message("OK", ephemeral=True)
        await update(i.client, gw, i.message)


    @discord.ui.button(label="⚙️ Manage", style=discord.ButtonStyle.gray, custom_id="gw_manage")
    async def manage(self, i: discord.Interaction, _):
        data = load()
        gw = data[str(i.message.id)]

        if str(i.user.id) != gw["host_id"]:
            return await i.response.send_message("No permission", ephemeral=True)

        view = ManageView(gw)
        view.build()

        await i.response.send_message("Manage:", view=view, ephemeral=True)


# ---------------- PAGINATION ---------------- #

class ManageView(discord.ui.View):
    def __init__(self, gw):
        super().__init__(timeout=120)
        self.gw = gw
        self.page = 0

    def build(self):
        self.clear_items()

        start = self.page * 25
        end = start + 25
        page = self.gw["participants"][start:end]

        options = [
            discord.SelectOption(label=f"{uid}", value=uid)
            for uid in page
        ]

        self.add_item(RemoveSelect(self.gw, options))

        if self.page > 0:
            self.add_item(Prev())
        if end < len(self.gw["participants"]):
            self.add_item(Next())


    async def refresh(self, i):
        self.build()
        await i.response.edit_message(view=self)


class RemoveSelect(discord.ui.Select):
    def __init__(self, gw, options):
        super().__init__(
            placeholder="Remove user",
            options=options,
            min_values=1,
            max_values=1
        )
        self.gw = gw

    async def callback(self, i: discord.Interaction):
        data = load()
        gw = data[str(i.message.id)]

        uid = self.values[0]
        if uid in gw["participants"]:
            gw["participants"].remove(uid)

        save(data)

        await update(i.client, gw, i.message)
        await i.response.send_message("Removed", ephemeral=True)


class Next(discord.ui.Button):
    def __init__(self):
        super().__init__(label="➡️")

    async def callback(self, i):
        v: ManageView = self.view
        v.page += 1
        await v.refresh(i)


class Prev(discord.ui.Button):
    def __init__(self):
        super().__init__(label="⬅️")

    async def callback(self, i):
        v: ManageView = self.view
        v.page -= 1
        await v.refresh(i)


# ---------------- CLAIM ---------------- #

class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎁 Claim", style=discord.ButtonStyle.blurple, custom_id="gw_claim")
    async def claim(self, i: discord.Interaction, _):
        data = load()
        gw = data[str(i.message.id)]

        if str(i.user.id) not in gw["winner_ids"]:
            return await i.response.send_message("Not winner", ephemeral=True)

        if datetime.now(tz=timezone.utc).timestamp() > gw["claim_deadline"]:
            return await i.response.send_message("Expired", ephemeral=True)

        if str(i.user.id) in gw["claimed"]:
            return await i.response.send_message("Already claimed", ephemeral=True)

        gw["claimed"].append(str(i.user.id))
        save(data)

        await i.response.send_message("Claimed!", ephemeral=True)


# ---------------- END + REROLL ---------------- #

async def end(bot, key, data):
    gw = data[key]
    guild = bot.get_guild(int(gw["guild_id"]))

    pool = []

    for uid in gw["participants"]:
        m = guild.get_member(int(uid))
        if not m:
            continue

        pool.append(uid)

        if gw.get("bonus_role") and discord.utils.get(m.roles, id=int(gw["bonus_role"])):
            pool.append(uid)

    winners = random.sample(pool, min(gw["winners"], len(pool))) if pool else []

    gw["ended"] = True
    gw["winner_ids"] = winners
    gw["claimed"] = []
    gw["rerolled"] = []
    gw["claim_deadline"] = (datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])).timestamp()

    save(data)

    ch = bot.get_channel(int(gw["channel_id"]))
    msg = await ch.fetch_message(int(gw["message_id"]))

    await msg.edit(view=ClaimView())
    await update(bot, gw, msg)


# ---------------- LOOP ---------------- #

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    @tasks.loop(seconds=10)
    async def loop(self):
        data = load()
        now = datetime.now(tz=timezone.utc).timestamp()

        for k, gw in data.items():

            if not gw["ended"] and now >= gw["end_time"]:
                await end(self.bot, k, data)

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

                    m = guild.get_member(int(uid))
                    if not m:
                        continue

                    pool.append(uid)

                    if gw.get("bonus_role") and discord.utils.get(m.roles, id=int(gw["bonus_role"])):
                        pool.append(uid)

                if not pool:
                    continue

                new = random.choice(pool)

                gw["winner_ids"] = [new]
                gw["claimed"] = []
                gw["rerolled"].extend(unclaimed)
                gw["claim_deadline"] = (datetime.now(tz=timezone.utc) + timedelta(seconds=gw["claim_time"])).timestamp()

                save(data)

                ch = self.bot.get_channel(int(gw["channel_id"]))
                await ch.send(f"🔄 New winner: <@{new}>")

                msg = await ch.fetch_message(int(gw["message_id"]))
                await msg.edit(view=ClaimView())
                await update(self.bot, gw, msg)


    @app_commands.command(name="giveaway_create")
    async def create(self, i: discord.Interaction, prize: str, duration: str, winners: int, role_bonus: discord.Role = None, claim: str = "10m"):

        seconds = parse(duration)
        claim_s = parse(claim)

        end = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)

        msg = await i.channel.send(
            embed=discord.Embed(title=f"🎁 {prize}", description="Join now"),
            view=GiveawayView()
        )

        data = load()
        data[str(msg.id)] = {
            "message_id": str(msg.id),
            "channel_id": str(i.channel_id),
            "guild_id": str(i.guild_id),
            "host_id": str(i.user.id),
            "prize": prize,
            "winners": winners,
            "participants": [],
            "ended": False,
            "end_time": end.timestamp(),
            "bonus_role": str(role_bonus.id) if role_bonus else None,
            "claim_time": claim_s
        }

        save(data)
        await i.response.send_message("Created", ephemeral=True)


# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
    bot.add_view(GiveawayView())
    bot.add_view(ClaimView())
