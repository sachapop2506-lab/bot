import discord
from discord.ext import commands
import random
import json
import os
import difflib
import unicodedata
import re

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

MEMORY_FILE = "memory.json"

# -------- NORMALIZE -------- #
def normalize(text):
    text = text.lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    text = re.sub(r"[^\w\s]", "", text)
    return text

# -------- MEMOIRE -------- #
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

memory = load_memory()

# -------- KEYWORDS -------- #
KEYWORDS = {

# SALUTATIONS
"bonjour": ["bonjour", "salut", "hello", "yo", "cc", "hey", "wesh"],

# POLITESSE
"merci": ["merci", "thx", "thanks", "mercii"],
"stp": ["stp", "svp", "sil te plait", "s'il te plait", "s il te plait"],
"désolé": ["désolé", "desole", "sorry", "pardon"],

# QUESTIONS BOT
"ça va": ["ça va", "ca va", "cv", "tu vas bien", "ca dit quoi"],
"tu fais quoi": ["tu fais quoi", "tu fais", "quoi de neuf"],
"tu es qui": ["tu es qui", "t'es qui", "qui es tu"],
"tu es vivant": ["tu es vivant", "t'es vivant", "t vivant"],
"tu dors": ["tu dors", "t'es reveille", "tu es la"],

# AIDE
"aide": ["aide", "help", "commande", "cmd", "besoin aide"],

# HUMOUR
"blague": ["blague", "drôle", "drole", "humour", "joke"],
"mdr": ["mdr", "ptdr", "lol", "😂", "🤣"],

# SERVEUR
"règles": ["regles", "règles", "rules"],
"role": ["role", "roles", "rôle"],
"staff": ["staff", "admin", "modo", "moderateur"],

# GAMING
"game": ["game", "jeu", "jouer", "play"],
"win": ["win", "gg", "victoire"],
"lose": ["lose", "defaite", "perdu"],

# INSULTES (soft)
"nul": ["nul", "zero", "mauvais"],
"idiot": ["idiot", "debile", "con"],

# TEMPS
"heure": ["heure", "time"],
"jour": ["jour", "date", "today"],

# MOTIVATION
"motivation": ["motivation", "motiver"],
"fatigue": ["fatigue", "fatigué", "creve"],
"triste": ["triste", "sad", "deprime"],

# RANDOM
"ok": ["ok", "d'accord", "dac"],
"oui": ["oui", "yes", "ouais"],
"non": ["non", "no", "nop"],

# BOT
"ping": ["ping"],
"latence": ["latence", "ms", "ping bot"],
"update": ["update", "maj", "mise a jour"],

# NIGHT
"dormir": ["dormir", "dodo", "sleep"],
"nuit": ["nuit", "bonne nuit"],
"tard": ["tard", "late"],

# SOCIAL
"invite": ["invite", "invitation"],
"ami": ["ami", "pote", "friend"],

# FUN
"boss": ["boss", "chef"],
"meilleur": ["meilleur", "best"],
"hack": ["hack", "pirate"],
"secret": ["secret"],

# ERREUR
"bug": ["bug", "glitch"],
"erreur": ["erreur", "error"],

# BONUS
"ennui": ["ennui", "bored", "ennuye"],
}

# -------- RESPONSES -------- #
RESPONSES = {

# SALUTATIONS
"bonjour": ["Salut 👋", "Hello 😄", "Yo !"],
"salut": ["Wesh 😎", "Salut !", "Hey 👋"],
"yo": ["Yo 🔥", "Bien ou quoi ?", "Quoi de neuf ?"],
"cc": ["Coucou 👋", "Salut !"],
"hey": ["Hey 😄", "Yo !"],

# POLITESSE
"merci": ["De rien 😁", "Avec plaisir 👍", "Toujours là 💪"],
"stp": ["Pas besoin de supplier 😏", "Je vois ça 👀"],
"s'il te plaît": ["Ok ok 😄", "Je gère 👍"],
"désolé": ["Tkt 😌", "C’est rien 👍"],
"pardon": ["Ça passe 😄"],

# QUESTIONS BOT
"ça va": ["Oui tranquille 😎", "Toujours en forme 💪", "Et toi ?"],
"tu fais quoi": ["Je surveille 👀", "Je bosse 😤", "Je code 😎"],
"tu es qui": ["Je suis ton bot 🤖", "Une IA stylée 😏"],
"tu es vivant": ["Presque 👀", "Plus que toi 😏"],
"tu dors": ["Jamais 😈", "Toujours actif 🔥"],

# AIDE
"aide": ["Utilise /help 👍", "Je peux t’aider 😄"],
"commande": ["Tape /help 📜", "Regarde mes commandes"],
"help": ["Voici mes commandes 🔧", "Besoin d’aide ?"],

# HUMOUR
"blague": [
    "Pourquoi les dev aiment le noir ? Parce que la lumière attire les bugs 🐛",
    "Un bug c’est juste une feature surprise 😏",
    "Je bug pas, je teste 😎"
],
"mdr": ["😂", "🤣", "T’es mort 😭"],
"lol": ["😂", "🤣"],
"ptdr": ["💀", "😂"],

# SERVEUR
"règles": ["Lis le salon règles 📜", "Respecte les règles 😤"],
"role": ["Va dans les rôles 👍", "Utilise les réactions"],
"staff": ["Contacte un admin 👮", "Le staff veille 👀"],

# GAMING
"game": ["On joue à quoi ? 🎮", "Je suis chaud 🔥"],
"jouer": ["Invite-moi 😏", "Je carry 😎"],
"win": ["GG 🔥", "Bien joué 👏"],
"lose": ["Rip 😭", "Ça arrive 💀"],

# INSULTES (réponses clean)
"nul": ["Pas très sympa ça 😐", "Respecte un peu 😤"],
"bot nul": ["C’est pas gentil 😢", "Je fais de mon mieux 😔"],
"idiot": ["Calme 😅", "On reste chill 😎"],

# TEMPS
"heure": ["Je n’ai pas de montre 😅", "Regarde ton tel 📱"],
"jour": ["On est aujourd’hui 😄", "Bonne journée !"],

# MOTIVATION
"motivation": [
    "Lâche rien 💪",
    "Tu peux le faire 🔥",
    "Continue comme ça 👑"
],
"fatigue": ["Va dormir 😴", "Repose-toi 🛌"],
"triste": ["Courage ❤️", "Ça va aller 😌"],

# RANDOM
"quoi": ["Quoi ? 😐", "Oui ?"],
"hein": ["Hein ? 🤨"],
"ok": ["Ok 👍", "Parfait 😄"],
"d'accord": ["Nice 👍"],
"non": ["Ok 😅"],
"oui": ["Parfait 😄"],

# BOT COMMAND
"ping": ["Pong 🏓"],
"latence": ["Je suis rapide ⚡"],
"update": ["Je suis à jour 🔥"],

# NIGHT
"dormir": ["Bonne nuit 😴", "Va te reposer 🛌"],
"nuit": ["Bonne nuit 🌙"],
"tard": ["Va dormir 😏"],

# SOCIAL
"invite": ["Invite tes potes 👥", "Plus on est mieux c’est 😄"],
"ami": ["Les amis c’est important ❤️"],

# FUN EXTRA
"boss": ["C’est moi 😏", "Toi 👑"],
"meilleur": ["Évidemment 😎", "Toujours 🔥"],
"hack": ["👀", "Je vois tout"],
"secret": ["Je dis rien 🤐"],

# ERREUR
"bug": ["C’est pas un bug 😏", "Feature 👀"],
"erreur": ["Oups 😅", "Ça arrive"],

# BONUS
"bored": ["On s’ennuie ? 😏", "Va parler à quelqu’un 😄"],
"ennui": ["Fais un jeu 🎮", "Discute 😄"],

}

# -------- DETECTION -------- #
def find_best_match(text):
    text = normalize(text)
    words = text.split()

    best_score = 0
    best_key = None

    for key, variants in KEYWORDS.items():
        for word in words:
            for v in variants + [key]:
                score = difflib.SequenceMatcher(None, word, normalize(v)).ratio()
                if score > best_score:
                    best_score = score
                    best_key = key

    if best_score > 0.7:
        return best_key

    return None

# -------- PSEUDO IA -------- #
def generate_smart_reply(text):
    if "?" in text:
        return random.choice(["Bonne question 🤔", "Ça dépend 😅"])

    if len(text) > 50:
        return "Résumé stp 😭"

    return random.choice(["Hmm 🤔", "Je vois 👀", "Pas faux 😅"])

# -------- EVENT -------- #
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:

        content = message.content
        content = content.replace(f"<@{bot.user.id}>", "")
        content = content.replace(f"<@!{bot.user.id}>", "")
        text = content.strip()

        if text == "":
            await message.channel.send(f"Oui {message.author.mention} ? 👀")
            return

        # 🔍 détection
        match = find_best_match(text)

        if match and match in RESPONSES:
            await message.channel.send(random.choice(RESPONSES[match]))
            return

        # 🧠 mémoire
        if text in memory:
            await message.channel.send(random.choice(memory[text]))
            return

        # 🤖 fallback
        reply = generate_smart_reply(text)
        await message.channel.send(reply)

        memory[text] = [reply]
        save_memory(memory)

    await bot.process_commands(message)

bot.run("TON_TOKEN")
