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

    return embed

# ---------- BOX ---------- #

def open_box(p):
    rewards = []

    coins = random.randint(30, 100)
    p["coins"] += coins
    rewards.append(f"🪙 {coins} coins")

    return rewards

# ---------- UI ---------- #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
            discord.SelectOption(label=str(b), description=f"lvl {player['brawlers'][b]['level']}")
            for b in player["brawlers"]
        ][:25]

        super().__init__(placeholder="Choisir un brawler", options=options)

    async def callback(self, interaction):
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

    async def interaction_check(self, i):
        if i.user.id != self.user.id:
            await i.response.send_message("❌ Pas pour toi", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👊 Click", style=discord.ButtonStyle.primary)
    async def click(self, i, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        gain = random.randint(5, 15)
        p["coins"] += gain
        p["trophies"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"\n👊 +{gain} coins"),
            view=view
        )

# ---------- COG ---------- #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
@app_commands.command(name="bs")
async def bs(self, i):
    try:
        await i.response.defer(ephemeral=True)

        data = load()
        print("LOAD OK")

        p = get_player(data, str(i.user.id))
        print("PLAYER OK")

        embed = create_embed(p)
        print("EMBED OK")

        view = MainView(i.user)
        print("VIEW OK")

        view.add_item(BrawlerSelect(p))
        print("SELECT OK")

        await i.followup.send(
            embed=embed,
            view=view,
            ephemeral=True
        )
        print("SEND OK")

    except Exception as e:
        print("ERREUR BS :", e)
        await i.followup.send(f"❌ {e}", ephemeral=True)
# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
