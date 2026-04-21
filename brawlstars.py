import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "/data/bs_game.json"
os.makedirs("/data", exist_ok=True)

# ================= DATA ================= #

def load():
    try:
        if os.path.exists(FILE):
            with open(FILE) as f:
                return json.load(f)
    except:
        pass
    return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_player(data, uid):
    if uid not in data:
        data[uid] = {
            "coins": 0,
            "trophies": 0,
            "boxes": {"normal": 5, "big": 0, "mega": 0},
            "selected": "Shelly",
            "brawlers": {"Shelly": {"level": 1}}
        }

    # compat ancien format
    if isinstance(data[uid].get("boxes"), int):
        data[uid]["boxes"] = {
            "normal": data[uid]["boxes"],
            "big": 0,
            "mega": 0
        }

    return data[uid]

# ================= CONFIG ================= #

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

RARITY_CHANCES = {
    "Common": 55,
    "Rare": 25,
    "Super Rare": 12,
    "Epic": 5,
    "Mythique": 2,
    "Légendaire": 0.9,
    "Ultra Légendaire": 0.1
}

RARITY_MULTIPLIER = {
    "Common": 1,
    "Rare": 1.3,
    "Super Rare": 1.7,
    "Epic": 2.5,
    "Mythique": 4,
    "Légendaire": 7,
    "Ultra Légendaire": 9
}

# ================= UTILS ================= #

def roll_rarity():
    r = random.random() * 100
    total = 0
    for rarity, chance in RARITY_CHANCES.items():
        total += chance
        if r <= total:
            return rarity
    return "Common"

def random_brawler(rarity):
    pool = [b for b,v in BRAWLERS.items() if v["rarity"] == rarity]
    return random.choice(pool if pool else list(BRAWLERS.keys()))

# ================= EMBED ================= #

def create_embed(p, extra=""):
    b = p["selected"]
    lvl = p["brawlers"][b]["level"]
    info = BRAWLERS.get(b, {"rarity": "?", "role": "?"})

    # couleur selon rareté
    rarity_colors = {
        "Common": 0x95a5a6,
        "Rare": 0x3498db,
        "Super Rare": 0x2ecc71,
        "Epic": 0x9b59b6,
        "Mythique": 0xe67e22,
        "Légendaire": 0xf1c40f,
        "Ultra Légendaire": 0xe74c3c
    }

    color = rarity_colors.get(info["rarity"], 0xf1c40f)

    embed = discord.Embed(
        title=f"🎮 {b} | Niveau {lvl}",
        description=f"Rareté: {info['rarity']}\nRôle: {info['role']}",
        color=color
    )

    embed.add_field(
        name="Progression",
        value=f"Niveau: {lvl}/11",
        inline=True
    )

    embed.add_field(
        name="Ressources",
        value=f"Coins: {p['coins']}\nBoxes: {p['boxes']}",
        inline=True
    )

    embed.add_field(
        name="Stats",
        value=f"Trophées: {p['trophies']}",
        inline=False
    )

    if extra:
        embed.add_field(name="Action", value=extra, inline=False)

    embed.set_footer(text="Brawl Stars Discord Game")
    return embed

# ================= UI ================= #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
            discord.SelectOption(label=b, description=f"lvl {player['brawlers'][b]['level']}")
            for b in player["brawlers"]
        ][:25]

        super().__init__(placeholder="Choisir un brawler", options=options)

    async def callback(self, interaction: discord.Interaction):
        data = load()
        p = get_player(data, str(interaction.user.id))

        p["selected"] = self.values[0]
        save(data)

        view = MainView(interaction.user)
        view.add_item(BrawlerSelect(p))

        await interaction.response.edit_message(embed=create_embed(p), view=view)

# ================= VIEW ================= #

class MainView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    async def interaction_check(self, i):
        if i.user.id != self.user.id:
            await i.response.send_message("Pas pour toi", ephemeral=True)
            return False
        return True

    # CLICK
    @discord.ui.button(label="Click", style=discord.ButtonStyle.primary)
    async def click(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        gain = random.randint(5, 15)
        p["coins"] += gain
        p["trophies"] += 1

        # 🎁 DROP BOX stylé
        drop_msg = ""
        chance = random.randint(1, 100)

        if chance <= 3:
            p["boxes"] += 1
            drop_msg = "\nMega Box drop"
        elif chance <= 10:
            p["boxes"] += 1
            drop_msg = "\nBig Box drop"
        elif chance <= 25:
            p["boxes"] += 1
            drop_msg = "\nBox drop"

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"+{gain} coins{drop_msg}"),
            view=view
        )

    # BOX
    @discord.ui.button(label="Ouvrir Box", style=discord.ButtonStyle.success)
    async def box(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.followup.send("Pas de box", ephemeral=True)

        p["boxes"] -= 1

        coins = random.randint(30, 120)
        p["coins"] += coins

        rarity = roll_rarity()
        brawler = random_brawler(rarity)

        if brawler not in p["brawlers"]:
            p["brawlers"][brawler] = {"level": 1}
            result = f"Nouveau: {brawler} ({rarity})"
        else:
            bonus = random.randint(20, 60)
            p["coins"] += bonus
            result = f"Doublon → +{bonus} coins"

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"+{coins} coins\n{result}"),
            view=view
        )

    # UPGRADE
    @discord.ui.button(label="Upgrade", style=discord.ButtonStyle.secondary)
    async def upgrade(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]

        if lvl >= 11:
            return await i.followup.send("Niveau max", ephemeral=True)

        rarity = BRAWLERS[b]["rarity"]
        multiplier = RARITY_MULTIPLIER.get(rarity, 1)

        cost = int(100 * multiplier * (2 ** (lvl - 1)))

        if p["coins"] < cost:
            return await i.followup.send(f"Pas assez de coins ({cost})", ephemeral=True)

        p["coins"] -= cost
        p["brawlers"][b]["level"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"Upgrade réussi (-{cost})"),
            view=view
        )

# ================= LEADERBOARD ================= #

class LeaderboardView(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.mode = "trophies"

    def build(self):
        data = load()
        key = self.mode

        players = [(uid, p.get(key, 0)) for uid, p in data.items()]
        players.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title=f"Leaderboard {key}", color=0xf1c40f)

        desc = ""
        for i, (uid, val) in enumerate(players[:10], 1):
            user = self.bot.get_user(int(uid))
            name = user.name if user else uid
            desc += f"{i}. {name} - {val}\n"

        embed.description = desc
        return embed

    @discord.ui.button(label="Trophées")
    async def t(self, i: discord.Interaction, _):
        self.mode = "trophies"
        await i.response.edit_message(embed=self.build(), view=self)

    @discord.ui.button(label="Coins")
    async def c(self, i: discord.Interaction, _):
        self.mode = "coins"
        await i.response.edit_message(embed=self.build(), view=self)

# ================= COMMAND ================= #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    bs = app_commands.Group(name="bs", description="jeu")

    @bs.command(name="play")
    async def play(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)

        data = load()
        p = get_player(data, str(i.user.id))

        view = MainView(i.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.send(embed=create_embed(p), view=view, ephemeral=True)

    @bs.command(name="leaderboard")
    async def leaderboard(self, i: discord.Interaction):
        view = LeaderboardView(self.bot)
        await i.response.send_message(embed=view.build(), view=view)

# ================= SETUP ================= #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
