import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "/data/bs_game.json"
os.makedirs("/data", exist_ok=True)

# ---------- DATA ---------- #

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
            "boxes": 5,
            "selected": "Shelly",
            "brawlers": {"Shelly": {"level": 1}}
        }

    # FIX ancien système box
    if isinstance(data[uid]["boxes"], dict):
        data[uid]["boxes"] = sum(data[uid]["boxes"].values())

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
RARITY_MULTIPLIER = {
    "Common": 1,
    "Rare": 1.3,
    "Super Rare": 1.7,
    "Epic": 2.5,
    "Mythique": 4,
    "Légendaire": 7,
    "Ultra Légendaire": 9
    
}

RARITY_CHANCES = {
    "Common": 55,
    "Rare": 25,
    "Super Rare": 12,
    "Epic": 8,
    "Mythique": 3,
    "Légendaire": 0.9,
    "Ultra Légendaire": 0.1
}

# ---------- UTILS ---------- #

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
    return random.choice(pool)

def level_multiplier(level):
    return 1 + (level - 1) * 0.25

def progress_bar(value):
    size = 10
    filled = int(size * value / 11)
    return "█"*filled + "░"*(size-filled)

# ---------- ROLE SYSTEM ---------- #

def apply_role_bonus(role, gain, p):
    msg = ""

    if role == "Assassinat" and random.randint(1,5)==1:
        gain *= 2
        msg = "💥 Crit x2"

    if role == "Tank" and random.randint(1,20)==1:
        p["boxes"] += 1
        msg = "🎁 Box bonus"

    if role == "Soutien":
        bonus = int(gain*0.2)
        gain += bonus
        msg = f"💰 +{bonus}"

    return int(gain), msg

# ---------- EMBED ---------- #

def create_embed(p, extra=""):
    b = p["selected"]
    lvl = p["brawlers"][b]["level"]
    info = BRAWLERS[b]

    embed = discord.Embed(
        title=f"🔥 {b} • Niveau {lvl}",
        description=f"{info['rarity']} • {info['role']}",
        color=0x9b59b6
    )

    embed.add_field(
        name="📊 Progression",
        value=f"`{progress_bar(lvl)}`\n{lvl}/11",
        inline=False
    )

    embed.add_field(
        name="💰 Compte",
        value=f"🪙 {p['coins']}\n🏆 {p['trophies']}",
        inline=True
    )

    embed.add_field(
        name="🎁 Boxes",
        value=f"{p['boxes']}",
        inline=True
    )

    if extra:
        embed.add_field(name="⚡ Action", value=extra, inline=False)

    return embed

# ---------- UI ---------- #

class MainView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    async def interaction_check(self, i):
        return i.user.id == self.user.id

    @discord.ui.button(label="Click", emoji="👊", style=discord.ButtonStyle.primary)
    async def click(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]
        rarity = BRAWLERS[b]["rarity"]
        role = BRAWLERS[b]["role"]

        gain = int(random.randint(5,10)*level_multiplier(lvl)*RARITY_MULTIPLIER[rarity])
        gain, msg = apply_role_bonus(role, gain, p)

        # 🎁 DROP BOX FIX
        drop = ""
        if random.random() < 0.15:
            p["boxes"] += 1
            drop = "🎁 Box gagnée !"

        p["coins"] += gain
        p["trophies"] += 1
        save(data)

        txt = f"+{gain} coins"
        if msg: txt += f"\n{msg}"
        if drop: txt += f"\n{drop}"

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, txt),
            view=MainView(self.user)
        )

    @discord.ui.button(label="Box", emoji="🎁", style=discord.ButtonStyle.success)
    async def box(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.followup.send("Pas de box", ephemeral=True)

        p["boxes"] -= 1

        rewards = []

        coins = random.randint(50,150)
        p["coins"] += coins
        rewards.append(f"🪙 +{coins}")

        if random.random() < 0.4:
            rarity = roll_rarity()
            brawler = random_brawler(rarity)

            if brawler not in p["brawlers"]:
                p["brawlers"][brawler] = {"level":1}
                rewards.append(f"✨ Nouveau {brawler} ({rarity})")
            else:
                bonus = random.randint(30,80)
                p["coins"] += bonus
                rewards.append(f"💰 Doublon +{bonus}")

        save(data)

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, "\n".join(rewards)),
            view=MainView(self.user)
        )

# ---------- COG ---------- #

class BSGame(commands.GroupCog, name="bs"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data = load()
        p = get_player(data, str(interaction.user.id))

        await interaction.followup.send(
            embed=create_embed(p),
            view=MainView(interaction.user),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(BSGame(bot))
