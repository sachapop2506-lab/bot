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
    # -------- COMMON --------
    "Shelly": {"rarity": "Common", "role": "Dégâts bruts"},

    # -------- RARE --------
    "Bartaba": {"rarity": "Rare", "role": "Artillerie"},
    "Brock": {"rarity": "Rare", "role": "Tir d'élite"},
    "Bull": {"rarity": "Rare", "role": "Tank"},
    "Colt": {"rarity": "Rare", "role": "Dégâts bruts"},
    "El Costo": {"rarity": "Rare", "role": "Tank"},
    "Nita": {"rarity": "Rare", "role": "Dégâts bruts"},
    "Poco": {"rarity": "Rare", "role": "Soutien"},
    "Rosa": {"rarity": "Rare", "role": "Tank"},

    # -------- SUPER RARE --------
    "A.R.K.A.D.": {"rarity": "Super Rare", "role": "Dégâts bruts"},
    "Carl": {"rarity": "Super Rare", "role": "Dégâts bruts"},
    "Darryl": {"rarity": "Super Rare", "role": "Tank"},
    "Dynamike": {"rarity": "Super Rare", "role": "Artillerie"},
    "Gus": {"rarity": "Super Rare", "role": "Soutien"},
    "Jacky": {"rarity": "Super Rare", "role": "Tank"},
    "Jessie": {"rarity": "Super Rare", "role": "Contrôle"},
    "Penny": {"rarity": "Super Rare", "role": "Contrôle"},
    "Ricochet": {"rarity": "Super Rare", "role": "Dégâts bruts"},
    "Tick": {"rarity": "Super Rare", "role": "Artillerie"},

    # -------- EPIC --------
    "Angelo": {"rarity": "Epic", "role": "Tir d'élite"},
    "Ash": {"rarity": "Epic", "role": "Tank"},
    "Béa": {"rarity": "Epic", "role": "Tir d'élite"},
    "Berry": {"rarity": "Epic", "role": "Artillerie"},
    "Billie": {"rarity": "Epic", "role": "Tank"},
    "Bo": {"rarity": "Epic", "role": "Contrôle"},
    "Bonnie": {"rarity": "Epic", "role": "Tir d'élite"},
    "Colette": {"rarity": "Epic", "role": "Dégâts bruts"},
    "Edgar": {"rarity": "Epic", "role": "Assassinat"},
    "Eliz@": {"rarity": "Epic", "role": "Contrôle"},
    "Frank": {"rarity": "Epic", "role": "Tank"},
    "Gaël": {"rarity": "Epic", "role": "Contrôle"},
    "Griff": {"rarity": "Epic", "role": "Contrôle"},
    "Grom": {"rarity": "Epic", "role": "Artillerie"},
    "Hank": {"rarity": "Epic", "role": "Tank"},
    "Larry & Lawrie": {"rarity": "Epic", "role": "Artillerie"},
    "Lola": {"rarity": "Epic", "role": "Dégâts bruts"},
    "Maisie": {"rarity": "Epic", "role": "Tir d'élite"},
    "Mandy": {"rarity": "Epic", "role": "Tir d'élite"},
    "Meeple": {"rarity": "Epic", "role": "Soutien"},
    "Nani": {"rarity": "Epic", "role": "Tir d'élite"},
    "Pam": {"rarity": "Epic", "role": "Soutien"},
    "Pearl": {"rarity": "Epic", "role": "Dégâts bruts"},
    "Polly": {"rarity": "Epic", "role": "Tir d'élite"},
    "Sam": {"rarity": "Epic", "role": "Assassinat"},
    "Shade": {"rarity": "Epic", "role": "Assassinat"},
    "Stu": {"rarity": "Epic", "role": "Assassinat"},
    "Trunk": {"rarity": "Epic", "role": "Tank"},

    # -------- MYTHIC --------
    "Alli": {"rarity": "Mythique", "role": "Soutien"},
    "Buster": {"rarity": "Mythique", "role": "Tank"},
    "Buzz": {"rarity": "Mythique", "role": "Assassinat"},
    "Byron": {"rarity": "Mythique", "role": "Soutien"},
    "Charlie": {"rarity": "Mythique", "role": "Contrôle"},
    "Chuck": {"rarity": "Mythique", "role": "Contrôle"},
    "Clancy": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "D'jinn": {"rarity": "Mythique", "role": "Contrôle"},
    "Doug": {"rarity": "Mythique", "role": "Soutien"},
    "Eve": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Fang": {"rarity": "Mythique", "role": "Assassinat"},
    "Finx": {"rarity": "Mythique", "role": "Contrôle"},
    "Gigi": {"rarity": "Mythique", "role": "Assassinat"},
    "Glowy": {"rarity": "Mythique", "role": "Soutien"},
    "Gray": {"rarity": "Mythique", "role": "Contrôle"},
    "Jae-Yong": {"rarity": "Mythique", "role": "Soutien"},
    "Janet": {"rarity": "Mythique", "role": "Tir d'élite"},
    "Juju": {"rarity": "Mythique", "role": "Artillerie"},
    "Lily": {"rarity": "Mythique", "role": "Assassinat"},
    "Lou": {"rarity": "Mythique", "role": "Contrôle"},
    "Lumi": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Max": {"rarity": "Mythique", "role": "Soutien"},
    "Médor": {"rarity": "Mythique", "role": "Soutien"},
    "Melody": {"rarity": "Mythique", "role": "Assassinat"},
    "Mico": {"rarity": "Mythique", "role": "Assassinat"},
    "Mina": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Moe": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Monsieur M.": {"rarity": "Mythique", "role": "Contrôle"},
    "Mortis": {"rarity": "Mythique", "role": "Assassinat"},
    "Najia": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Ollie": {"rarity": "Mythique", "role": "Tank"},
    "Otis": {"rarity": "Mythique", "role": "Contrôle"},
    "R-T": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Squeak": {"rarity": "Mythique", "role": "Contrôle"},
    "Tara": {"rarity": "Mythique", "role": "Dégâts bruts"},
    "Wally": {"rarity": "Mythique", "role": "Artillerie"},
    "Willow": {"rarity": "Mythique", "role": "Contrôle"},
    "Ziggy": {"rarity": "Mythique", "role": "Contrôle"},

    # -------- LEGENDARY --------
    "Ambre": {"rarity": "Légendaire", "role": "Contrôle"},
    "Chester": {"rarity": "Légendaire", "role": "Dégâts bruts"},
    "Corbac": {"rarity": "Légendaire", "role": "Assassinat"},
    "Cordelius": {"rarity": "Légendaire", "role": "Assassinat"},
    "Draco": {"rarity": "Légendaire", "role": "Tank"},
    "Émeri": {"rarity": "Légendaire", "role": "Contrôle"},
    "Kenji": {"rarity": "Légendaire", "role": "Assassinat"},
    "Kit": {"rarity": "Légendaire", "role": "Soutien"},
    "Léon": {"rarity": "Légendaire", "role": "Assassinat"},
    "Meg": {"rarity": "Légendaire", "role": "Tank"},
    "Pierce": {"rarity": "Légendaire", "role": "Tir d'élite"},
    "Spike": {"rarity": "Légendaire", "role": "Dégâts bruts"},
    "Surge": {"rarity": "Légendaire", "role": "Dégâts bruts"},

    # -------- ULTRA LEGENDARY --------
    "Kaze": {"rarity": "Ultra Légendaire", "role": "Assassinat"},
    "Sirius": {"rarity": "Ultra Légendaire", "role": "Contrôle"},
}

RARITY = {
    "Common": 60,
    "Rare": 25,
    "Super Rare": 10,
    "Epic": 4,
    "Legendary": 0.9,
    "Ultra Légendaire": 0.1
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
