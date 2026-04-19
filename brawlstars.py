import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "bs_game.json"

# ---------------- DATA ---------------- #

def load():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_player(data, user_id):
    if user_id not in data:
        data[user_id] = {
            "trophies": 0,
            "coins": 100,
            "brawlers": ["Shelly"],
            "selected": "Shelly"
        }
    return data[user_id]

# ---------------- BRAWLERS ---------------- #

BRAWLERS = {
    "Shelly": {"hp": 100, "min": 10, "max": 20},
    "Colt": {"hp": 90, "min": 12, "max": 22},
    "Bull": {"hp": 120, "min": 8, "max": 25},
    "Jessie": {"hp": 95, "min": 11, "max": 18},
}

ALL_BRAWLERS = list(BRAWLERS.keys())

# ---------------- COG ---------------- #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------- PROFIL -------- #

    @app_commands.command(name="bs_profile")
    async def profile(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))
        save(data)

        embed = discord.Embed(title=f"👤 {i.user.name}", color=0xf1c40f)
        embed.add_field(name="🏆 Trophées", value=p["trophies"])
        embed.add_field(name="🪙 Pièces", value=p["coins"])
        embed.add_field(name="🎮 Brawler", value=p["selected"])
        embed.add_field(name="📦 Collection", value=", ".join(p["brawlers"]))

        await i.response.send_message(embed=embed)

    # -------- BOX -------- #

    @app_commands.command(name="bs_open")
    async def open_box(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        reward = random.choices(["coins", "brawler"], weights=[70, 30])[0]

        if reward == "coins":
            amount = random.randint(20, 100)
            p["coins"] += amount
            msg = f"🪙 +{amount} pièces"
        else:
            new = random.choice(ALL_BRAWLERS)
            if new in p["brawlers"]:
                p["coins"] += 50
                msg = "🔁 Doublon → +50 pièces"
            else:
                p["brawlers"].append(new)
                msg = f"🎉 Nouveau brawler : {new}"

        save(data)
        await i.response.send_message(msg)

    # -------- SELECT -------- #

    @app_commands.command(name="bs_select")
    async def select(self, i: discord.Interaction, brawler: str):
        data = load()
        p = get_player(data, str(i.user.id))

        if brawler not in p["brawlers"]:
            return await i.response.send_message("❌ Tu ne l'as pas")

        p["selected"] = brawler
        save(data)

        await i.response.send_message(f"✅ {brawler} sélectionné")

    # -------- FIGHT -------- #

   @app_commands.command(name="bs_fight")
async def fight(self, i: discord.Interaction):
    data = load()
    p = get_player(data, str(i.user.id))

    player = p["selected"]
    enemy = random.choice(ALL_BRAWLERS)

    ps = BRAWLERS[player]
    es = BRAWLERS[enemy]

    view = FightView(i.user.id, player, enemy, ps, es, data)

    embed = view.get_embed()

    await i.response.send_message(embed=embed, view=view)
# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
