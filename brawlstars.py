import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "bs_full.json"

# ---------- DATA ---------- #

def load():
    if os.path.exists(FILE):
        with open(FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_player(data, uid):
    if uid not in data:
        data[uid] = {
            "coins": 0,
            "trophies": 0,
            "boxes": 5,
            "selected": "Shelly",
            "brawlers": {
                "Shelly": {"level":1,"pp":0}
            }
        }
    return data[uid]

# ---------- BRAWLERS ---------- #

BRAWLERS = {
    "Shelly": {"rarity":"Common"},
    "Nita": {"rarity":"Rare"},
    "Colt": {"rarity":"Rare"},
    "Bull": {"rarity":"Epic"},
    "Jessie": {"rarity":"Super Rare"},
    "Spike": {"rarity":"Legendary"},
}

RARITY = {
    "Common": 60,
    "Rare": 25,
    "Super Rare": 10,
    "Epic": 4,
    "Legendary": 1
}

# ---------- UTILS ---------- #

def get_multiplier(trophies):
    return 1 + (trophies // 100) * 0.2

def roll_rarity():
    r = random.randint(1, 100)
    total = 0
    for rarity, chance in RARITY.items():
        total += chance
        if r <= total:
            return rarity

def random_brawler(rarity):
    return random.choice([b for b,v in BRAWLERS.items() if v["rarity"] == rarity])

# ---------- BOX ---------- #

def open_box(p):
    rewards = []

    coins = random.randint(20, 80)
    p["coins"] += coins
    rewards.append(f"🪙 {coins} coins")

    rarity = roll_rarity()
    brawler = random_brawler(rarity)

    if brawler not in p["brawlers"]:
        p["brawlers"][brawler] = {"level":1,"pp":0}
        rewards.append(f"✨ Nouveau {brawler} ({rarity})")
    else:
        pp = random.randint(10, 25)
        p["brawlers"][brawler]["pp"] += pp
        rewards.append(f"⚡ {brawler} +{pp} PP")

    return rewards

# ---------- SELECT MENU ---------- #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
            discord.SelectOption(label=b, description=f"Level {player['brawlers'][b]['level']}")
            for b in player["brawlers"]
        ]
        super().__init__(placeholder="Choisir un brawler", options=options)

    async def callback(self, interaction):
        data = load()
        p = get_player(data, str(interaction.user.id))

        p["selected"] = self.values[0]
        save(data)

        await interaction.response.send_message(
            f"✅ {self.values[0]} sélectionné",
            ephemeral=True
        )

# ---------- MAIN VIEW ---------- #

class MainView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, i):
        return i.user.id == self.user.id

    @discord.ui.button(label="👊 Click", style=discord.ButtonStyle.primary)
    async def click(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        multi = get_multiplier(p["trophies"])
        gain = int(random.randint(5,15) * multi)

        p["coins"] += gain
        p["trophies"] += 1

        bonus = ""
        if random.randint(1,10) == 1:
            p["boxes"] += 1
            bonus = " 🎁 box!"

        save(data)

        await i.response.edit_message(
            content=f"👊 +{gain} coins (x{multi:.1f}) | 🏆 +1{bonus}",
            view=self
        )

    @discord.ui.button(label="🎁 Box", style=discord.ButtonStyle.success)
    async def box(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.response.send_message("❌ Pas de box", ephemeral=True)

        p["boxes"] -= 1
        rewards = open_box(p)

        save(data)

        await i.response.send_message("\n".join(rewards), ephemeral=True)

    @discord.ui.button(label="⬆️ Upgrade", style=discord.ButtonStyle.secondary)
    async def upgrade(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        info = p["brawlers"][b]

        cost = 50 * info["level"]

        if info["pp"] < cost:
            return await i.response.send_message(
                f"❌ Pas assez de PP ({cost})",
                ephemeral=True
            )

        info["pp"] -= cost
        info["level"] += 1

        save(data)

        await i.response.send_message(
            f"⬆️ {b} level {info['level']}",
            ephemeral=True
        )

# ---------- COG ---------- #

class BSFull(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bs")
    async def bs(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        view = MainView(i.user)
        view.add_item(BrawlerSelect(p))

        txt = f"""
🏆 {p['trophies']} | 🪙 {p['coins']} | 🎁 {p['boxes']}
🎯 Actif: {p['selected']}
💰 Multiplicateur: x{get_multiplier(p['trophies']):.1f}
"""

        await i.response.send_message(txt, view=view, ephemeral=True)

    @app_commands.command(name="leaderboard")
    async def leaderboard(self, i: discord.Interaction):
        data = load()

        top = sorted(data.items(), key=lambda x: x[1]["trophies"], reverse=True)[:10]

        txt = "\n".join([
            f"<@{uid}> - {p['trophies']}🏆"
            for uid, p in top
        ])

        await i.response.send_message(f"🏆 Classement:\n{txt}")

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSFull(bot))
