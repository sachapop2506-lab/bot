import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "bs_advanced.json"

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
            "pity": 0,
            "brawlers": {
                "Shelly": {
                    "level": 1,
                    "pp": 0,
                    "gadgets": 0,
                    "starpower": False
                }
            }
        }
    return data[uid]

# ---------- BRAWLERS ---------- #

BRAWLERS = {
    "Shelly": {"rarity": "Common", "hp": 100, "dmg": 15},
    "Nita": {"rarity": "Rare", "hp": 110, "dmg": 13},
    "Colt": {"rarity": "Rare", "hp": 90, "dmg": 18},
    "Bull": {"rarity": "Epic", "hp": 140, "dmg": 12},
    "Jessie": {"rarity": "Super Rare", "hp": 95, "dmg": 14},
    "Spike": {"rarity": "Legendary", "hp": 80, "dmg": 22},
}

RARITY = {
    "Common": 60,
    "Rare": 25,
    "Super Rare": 10,
    "Epic": 4,
    "Legendary": 1
}

# ---------- DROP SYSTEM ---------- #

def roll_rarity(pity):
    chances = RARITY.copy()

    # PITY SYSTEM
    chances["Legendary"] += pity

    r = random.randint(1, sum(chances.values()))
    total = 0
    for rarity, val in chances.items():
        total += val
        if r <= total:
            return rarity

def get_brawler(rarity):
    return random.choice([b for b,v in BRAWLERS.items() if v["rarity"] == rarity])

# ---------- BOX ---------- #

def open_box(p):
    rewards = []
    coins = random.randint(20, 70)
    p["coins"] += coins
    rewards.append(f"🪙 {coins} coins")

    rarity = roll_rarity(p["pity"])
    brawler = get_brawler(rarity)

    if rarity == "Legendary":
        p["pity"] = 0
    else:
        p["pity"] += 1

    if brawler not in p["brawlers"]:
        p["brawlers"][brawler] = {"level":1,"pp":0,"gadgets":0,"starpower":False}
        rewards.append(f"✨ NEW {brawler} ({rarity})")
    else:
        pp = random.randint(5, 25)
        p["brawlers"][brawler]["pp"] += pp
        rewards.append(f"⚡ {brawler} +{pp}pp")

    return rewards

# ---------- FIGHT ---------- #

def simulate_fight(p1, p2):
    b1 = BRAWLERS[p1["selected"]]
    b2 = BRAWLERS[p2["selected"]]

    hp1 = b1["hp"] + p1["brawlers"][p1["selected"]]["level"] * 5
    hp2 = b2["hp"] + p2["brawlers"][p2["selected"]]["level"] * 5

    while hp1 > 0 and hp2 > 0:
        hp2 -= b1["dmg"]
        if hp2 <= 0:
            return True
        hp1 -= b2["dmg"]

    return False

# ---------- VIEWS ---------- #

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

        gain = random.randint(5,15)
        p["coins"] += gain
        p["trophies"] += 1

        if random.randint(1,10) == 1:
            p["boxes"] += 1
            bonus = " 🎁 box gagnée!"
        else:
            bonus = ""

        save(data)

        await i.response.edit_message(
            content=f"👊 +{gain} coins | 🏆 +1{bonus}",
            view=self
        )

    @discord.ui.button(label="🎁 Box", style=discord.ButtonStyle.success)
    async def box(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.response.send_message("❌ 0 box", ephemeral=True)

        p["boxes"] -= 1
        rewards = open_box(p)

        save(data)

        await i.response.send_message(
            "\n".join(rewards),
            ephemeral=True
        )

    @discord.ui.button(label="⚔️ Fight IA", style=discord.ButtonStyle.danger)
    async def fight_ai(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        bot_p = {
            "selected": random.choice(list(BRAWLERS.keys())),
            "brawlers": {b: {"level": random.randint(1,5)} for b in BRAWLERS}
        }

        win = simulate_fight(p, bot_p)

        if win:
            p["trophies"] += 10
            result = "🏆 Victoire +10"
        else:
            result = "💀 Défaite"

        save(data)

        await i.response.send_message(result, ephemeral=True)

# ---------- COG ---------- #

class BSAdvanced(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bs")
    async def bs(self, i: discord.Interaction):
        p = get_player(load(), str(i.user.id))

        txt = f"""
🏆 {p['trophies']} | 🪙 {p['coins']} | 🎁 {p['boxes']}
🎯 Brawler: {p['selected']}
🔥 Pity: {p['pity']}
"""

        await i.response.send_message(
            txt,
            view=MainView(i.user),
            ephemeral=True
        )

    @app_commands.command(name="select")
    async def select(self, i: discord.Interaction, brawler: str):
        data = load()
        p = get_player(data, str(i.user.id))

        if brawler not in p["brawlers"]:
            return await i.response.send_message("❌ pas débloqué", ephemeral=True)

        p["selected"] = brawler
        save(data)

        await i.response.send_message(f"✅ {brawler} sélectionné", ephemeral=True)

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSAdvanced(bot))
