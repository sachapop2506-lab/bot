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

    # ---------------- PROFILE ---------------- #

    @app_commands.command(name="bs_profile")
    async def profile(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))
        save(data)

        embed = discord.Embed(title=f"👤 Profil de {i.user.name}", color=0xf1c40f)
        embed.add_field(name="🏆 Trophées", value=p["trophies"])
        embed.add_field(name="🪙 Pièces", value=p["coins"])
        embed.add_field(name="🎮 Brawler", value=p["selected"])
        embed.add_field(name="📦 Collection", value=", ".join(p["brawlers"]))

        await i.response.send_message(embed=embed)

    # ---------------- OPEN BOX ---------------- #

    @app_commands.command(name="bs_open")
    async def open_box(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        reward_type = random.choices(
            ["coins", "brawler"],
            weights=[70, 30]
        )[0]

        if reward_type == "coins":
            amount = random.randint(20, 100)
            p["coins"] += amount
            msg = f"🪙 Tu gagnes {amount} pièces !"

        else:
            new = random.choice(ALL_BRAWLERS)
            if new in p["brawlers"]:
                amount = 50
                p["coins"] += amount
                msg = f"🔁 Doublon → {amount} pièces"
            else:
                p["brawlers"].append(new)
                msg = f"🎉 Nouveau brawler débloqué : **{new}** !"

        save(data)
        await i.response.send_message(msg)

    # ---------------- SELECT ---------------- #

    @app_commands.command(name="bs_select")
    async def select(self, i: discord.Interaction, brawler: str):
        data = load()
        p = get_player(data, str(i.user.id))

        if brawler not in p["brawlers"]:
            return await i.response.send_message("❌ Tu ne possèdes pas ce brawler")

        p["selected"] = brawler
        save(data)

        await i.response.send_message(f"✅ {brawler} sélectionné")

    # ---------------- FIGHT ---------------- #

    @app_commands.command(name="bs_fight")
    async def fight(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        player_brawler = p["selected"]
        enemy_brawler = random.choice(ALL_BRAWLERS)

        p_stats = BRAWLERS[player_brawler]
        e_stats = BRAWLERS[enemy_brawler]

        hp_p = p_stats["hp"]
        hp_e = e_stats["hp"]

        log = ""

        while hp_p > 0 and hp_e > 0:
            dmg_p = random.randint(p_stats["min"], p_stats["max"])
            dmg_e = random.randint(e_stats["min"], e_stats["max"])

            hp_e -= dmg_p
            hp_p -= dmg_e

            log += f"💥 Tu fais {dmg_p} | Ennemi fait {dmg_e}\n"

        if hp_p > 0:
            gain = random.randint(10, 25)
            p["trophies"] += gain
            result = f"🏆 Victoire ! +{gain} trophées"
        else:
            loss = random.randint(5, 15)
            p["trophies"] = max(0, p["trophies"] - loss)
            result = f"💀 Défaite ! -{loss} trophées"

        save(data)

               embed = discord.Embed(title="⚔️ Combat", description=log[:1000], color=0xe74c3c)
        embed.add_field(name="Résultat", value=result)

        await i.response.send_message(embed=embed)


# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
