import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "bs_game.json"

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
                "Shelly": {"level":1}
            }
        }
    return data[uid]

# ---------- CONFIG ---------- #

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

def progress_bar(value, max_value=11, size=10):
    filled = int(size * value / max_value)
    return "🟩" * filled + "⬛" * (size - filled)

def roll_rarity():
    r = random.randint(1, 100)
    total = 0
    for rarity, chance in RARITY.items():
        total += chance
        if r <= total:
            return rarity

def random_brawler(rarity):
    return random.choice([b for b,v in BRAWLERS.items() if v["rarity"] == rarity])

# ---------- EMBED UI ---------- #

def create_embed(p, extra=""):
    b = p["selected"]
    lvl = p["brawlers"][b]["level"]

    multi = get_multiplier(p["trophies"])
    cost = int(100 * (1.5 ** (lvl - 1)))

    embed = discord.Embed(
        title="🎮 BRAWL STARS BOT",
        description=f"🎯 **{b}** (lvl {lvl})\n{extra}",
        color=0xf1c40f
    )

    embed.add_field(
        name="🏆 Progression",
        value=f"🏆 {p['trophies']}\n💰 x{multi:.1f}",
        inline=True
    )

    embed.add_field(
        name="💰 Ressources",
        value=f"🪙 {p['coins']}\n🎁 {p['boxes']}",
        inline=True
    )

    embed.add_field(
        name="📈 Niveau",
        value=f"{progress_bar(lvl)} (lvl {lvl}/11)",
        inline=False
    )

    embed.add_field(
        name="⬆️ Upgrade",
        value=f"{cost} coins",
        inline=False
    )

    return embed

# ---------- BOX ---------- #

def open_box(p):
    rewards = []

    coins = random.randint(30, 100)
    p["coins"] += coins
    rewards.append(f"🪙 {coins} coins")

    rarity = roll_rarity()
    brawler = random_brawler(rarity)

    if brawler not in p["brawlers"]:
        p["brawlers"][brawler] = {"level":1}
        rewards.append(f"✨ Nouveau {brawler} ({rarity})")
    else:
        bonus = random.randint(20, 60)
        p["coins"] += bonus
        rewards.append(f"💰 +{bonus} coins (doublon)")

    return rewards

# ---------- SELECT ---------- #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
            discord.SelectOption(label=b, description=f"lvl {player['brawlers'][b]['level']}")
            for b in player["brawlers"]
        ]
        super().__init__(placeholder="Choisir un brawler", options=options)

    async def callback(self, interaction: discord.Interaction):
        data = load()
        p = get_player(data, str(interaction.user.id))

        p["selected"] = self.values[0]
        save(data)

        view = MainView(interaction.user)
        view.add_item(BrawlerSelect(p))

        await interaction.response.edit_message(
            embed=create_embed(p, f"\n✅ {self.values[0]} sélectionné"),
            view=view
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

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.response.edit_message(
            embed=create_embed(p, f"\n👊 +{gain} coins{bonus}"),
            view=view
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

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.response.edit_message(
            embed=create_embed(p, "\n" + "\n".join(rewards)),
            view=view
        )

    @discord.ui.button(label="⬆️ Upgrade", style=discord.ButtonStyle.secondary)
    async def upgrade(self, i, _):
        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]

        cost = int(100 * (1.5 ** (lvl - 1)))

        if p["coins"] < cost:
            return await i.response.send_message(
                f"❌ Pas assez de coins ({cost})",
                ephemeral=True
            )

        p["coins"] -= cost
        p["brawlers"][b]["level"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.response.edit_message(
            embed=create_embed(p, f"\n⬆️ {b} level {p['brawlers'][b]['level']}"),
            view=view
        )

# ---------- COG ---------- #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bs")
    async def bs(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        view = MainView(i.user)
        view.add_item(BrawlerSelect(p))

        await i.response.send_message(
            embed=create_embed(p),
            view=view,
            ephemeral=True
        )

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
    await bot.add_cog(BSGame(bot))
