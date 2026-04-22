import discord
from discord.ext import commands
from discord import app_commands
import json, os, random

FILE = "/data/bs_game.json"
os.makedirs("/data", exist_ok=True)

# ---------- DATA ---------- #
def get_daily_brawler():
    return random.choice(list(BRAWLERS.keys()))

def check_daily_shop(data):
    import time
    now = int(time.time())

    if "shop" not in data:
        data["shop"] = {}

    if "reset_time" not in data["shop"] or now >= data["shop"]["reset_time"]:
        data["shop"]["daily_brawler"] = get_daily_brawler()
        data["shop"]["reset_time"] = now + 86400  # reset dans 24h
        
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
            "brawlers": {"Shelly": {"level": 1}},
            "last_box_buy": 0  # ✅ AJOUT
        }

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
    "Common": 1.0,
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
    "Epic": 5,
    "Mythique": 2,
    "Légendaire": 0.9,
    "Ultra Légendaire": 0.1
}

BRAWLER_PRICES = {
    "Common": 1000,
    "Rare": 1600,
    "Super Rare": 2400,
    "Epic": 4000,
    "Mythique": 8000,
    "Légendaire": 16000,
    "Ultra Légendaire": 30000
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
    return random.choice(pool if pool else list(BRAWLERS.keys()))

def level_multiplier(level):
    return 1 + (level - 1) * 0.25

def progress_bar(value, max_value=11, size=10):
    filled = int(size * value / max_value)
    return "█" * filled + "░" * (size - filled)

# ---------- ROLE ---------- #

def apply_role_bonus(role, gain, p):
    msg = ""

    if role == "Assassinat" and random.randint(1, 5) == 1:
        gain *= 2
        msg = "💥 Crit x2"

    elif role == "Tank":
        gain = int(gain * 0.9)
        if random.randint(1, 40) == 1:
            p["boxes"] += 1
            msg = "🎁 Box bonus"

    elif role == "Soutien":
        extra = int(gain * 0.2)
        gain += extra
        msg = f"💰 +{extra}"

    elif role == "Tir d'élite":
        gain = int(gain * 1.3)

    elif role == "Artillerie" and random.randint(1, 7) == 1:
        gain = int(gain * 1.5)
        msg = "💥 Explosion"

    elif role == "Contrôle" and random.randint(1, 10) == 1:
        p["trophies"] += 2
        msg = "🏆 Bonus trophées"

    elif role == "Dégâts bruts":
        gain = int(gain * 1.2)

    return gain, msg
    
    # ---------- QUESTS / SHOP ---------- #

SHOP = {
    "box": {"price": 1000}
}

def get_daily():
    return {
        "click": random.randint(20, 50),
        "reward": random.randint(100, 300),
        "done": 0
    }

def check_reset_daily(p):
    import time
    now = int(time.time())

    if "daily_time" not in p or now - p["daily_time"] > 86400:
        p["daily"] = get_daily()
        p["daily_time"] = now

# ---------- EMBED ---------- #

def create_embed(p, extra=""):
    b = p["selected"]
    lvl = p["brawlers"][b]["level"]
    info = BRAWLERS[b]

    colors = {
        "Common": 0x7f8c8d,
        "Rare": 0x3498db,
        "Super Rare": 0x2ecc71,
        "Epic": 0x9b59b6,
        "Mythique": 0xe67e22,
        "Légendaire": 0xf1c40f,
        "Ultra Légendaire": 0xe74c3c
    }

    embed = discord.Embed(
        title=f"🔥 {b} • Niveau {lvl}",
        description=f"✨ {info['rarity']} • {info['role']}",
        color=colors[info["rarity"]]
    )

    embed.add_field(
        name="📊 Progression",
        value=f"`{progress_bar(lvl)}`\n**{lvl}/11**",
        inline=False
    )

    embed.add_field(
        name="💰 Compte",
        value=f"🪙 `{p['coins']}`\n🏆 `{p['trophies']}`",
        inline=True
    )

    embed.add_field(
        name="🎁 Inventaire",
        value=f"📦 `{p['boxes']}`",
        inline=True
    )

    if extra:
        embed.add_field(name="⚡ Action", value=f"```{extra}```", inline=False)

    return embed

# ---------- SELECT ---------- #

class BrawlerSelect(discord.ui.Select):
    def __init__(self, p):
        options = [
            discord.SelectOption(
                label=b,
                description=f"Lvl {p['brawlers'][b]['level']} • {BRAWLERS[b]['rarity']}"
            ) for b in p["brawlers"]
        ][:25]

        super().__init__(placeholder="Choisir un brawler", options=options)

    async def callback(self, i):
        data = load()
        p = get_player(data, str(i.user.id))

        p["selected"] = self.values[0]
        save(data)

        view = MainView(i.user)
        view.add_item(BrawlerSelect(p))

        await i.response.edit_message(embed=create_embed(p, "Switch"), view=view)

# ---------- VIEW ---------- #

class MainView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=120)
        self.user = user

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.user.id:
            await i.response.send_message("Pas pour toi", ephemeral=True)
            return False
        return True

    # 👊 CLICK
    @discord.ui.button(label="Click", emoji="👊", style=discord.ButtonStyle.primary)
    async def click(self, i: discord.Interaction, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        check_reset_daily(p)

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]
        rarity = BRAWLERS[b]["rarity"]
        role = BRAWLERS[b]["role"]

        base = random.randint(5, 10)
        gain = int(base * level_multiplier(lvl) * RARITY_MULTIPLIER[rarity])
        gain, msg = apply_role_bonus(role, gain, p)

        drop = ""
        if random.random() < 0.08:
            p["boxes"] += 1
            drop = "🎁 +1 box"

        p["coins"] += gain
        p["trophies"] += 1

        if "daily" not in p:
            p["daily"] = get_daily()

        if p["daily"]["done"] < p["daily"]["click"]:
            p["daily"]["done"] += 1
            if p["daily"]["done"] >= p["daily"]["click"]:
                p["coins"] += p["daily"]["reward"]
                msg += f"\n🎯 Quête terminée +{p['daily']['reward']} coins"

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        txt = f"+{gain} coins"
        if msg:
            txt += f"\n{msg}"
        if drop:
            txt += f"\n{drop}"

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, txt),
            view=view
        )

    # 🎁 BOX
    @discord.ui.button(label="Box", emoji="🎁", style=discord.ButtonStyle.success)
    async def box(self, i: discord.Interaction, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        if p["boxes"] <= 0:
            return await i.followup.send("Pas de box", ephemeral=True)

        p["boxes"] -= 1

        coins = random.randint(50, 150)
        p["coins"] += coins

        rewards = [f"+{coins} coins"]

        if random.random() < 0.55:
            rarity = roll_rarity()
            brawler = random_brawler(rarity)

            if brawler not in p["brawlers"]:
                p["brawlers"][brawler] = {"level": 1}
                rewards.append(f"🧑‍🎤 Nouveau {brawler}")
            else:
                bonus = random.randint(40, 120)
                p["coins"] += bonus
                rewards.append(f"🔁 Doublon → +{bonus}")

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, "\n".join(rewards)),
            view=view
        )

    # ⬆️ UPGRADE
    @discord.ui.button(label="Upgrade", emoji="⬆️", style=discord.ButtonStyle.secondary)
    async def upgrade(self, i: discord.Interaction, _):
        await i.response.defer()

        data = load()
        p = get_player(data, str(self.user.id))

        b = p["selected"]
        lvl = p["brawlers"][b]["level"]

        if lvl >= 11:
            return await i.followup.send("Niveau max", ephemeral=True)

        cost = int(100 * RARITY_MULTIPLIER[BRAWLERS[b]["rarity"]] * (2 ** (lvl - 1)))

        if p["coins"] < cost:
            return await i.followup.send(f"Pas assez ({cost})", ephemeral=True)

        p["coins"] -= cost
        p["brawlers"][b]["level"] += 1

        save(data)

        view = MainView(self.user)
        view.add_item(BrawlerSelect(p))

        await i.followup.edit_message(
            message_id=i.message.id,
            embed=create_embed(p, f"Upgrade (-{cost})"),
            view=view
        )

    # 🛒 SHOP
    @discord.ui.button(label="Shop", emoji="🛒", style=discord.ButtonStyle.secondary)
    async def shop(self, i: discord.Interaction, _):
        import time

        data = load()
        check_daily_shop(data)
        save(data)

        shop = data["shop"]
        daily = shop.get("daily_brawler")

        rarity = BRAWLERS[daily]["rarity"]
        price = BRAWLER_PRICES[rarity]

        # ⏳ countdown
        remaining = shop["reset_time"] - int(time.time())
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        embed = discord.Embed(title="🛒 Shop")
        embed.description = (
            f"📦 Box — {SHOP['box']['price']} coins (1/jour)\n\n"
            f"🔥 Brawler du jour:\n{daily} — {price} coins\n\n"
            f"⏳ Reset dans {hours}h {minutes}m"
        )
        await i.response.send_message(
            embed=embed,
            view=ShopView(self.user),
            ephemeral=True
        )
# ---------- LEADERBOARD ---------- #

class LeaderboardView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=60)
        self.data = data
        self.mode = "coins"

    def get_embed(self):
        top = sorted(
            self.data.items(),
            key=lambda x: x[1].get(self.mode, 0),
            reverse=True
        )[:10]

        desc = "\n".join(
            [f"**{i+1}.** <@{u}> — {p.get(self.mode, 0)}" for i, (u, p) in enumerate(top)]
        )

        return discord.Embed(title=f"🏆 {self.mode}", description=desc or "Vide")

    @discord.ui.button(label="Switch", style=discord.ButtonStyle.primary)
    async def switch(self, i: discord.Interaction, _):
        self.mode = "trophies" if self.mode == "coins" else "coins"
        await i.response.edit_message(embed=self.get_embed(), view=self)
        
class ShopView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=60)
        self.user = user

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.user.id:
            await i.response.send_message("Pas pour toi", ephemeral=True)
            return False
        return True

    # 🔥 BRAWLER DU JOUR
    @discord.ui.button(label="Brawler du jour", style=discord.ButtonStyle.success)
    async def buy_daily_brawler(self, i: discord.Interaction, _):
        data = load()
        check_daily_shop(data)

        p = get_player(data, str(self.user.id))

        brawler = data["shop"]["daily_brawler"]
        rarity = BRAWLERS[brawler]["rarity"]
        price = BRAWLER_PRICES[rarity]

        if p["coins"] < price:
            return await i.response.send_message("Pas assez", ephemeral=True)

        p["coins"] -= price

        if brawler in p["brawlers"]:
            p["coins"] += 300
            msg = "🔁 Doublon → +300 coins"
        else:
            p["brawlers"][brawler] = {"level": 1}
            msg = f"🧑‍🎤 {brawler} débloqué"

        save(data)
        await i.response.send_message(msg, ephemeral=True)

    # 📦 ACHETER BOX (FIX)
    @discord.ui.button(label="Acheter Box", style=discord.ButtonStyle.primary)
    async def buy_box(self, i: discord.Interaction, _):
        import time

        await i.response.defer(ephemeral=True)  # 🔥 IMPORTANT

        data = load()
        p = get_player(data, str(self.user.id))

        now = int(time.time())

        # cooldown
        if now - p["last_box_buy"] < 86400:
            remaining = 86400 - (now - p["last_box_buy"])
            h = remaining // 3600
            m = (remaining % 3600) // 60

            return await i.followup.send(
                f"⏳ Déjà acheté aujourd'hui\nRéessaie dans {h}h {m}m",
                ephemeral=True
            )

        # pas assez
        if p["coins"] < SHOP["box"]["price"]:
            return await i.followup.send("❌ Pas assez de coins", ephemeral=True)

        # achat
        p["coins"] -= SHOP["box"]["price"]
        p["boxes"] += 1
        p["last_box_buy"] = now

        save(data)

        await i.followup.send("📦 Box achetée (1/jour)", ephemeral=True)
# ---------- COG ---------- #

class BSGame(commands.GroupCog, name="bs"):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="quest")
    async def quest(self, interaction):
        data = load()
        p = get_player(data, str(interaction.user.id))

        check_reset_daily(p)
        save(data)

        d = p["daily"]

        embed = discord.Embed(title="🎯 Quête du jour")
        embed.description = (
            f"👊 Clicks: {d['done']}/{d['click']}\n"
            f"💰 Récompense: {d['reward']} coins"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 🎁 GIVE ADMIN
    @app_commands.command(name="give", description="Donner des récompenses")
    @app_commands.describe(
        user="Utilisateur",
        type="Type: coins / box / brawler",
        amount="Quantité (pas pour brawler)",
        brawler="Nom du brawler (si type=brawler)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def give(
        self,
        interaction,
        user: discord.User,
        type: str,
        amount: int = 0,
        brawler: str = None
    ):
        data = load()
        p = get_player(data, str(user.id))

        msg = ""

        # 💰 COINS
        if type.lower() == "coins":
            if amount <= 0:
                return await interaction.response.send_message("Montant invalide", ephemeral=True)

            p["coins"] += amount
            msg = f"💰 {amount} coins donnés à {user.mention}"

        # 🎁 BOX
        elif type.lower() == "box":
            if amount <= 0:
                return await interaction.response.send_message("Montant invalide", ephemeral=True)

            p["boxes"] += amount
            msg = f"🎁 {amount} box(s) données à {user.mention}"

        # 🧑‍🎤 BRAWLER
        elif type.lower() == "brawler":
            if not brawler:
                return await interaction.response.send_message("Nom du brawler manquant", ephemeral=True)

            if brawler not in BRAWLERS:
                return await interaction.response.send_message("Brawler invalide", ephemeral=True)

            if brawler in p["brawlers"]:
                bonus = 200
                p["coins"] += bonus
                msg = f"🔁 Doublon {brawler} → +{bonus} coins"
            else:
                p["brawlers"][brawler] = {"level": 1}
                msg = f"🧑‍🎤 {brawler} donné à {user.mention}"

        else:
            return await interaction.response.send_message(
                "Type invalide (coins/box/brawler)", ephemeral=True
            )

        save(data)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Give réussi",
                description=msg,
                color=0x2ecc71
            ),
            ephemeral=True
        )

    # 🎮 PLAY
    @app_commands.command(name="play")
    async def play(self, interaction):
        await interaction.response.defer(ephemeral=True)

        data = load()
        p = get_player(data, str(interaction.user.id))

        view = MainView(interaction.user)
        view.add_item(BrawlerSelect(p))

        await interaction.followup.send(
            embed=create_embed(p),
            view=view,
            ephemeral=True
        )

    # 🏆 LEADERBOARD
    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction):
        data = load()
        view = LeaderboardView(data)

        await interaction.response.send_message(
            embed=view.get_embed(),
            view=view,
            ephemeral=True
        )
# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(BSGame(bot))
