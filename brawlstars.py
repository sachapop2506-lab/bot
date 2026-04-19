import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "bs_clicker.json"

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
            "boxes": 3,
            "brawlers": {"Shelly": 0},  # power points
            "owned": ["Shelly"]
        }
    return data[uid]

# ---------- BRAWLERS ---------- #

BRAWLERS = {
    "Shelly": {"rarity": "Common"},
    "Nita": {"rarity": "Rare"},
    "Colt": {"rarity": "Rare"},
    "Bull": {"rarity": "Epic"},
    "Jessie": {"rarity": "Super Rare"},
    "Poco": {"rarity": "Epic"},
    "Spike": {"rarity": "Legendary"},
}

RARITY_DROP = {
    "Common": 60,
    "Rare": 25,
    "Super Rare": 10,
    "Epic": 4,
    "Legendary": 1
}

# ---------- BOX SYSTEM ---------- #

def roll_rarity():
    r = random.randint(1, 100)
    total = 0
    for rarity, chance in RARITY_DROP.items():
        total += chance
        if r <= total:
            return rarity

def get_random_brawler(rarity):
    return random.choice([
        b for b, v in BRAWLERS.items() if v["rarity"] == rarity
    ])

# ---------- VIEW ---------- #

class BoxView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, i):
        return i.user.id == self.user.id

    @discord.ui.button(label="🎁 Ouvrir une box", style=discord.ButtonStyle.primary)
    async def open_box(self, interaction: discord.Interaction, _):
        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await interaction.response.send_message(
                "❌ Tu n'as pas de box",
                ephemeral=True
            )

        p["boxes"] -= 1

        coins = random.randint(20, 80)
        p["coins"] += coins

        rarity = roll_rarity()
        brawler = get_random_brawler(rarity)

        msg = f"🎁 Box ouverte !\n🪙 +{coins} coins\n🎲 Rareté: {rarity}\n"

        if brawler not in p["owned"]:
            p["owned"].append(brawler)
            p["brawlers"][brawler] = 0
            msg += f"✨ Nouveau brawler: **{brawler}**"
        else:
            pp = random.randint(5, 20)
            p["brawlers"][brawler] += pp
            msg += f"⚡ {brawler} +{pp} power points"

        save(data)

        embed = discord.Embed(
            title="🎁 Résultat",
            description=msg,
            color=0x2ecc71
        )

        await interaction.response.edit_message(embed=embed, view=self)

# ---------- CLICKER ---------- #

class ClickView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, i):
        return i.user.id == self.user.id

    @discord.ui.button(label="👊 Click", style=discord.ButtonStyle.success)
    async def click(self, interaction: discord.Interaction, _):
        data = load()
        p = get_player(data, str(self.user.id))

        gain = random.randint(5, 15)
        p["coins"] += gain
        p["trophies"] += 1

        # chance de box
        if random.randint(1, 10) == 1:
            p["boxes"] += 1
            bonus = "\n🎁 Tu as gagné une box !"
        else:
            bonus = ""

        save(data)

        await interaction.response.edit_message(
            content=f"👊 +{gain} coins | 🏆 +1 trophée{bonus}",
            view=self
        )

# ---------- COG ---------- #

class BSSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="click")
    async def click(self, i: discord.Interaction):
        await i.response.send_message(
            "👊 Clique pour farmer !",
            view=ClickView(i.user)
        )

    @app_commands.command(name="box")
    async def box(self, i: discord.Interaction):
        await i.response.send_message(
            "🎁 Ouvre tes boxes",
            view=BoxView(i.user)
        )

    @app_commands.command(name="profil")
    async def profil(self, i: discord.Interaction):
        p = get_player(load(), str(i.user.id))

        brawlers = "\n".join([
            f"{b} ({p['brawlers'][b]} pp)"
            for b in p["owned"]
        ])

        await i.response.send_message(
            f"🏆 {p['trophies']} | 🪙 {p['coins']} | 🎁 {p['boxes']}\n\n🧑‍🚀 Brawlers:\n{brawlers}"
        )

    @app_commands.command(name="classement")
    async def classement(self, i: discord.Interaction):
        data = load()

        top = sorted(data.items(), key=lambda x: x[1]["trophies"], reverse=True)[:10]

        txt = "\n".join([
            f"<@{uid}> - {p['trophies']}🏆"
            for uid, p in top
        ])

        await i.response.send_message(f"🏆 Classement:\n{txt}")

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSSystem(bot))
