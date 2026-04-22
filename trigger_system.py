import discord
from discord.ext import commands
from discord import app_commands
import json, os, time, random

# ---------- FILES ---------- #

TRIGGERS_FILE = "/data/triggers.json"
CHANNEL_TRIGGER_FILE = "/data/channel_triggers.json"

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

def load_channel_triggers():
    if os.path.exists(CHANNEL_TRIGGER_FILE):
        with open(CHANNEL_TRIGGER_FILE) as f:
            return json.load(f)
    return {}

def save_channel_triggers(data):
    with open(CHANNEL_TRIGGER_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------- COG ---------- #

class TriggerSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_track = {}
        self.cooldown = {}

    # ---------- GROUP ---------- #

    setup_group = app_commands.Group(name="setup", description="Configuration du bot")
    channel_group = app_commands.Group(name="channel", description="Triggers par salon")

    # ---------- TRIGGER COMMAND ---------- #

    @setup_group.command(name="trigger")
    async def trigger(self, interaction: discord.Interaction, action: str, word: str = None, response: str = None):
        data = load_triggers()
        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        if action == "add":
            if not word or not response:
                return await interaction.response.send_message("❌ mot + réponse requis", ephemeral=True)

            if word.lower() not in data[guild_id]:
                data[guild_id][word.lower()] = []

            data[guild_id][word.lower()].append(response)
            save_triggers(data)

            return await interaction.response.send_message(f"✅ `{word}` ajouté", ephemeral=True)

        elif action == "remove":
            if word and word.lower() in data[guild_id]:
                del data[guild_id][word.lower()]
                save_triggers(data)
                return await interaction.response.send_message("🗑️ supprimé", ephemeral=True)

            return await interaction.response.send_message("❌ introuvable", ephemeral=True)

        elif action == "list":
            txt = "\n".join([f"{k} ({len(v)})" for k, v in data[guild_id].items()]) or "vide"
            await interaction.response.send_message(txt, ephemeral=True)

    # ---------- CHANNEL COMMANDS ---------- #

    @channel_group.command(name="set")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        data = load_channel_triggers()
        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id][str(channel.id)] = message
        save_channel_triggers(data)

        await interaction.response.send_message(f"✅ activé dans {channel.mention}", ephemeral=True)

    @channel_group.command(name="remove")
    async def remove_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_channel_triggers()
        guild_id = str(interaction.guild.id)

        if guild_id in data and str(channel.id) in data[guild_id]:
            del data[guild_id][str(channel.id)]
            save_channel_triggers(data)
            return await interaction.response.send_message("🗑️ supprimé", ephemeral=True)

        await interaction.response.send_message("❌ rien", ephemeral=True)

    @channel_group.command(name="list")
    async def list_channel(self, interaction: discord.Interaction):
        data = load_channel_triggers()
        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            return await interaction.response.send_message("vide", ephemeral=True)

        txt = "\n".join([f"<#{cid}> → {msg}" for cid, msg in data[guild_id].items()])
        await interaction.response.send_message(txt or "vide", ephemeral=True)

    # ---------- AUTO REACTIONS ---------- #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.lower()
        guild_id = str(message.guild.id)
        user_id = message.author.id
        now = time.time()

        # cooldown
        if user_id in self.cooldown and now - self.cooldown[user_id] < 2:
            return

        # ---------- CHANNEL TRIGGER ---------- #
        channel_data = load_channel_triggers()

        if guild_id in channel_data:
            if str(message.channel.id) in channel_data[guild_id]:
                await message.channel.send(channel_data[guild_id][str(message.channel.id)])
                self.cooldown[user_id] = now
                return

        # ---------- WORD TRIGGERS ---------- #
        data = load_triggers()

        if guild_id in data:
            for word, responses in data[guild_id].items():
                if word in content:
                    await message.channel.send(random.choice(responses))
                    self.cooldown[user_id] = now
                    break

        # ---------- SPAM ---------- #
        if user_id not in self.spam_track:
            self.spam_track[user_id] = []

        self.spam_track[user_id].append(now)
        self.spam_track[user_id] = [t for t in self.spam_track[user_id] if now - t < 5]

        if len(self.spam_track[user_id]) >= 5:
            await message.channel.send(f"{message.author.mention} calme toi chef 😭")
            self.spam_track[user_id] = []

        await self.bot.process_commands(message)

# ---------- SETUP ---------- #

async def setup(bot):
    await bot.add_cog(TriggerSystem(bot))
