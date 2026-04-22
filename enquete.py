import random
import discord
from discord.ext import commands
from discord import app_commands
from collections import defaultdict
import datetime, time, timedelta
import random

class SleepMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sleep_time = None  # heure limite
        self.last_warn = {}  # {user_id: datetime}

    # -------- COMMAND -------- #
    @app_commands.command(name="sleepmode", description="Active le mode 'va dormir'")
    async def sleepmode(self, interaction: discord.Interaction, heure: int, minute: int):
        self.sleep_time = time(hour=heure, minute=minute)
        await interaction.response.send_message(
            f"🌙 Mode sommeil activé à {heure:02d}:{minute:02d}"
        )

    # -------- LISTENER -------- #
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.sleep_time is None:
            return

        now = datetime.now().time()

        # Vérifie si on est après l'heure
        if now >= self.sleep_time:
            user_id = message.author.id
            now_dt = datetime.now()

            # cooldown 30 minutes
            if user_id in self.last_warn:
                if now_dt - self.last_warn[user_id] < timedelta(minutes=30):
                    return

            self.last_warn[user_id] = now_dt

            await message.channel.send(
                f"🌙 {message.author.mention} va dormir il est tard !"
            )

async def setup(bot):
    await bot.add_cog(SleepMode(bot))

class Enquete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_stats = defaultdict(lambda: {
            "messages": 0,
            "hours": [],
            "channels": defaultdict(int)
        })

    # 📊 TRACK MESSAGES
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        data = self.user_stats[message.author.id]
        data["messages"] += 1
        data["hours"].append(message.created_at.hour)
        data["channels"][message.channel.name] += 1

    # 🔎 ENQUETE
    @app_commands.command(name="enquete", description="Analyse un utilisateur")
    async def enquete(self, interaction: discord.Interaction, member: discord.Member):
        data = self.user_stats.get(member.id)

        if not data or data["messages"] == 0:
            return await interaction.response.send_message("Aucune donnée.", ephemeral=True)

        # heure la plus active
        most_active_hour = max(set(data["hours"]), key=data["hours"].count)

        # salon préféré
        fav_channel = max(data["channels"], key=data["channels"].get)

        await interaction.response.send_message(
            f"🔎 Analyse de {member.mention}\n\n"
            f"📨 Messages : {data['messages']}\n"
            f"🕒 Heure active : {most_active_hour}h\n"
            f"💬 Salon préféré : #{fav_channel}\n\n"
            f"🧠 Conclusion : comportement... suspect."
        )

    # 😈 ANALYSE FLIPPANTE
    @app_commands.command(name="analyse", description="Analyse creepy")
    async def analyse(self, interaction: discord.Interaction, member: discord.Member):
        data = self.user_stats.get(member.id)

        if not data or not data["hours"]:
            return await interaction.response.send_message("Pas assez d'infos...", ephemeral=True)

        hour = random.choice(data["hours"])
        fake_day = random.randint(10, 28)

        messages = [
            f"👁️ Je sais que tu étais actif le {fake_day} avril à {hour}h...",
            f"📡 Activité détectée à {hour}h. Ce n’est pas passé inaperçu.",
            f"⚠️ Tu reviens souvent vers {hour}h... intéressant.",
            f"🧠 Pattern détecté... connexion fréquente à {hour}h.",
            f"👀 Je te surveille depuis un moment..."
        ]

        await interaction.response.send_message(random.choice(messages))
        
async def setup(bot):
    await bot.add_cog(Enquete(bot))
