import discord
from discord.ext import commands
from discord import app_commands
import json, os, time, random

TRIGGERS_FILE = "/data/triggers.json"
os.makedirs("/data", exist_ok=True)

# ---------- DATA ---------- #

def load_triggers():
    if os.path.exists(TRIGGERS_FILE):
        with open(TRIGGERS_FILE) as f:
            return json.load(f)
    return {}

def save_triggers(data):
    with open(TRIGGERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------- COG ---------- #

class TriggerSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_track = {}
        self.cooldown = {}

    # ---------- SETUP COMMAND ---------- #

    setup_group = app_commands.Group(name="setup", description="Configuration du bot")

    @setup_group.command(name="trigger", description="Gérer les triggers")
    @app_commands.describe(
        action="add / remove / list",
        word="mot déclencheur",
        response="réponse du bot"
    )
    async def trigger(
        self,
        interaction: discord.Interaction,
        action: str,
        word: str = None,
        response: str = None
    ):
        data = load_triggers()
        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        # ➕ ADD
        if action == "add":
            if not word or not response:
                return await interaction.response.send_message(
                    "❌ mot + réponse requis",
                    ephemeral=True
                )

            if word.lower() not in data[guild_id]:
                data[guild_id][word.lower()] = []

            data[guild_id][word.lower()].append(response)
            save_triggers(data)

            return await interaction.response.send_message(
                f"✅ Ajouté : `{word}` → `{response}`",
                ephemeral=True
            )

        # ➖ REMOVE
        elif action == "remove":
            if not word:
                return await interaction.response.send_message(
                    "❌ mot requis",
                    ephemeral=True
                )

            if word.lower() in data[guild_id]:
                del data[guild_id][word.lower()]
                save_triggers(data)

                return await interaction.response.send_message(
                    f"🗑️ Supprimé : `{word}`",
                    ephemeral=True
                )

            return await interaction.response.send_message(
                "❌ Introuvable",
                ephemeral=True
            )

        # 📜 LIST
        elif action == "list":
            if not data[guild_id]:
                return await interaction.response.send_message(
                    "Aucun trigger",
                    ephemeral=True
                )

            txt = ""
            for k, v in data[guild_id].items():
                txt += f"**{k}** → {len(v)} réponses\n"

            embed = discord.Embed(title="📜 Triggers", description=txt)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            await interaction.response.send_message(
                "❌ action invalide",
                ephemeral=True
            )

    # ---------- AUTO REACTIONS ---------- #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()
        guild_id = str(message.guild.id)
        user_id = message.author.id
        now = time.time()

        # ---------- COOLDOWN (évite spam bot) ---------- #
        if user_id in self.cooldown and now - self.cooldown[user_id] < 2:
            return

        # ---------- TRIGGERS ---------- #
        data = load_triggers()

        if guild_id in data:
            for word, responses in data[guild_id].items():
                if word in content:
                    rep = random.choice(responses)
                    await message.channel.send(rep)
                    self.cooldown[user_id] = now
                    break

        # ---------- QUOI → FEUR ---------- #
        if "quoi" in content:
            await message.channel.send("feur")
            self.cooldown[user_id] = now

        # ---------- SPAM DETECTION ---------- #
        if user_id not in self.spam_track:
            self.spam_track[user_id] = []

        self.spam_track[user_id].append(now)

        # garder messages < 5 sec
        self.spam_track[user_id] = [
            t for t in self.spam_track[user_id]
            if now - t < 5
        ]

        if len(self.spam_track[user_id]) >= 5:
            await message.channel.send(f"{message.author.mention} calme toi chef 😭")
            self.spam_track[user_id] = []

        await self.bot.process_commands(message)

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(TriggerSystem(bot))
