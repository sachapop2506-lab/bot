import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "/data/bs_game.json"
os.makedirs("/data", exist_ok=True)

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
            "brawlers": {"Shelly": {"level": 1}}
        }
    return data[uid]

# ---------- CONFIG ---------- #

BRAWLERS = {
    "Shelly": {"rarity": "Common", "role": "Dégâts bruts"},
    "Colt": {"rarity": "Rare", "role": "Dégâts bruts"},
    "Bull": {"rarity": "Rare", "role": "Tank"},
    "Brock": {"rarity": "Rare", "role": "Tir d'élite"},
    "Nita": {"rarity": "Rare", "role": "Dégâts bruts"},
    "Poco": {"rarity": "Rare", "role": "Soutien"},
    "Jessie": {"rarity": "Super Rare", "role": "Contrôle"},
    "Dynamike": {"rarity": "Super Rare", "role": "Artillerie"},
    "Tick": {"rarity": "Super Rare", "role": "Artillerie"},
    "Bo": {"rarity": "Epic", "role": "Contrôle"},
    "Edgar": {"rarity": "Epic", "role": "Assassinat"},
    "Pam": {"rarity": "Epic", "role": "Soutien"},
    "Frank": {"rarity": "Epic", "role": "Tank"},
    "Mortis": {"rarity": "Mythique", "role": "Assassinat"},
    "Max": {"rarity": "Mythique", "role": "Soutien"},
    "Spike": {"rarity": "Légendaire", "role": "Dégâts bruts"},
    "Leon": {"rarity": "Légendaire", "role": "Assassinat"},
}

RARITY = {
    "Common": 55,
    "Rare": 25,
    "Super Rare": 12,
    "Epic": 5,
    "Mythique": 2,
    "Légendaire": 1
}

RARITY_MULTIPLIER = {
    "Common": 1.0,
    "Rare": 1.2,
    "Super Rare": 1.5,
    "Epic": 2.0,
    "Mythique": 3.0,
    "Légendaire": 5.0
}

# ---------- UTILS ---------- #

def get_multiplier(trophies):
    return 1 + (trophies // 100) * 0.2

def progress_bar(value, max_value=11, size=10):
    filled = int(size * value / max_value)
    return "🟩" * filled + "⬛" * (size - filled)

def roll_rarity():
    r = random.random() * 100
    total = 0
    for rarity, chance in RARITY.items():
        total += chance
        if r <= total:
            return rarity
    return "Common"

def random_brawler(rarity):
    pool = [b for b,v in BRAWLERS.items() if v["rarity"] == rarity]
    return random.choice(pool if pool else list(BRAWLERS.keys()))

# ---------- EMBED ---------- #

def create_embed(p, extra=""):
    b = p["selected"]
    lvl = p["brawlers"][b]["level"]

    embed = discord.Embed(
        title="🎮 BRAWL STARS BOT",
        description=f"🎯 **{b}** (lvl {lvl})\n⭐ {BRAWLERS[b]['rarity']} | 🎭 {BRAWLERS[b]['role']}\n{extra}",
        color=0xf1c40f
    )

    embed.add_field(name="🏆 Trophées", value=p["trophies"])
    embed.add_field(name="💰 Coins", value=p["coins"])
    embed.add_field(name="🎁 Boxes", value=p["boxes"], inline=False)

    embed.add_field(
        name="📈 Niveau",
        value=f"{progress_bar(lvl)} (lvl {lvl}/11)",
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
        rewards.append(f"💰 +{bonus} coins")

    return rewards

# ---------- UI ---------- #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
    discord.SelectOption(
        label=str(b)[:100],
        description=f"lvl {player['brawlers'][b]['level']}"[:100]
    )
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

        await interaction.response.edit_message(
            embed=create_embed(p, f"\n✅ {self.values[0]} sélectionné"),
            view=view
        )

class MainView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.user.id:
            await i.response.send_message("❌ Pas pour toi", ephemeral=True)
            return False

        if not i.response.is_done():
            await i.response.defer()

        return True

    @discord.ui.button(label="👊 Click", style=discord.ButtonStyle.primary)
    async def click(self, i: discord.Interaction, _):
        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        rarity = BRAWLERS[b]["rarity"]
        role = BRAWLERS[b]["role"]

        multi = get_multiplier(p["trophies"])
        rarity_multi = RARITY_MULTIPLIER.get(rarity, 1)

        gain = int(random.randint(5, 15) * multi * rarity_multi)
        bonus = ""

        if role == "Assassinat" and random.randint(1, 5) == 1:
            gain *= 2
            bonus += "\n💥 Crit x2"

        if role == "Soutien":
            extra = int(gain * 0.2)
            gain += extra
            bonus += f"\n💰 +{extra}"

        if role == "Tank" and random.randint(1, 25) == 1:
            p["boxes"] += 1
            bonus += "\n🎁 Bonus box (tank)"

        if random.randint(1, 50) == 1:
            p["boxes"] += 1
            bonus += "\n🎁 Box (rare)"

        p["coins"] += gain
        p["trophies"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"\n👊 +{gain} coins{bonus}"),
            view=view
        )

    @discord.ui.button(label="🎁 Box", style=discord.ButtonStyle.success)
    async def box(self, i: discord.Interaction, _):
        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.followup.send("❌ Pas de box", ephemeral=True)

        p["boxes"] -= 1
        rewards = open_box(p)
        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, "\n" + "\n".join(rewards)),
            view=view
        )

    @discord.ui.button(label="⬆️ Upgrade", style=discord.ButtonStyle.secondary)
    async def upgrade(self, i: discord.Interaction, _):
        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]

        if lvl >= 11:
            return await i.followup.send("❌ Niveau max atteint", ephemeral=True)

        rarity = BRAWLERS[b]["rarity"]
        rarity_multi = RARITY_MULTIPLIER.get(rarity, 1)

        base_cost = 100 * rarity_multi
        cost = int(base_cost * (2 ** (lvl - 1)))

        if p["coins"] < cost:
            return await i.followup.send(f"❌ Pas assez de coins ({cost})", ephemeral=True)

        p["coins"] -= cost
        p["brawlers"][b]["level"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"\n⬆️ {b} level {p['brawlers'][b]['level']} (-{cost} coins)"),
            view=view
        )

# ---------- COG ---------- #

@app_commands.command(name="bs")
async def bs(self, i: discord.Interaction):
    try:
        await i.response.defer(ephemeral=True)

        data = load()
        print("1 OK")

        p = get_player(data, str(i.user.id))
        print("2 OK")

        embed = create_embed(p)
        print("3 OK")

        view = MainView(i.user)
        print("4 OK")

        view.add_item(BrawlerSelect(p))
        print("5 OK")

        await i.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
        print("6 OK")

    except Exception as e:
        print("ERREUR BS :", e)
        await i.followup.send(f"❌ {e}", ephemeral=True)

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
