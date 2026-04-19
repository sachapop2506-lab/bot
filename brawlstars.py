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

# ---------------- FIGHT VIEW ---------------- #

class FightView(discord.ui.View):
    def __init__(self, user_id, player, enemy, ps, es, data):
        super().__init__(timeout=60)

        self.user_id = user_id
        self.player = player
        self.enemy = enemy

        self.hp_p = ps["hp"]
        self.hp_e = es["hp"]

        self.ps = ps
        self.es = es

        self.data = data
        self.log = []
        self.ulti_used = False

    def get_embed(self):
        embed = discord.Embed(
            title=f"⚔️ {self.player} VS {self.enemy}",
            description="\n".join(self.log[-5:]) or "Le combat commence !",
            color=0x3498db
        )

        embed.add_field(
            name="❤️ PV",
            value=f"Toi: {self.hp_p}\nEnnemi: {self.hp_e}"
        )

        return embed

    async def end(self, interaction):
        p = get_player(self.data, str(self.user_id))

        if self.hp_p > self.hp_e:
            gain = random.randint(10, 25)
            p["trophies"] += gain
            result = f"🏆 Victoire +{gain}"
            color = 0x2ecc71
        else:
            loss = random.randint(5, 15)
            p["trophies"] = max(0, p["trophies"] - loss)
            result = f"💀 Défaite -{loss}"
            color = 0xe74c3c

        save(self.data)

        embed = discord.Embed(
            title="🏁 Combat terminé",
            description="\n".join(self.log[-5:]),
            color=color
        )

        embed.add_field(name="Résultat", value=result)

        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="⚔️ Attaquer", style=discord.ButtonStyle.primary)
    async def attack(self, interaction: discord.Interaction, button):

        dmg_p = random.randint(self.ps["min"], self.ps["max"])
        dmg_e = random.randint(self.es["min"], self.es["max"])

        self.hp_e -= dmg_p
        self.hp_p -= dmg_e

        self.log.append(f"⚔️ Tu fais {dmg_p} | Ennemi fait {dmg_e}")

        if self.hp_p <= 0 or self.hp_e <= 0:
            return await self.end(interaction)

        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="💥 Ulti", style=discord.ButtonStyle.danger)
    async def ulti(self, interaction: discord.Interaction, button):

        if self.ulti_used:
            return await interaction.response.send_message("⛔ Ulti déjà utilisé", ephemeral=True)

        self.ulti_used = True

        dmg_p = random.randint(self.ps["max"], self.ps["max"] + 15)
        dmg_e = random.randint(self.es["min"], self.es["max"])

        self.hp_e -= dmg_p
        self.hp_p -= dmg_e

        self.log.append(f"💥 ULTI {dmg_p} dégâts | Ennemi {dmg_e}")

        if self.hp_p <= 0 or self.hp_e <= 0:
            return await self.end(interaction)

        await interaction.response.edit_message(embed=self.get_embed(), view=self)

# ---------------- COG ---------------- #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bs_profile")
    async def profile(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))
        save(data)

        embed = discord.Embed(title=f"👤 {i.user.name}", color=0xf1c40f)
        embed.add_field(name="🏆 Trophées", value=p["trophies"])
        embed.add_field(name="🪙 Pièces", value=p["coins"])
        embed.add_field(name="🎮 Brawler", value=p["selected"])
        embed.add_field(name="📦 Collection", value=", ".join(p["brawlers"]))

        await i.response.send_message(embed=embed)

    @app_commands.command(name="bs_open")
    async def open_box(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        reward = random.choices(["coins", "brawler"], weights=[70, 30])[0]

        if reward == "coins":
            amount = random.randint(20, 100)
            p["coins"] += amount
            msg = f"🪙 +{amount} pièces"
        else:
            new = random.choice(ALL_BRAWLERS)
            if new in p["brawlers"]:
                p["coins"] += 50
                msg = "🔁 Doublon → +50 pièces"
            else:
                p["brawlers"].append(new)
                msg = f"🎉 Nouveau brawler : {new}"

        save(data)
        await i.response.send_message(msg)

    @app_commands.command(name="bs_select")
    async def select(self, i: discord.Interaction, brawler: str):
        data = load()
        p = get_player(data, str(i.user.id))

        if brawler not in p["brawlers"]:
            return await i.response.send_message("❌ Tu ne l'as pas")

        p["selected"] = brawler
        save(data)

        await i.response.send_message(f"✅ {brawler} sélectionné")

    @app_commands.command(name="bs_fight")
    async def fight(self, i: discord.Interaction):
        data = load()
        p = get_player(data, str(i.user.id))

        player = p["selected"]
        enemy = random.choice(ALL_BRAWLERS)

        ps = BRAWLERS[player]
        es = BRAWLERS[enemy]

        view = FightView(i.user.id, player, enemy, ps, es, data)
        embed = view.get_embed()

        await i.response.send_message(embed=embed, view=view)

# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
