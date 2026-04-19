import discord
from discord.ext import commands
from discord import app_commands
import json, os, random, asyncio

FILE = "bs_game.json"

# ---------------- DATA ---------------- #

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
            "trophies": 0,
            "coins": 200,
            "brawlers": ["Shelly"],
            "selected": "Shelly",
            "skins": [],
            "equipped_skin": None
        }
    return data[uid]

# ---------------- BRAWLERS ---------------- #

BRAWLERS = {
    "Shelly": {"hp":100,"min":10,"max":20,"ulti":35,"rarity":"Common"},
    "Colt": {"hp":90,"min":12,"max":22,"ulti":30,"rarity":"Rare"},
    "Bull": {"hp":120,"min":8,"max":25,"ulti":40,"rarity":"Epic"},
    "Jessie": {"hp":95,"min":11,"max":18,"ulti":28,"rarity":"Rare"},
}

SHOP = {"Skin Rouge":100,"Skin Or":250,"Skin Galaxy":500}
queue = []

# ---------------- FIGHT ---------------- #

class FightView(discord.ui.View):
    def __init__(self, p1, p2, data, ai=False):
        super().__init__(timeout=60)
        self.p1, self.p2 = p1, p2
        self.ai = ai
        self.data = data

        d1, d2 = get_player(data,str(p1.id)), get_player(data,str(p2.id))
        self.b1, self.b2 = d1["selected"], d2["selected"]

        self.hp1 = BRAWLERS[self.b1]["hp"]
        self.hp2 = BRAWLERS[self.b2]["hp"]

        self.turn = p1.id
        self.log = []
        self.ulti_used = {p1.id:False,p2.id:False}

    def embed(self):
        return discord.Embed(
            title=f"⚔️ {self.b1} VS {self.b2}",
            description="\n".join(self.log[-4:]) or "Combat...",
            color=0x3498db
        ).add_field(
            name="❤️ PV",
            value=f"{self.p1.name}: {self.hp1}\n{self.p2.name}: {self.hp2}"
        )

    async def finish(self, i):
        d1,d2 = get_player(self.data,str(self.p1.id)),get_player(self.data,str(self.p2.id))

        if self.hp1 > self.hp2:
            d1["trophies"] += 20
            winner = self.p1
        else:
            d2["trophies"] += 20
            winner = self.p2

        reward = random.randint(20,80)
        get_player(self.data,str(winner.id))["coins"] += reward

        save(self.data)

        self.clear_items()
        await i.response.edit_message(
            embed=self.embed().add_field(name="🏆", value=f"{winner.name} gagne\n🎁 +{reward} coins"),
            view=self
        )

    async def interaction_check(self, i):
        return i.user.id == self.turn

    async def ai_play(self, msg):
        await asyncio.sleep(1)

        dmg = random.randint(10,25)
        self.hp1 -= dmg
        self.log.append(f"🤖 IA attaque {dmg}")
        self.turn = self.p1.id

        if self.hp1 <= 0:
            return await msg.edit(embed=self.embed())

        await msg.edit(embed=self.embed(), view=self)

    @discord.ui.button(label="⚔️ Attaque", style=discord.ButtonStyle.primary)
    async def attack(self, i, _):
        dmg = random.randint(10,25)

        if i.user == self.p1:
            self.hp2 -= dmg
            self.turn = self.p2.id
        else:
            self.hp1 -= dmg
            self.turn = self.p1.id

        self.log.append(f"{i.user.name} fait {dmg}")

        if self.hp1 <= 0 or self.hp2 <= 0:
            return await self.finish(i)

        await i.response.edit_message(embed=self.embed(), view=self)

        if self.ai and self.turn == self.p2.id:
            await self.ai_play(await i.original_response())

    @discord.ui.button(label="💥 Ulti", style=discord.ButtonStyle.danger)
    async def ulti(self, i, _):
        if self.ulti_used[i.user.id]:
            return await i.response.send_message("Déjà utilisé", ephemeral=True)

        self.ulti_used[i.user.id] = True
        dmg = random.randint(25,40)

        if i.user == self.p1:
            self.hp2 -= dmg
            self.turn = self.p2.id
        else:
            self.hp1 -= dmg
            self.turn = self.p1.id

        self.log.append(f"💥 {i.user.name} ulti {dmg}")

        if self.hp1 <= 0 or self.hp2 <= 0:
            return await self.finish(i)

        await i.response.edit_message(embed=self.embed(), view=self)

# ---------------- MENU ---------------- #

class MenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚔️ PvE", style=discord.ButtonStyle.primary)
    async def pve(self, i, _):
        view = FightView(i.user, i.client.user, load(), ai=True)
        await i.response.send_message(embed=view.embed(), view=view)

    @discord.ui.button(label="⚔️ PvP", style=discord.ButtonStyle.danger)
    async def pvp(self, i, _):
        queue.append(i.user)
        if len(queue) >= 2:
            p1,p2 = queue.pop(0),queue.pop(0)
            view = FightView(p1,p2,load())
            await i.channel.send(embed=view.embed(), view=view)
        else:
            await i.response.send_message("⏳ En attente...", ephemeral=True)

    @discord.ui.button(label="🛒 Shop", style=discord.ButtonStyle.secondary)
    async def shop(self, i, _):
        embed = discord.Embed(title="Shop")
        for k,v in SHOP.items():
            embed.add_field(name=k, value=f"{v} coins")
        await i.response.send_message(embed=embed, ephemeral=True)

# ---------------- COG ---------------- #

class BSGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bs_menu")
    async def menu(self, i: discord.Interaction):
        await i.response.send_message("🎮 Menu", view=MenuView())

    @app_commands.command(name="bs_profile")
    async def profile(self, i: discord.Interaction):
        p = get_player(load(), str(i.user.id))
        await i.response.send_message(
            f"🏆 {p['trophies']} | 🪙 {p['coins']} | 🎮 {p['selected']}"
        )

    @app_commands.command(name="bs_leaderboard")
    async def leaderboard(self, i: discord.Interaction):
        data = load()
        top = sorted(data.items(), key=lambda x:x[1]["trophies"], reverse=True)[:10]
        txt = "\n".join([f"<@{u}> {p['trophies']}" for u,p in top])
        await i.response.send_message(f"🏆\n{txt}")

# ---------------- SETUP ---------------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
