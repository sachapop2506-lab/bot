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

# -------- INTENTS -------- #
INTENTS = {

# SALUTATIONS
"bonjour": {
    "patterns": [
        "bonjour", "salut", "yo", "cc", "hey", "wesh",
        "bien ou quoi", "quoi de neuf", "salut ca va"
    ]
},

# POLITESSE
"merci": {
    "patterns": [
        "merci", "merci beaucoup", "mercii", "thanks", "thx"
    ]
},

"stp": {
    "patterns": [
        "stp", "svp", "s'il te plait", "sil te plait",
        "tu peux", "peux tu", "tu pourrais"
    ]
},

"désolé": {
    "patterns": [
        "désolé", "desole", "pardon", "je suis desole",
        "sorry"
    ]
},

# QUESTIONS BOT
"ça va": {
    "patterns": [
        "ça va", "ca va", "cv", "tu vas bien",
        "ça dit quoi", "tout va bien", "bien ou quoi"
    ]
},

"tu fais quoi": {
    "patterns": [
        "tu fais quoi", "tu fais quoi la",
        "tu fais quoi maintenant",
        "quoi de neuf", "tu fais quoi aujourd'hui"
    ]
},

"tu es qui": {
    "patterns": [
        "tu es qui", "t'es qui", "qui es tu",
        "c'est qui toi", "tu es quoi"
    ]
},

"tu es vivant": {
    "patterns": [
        "tu es vivant", "t'es vivant",
        "t'es reel", "t'es humain"
    ]
},

"tu dors": {
    "patterns": [
        "tu dors", "t'es reveille",
        "tu es la", "tu es actif"
    ]
},

# AIDE
"aide": {
    "patterns": [
        "aide", "help", "j'ai besoin d'aide",
        "tu peux m'aider", "comment faire",
        "explique moi"
    ]
},

# HUMOUR
"blague": {
    "patterns": [
        "blague", "raconte une blague",
        "dis une blague", "fais moi rire",
        "humour"
    ]
},

"mdr": {
    "patterns": [
        "mdr", "ptdr", "lol", "😂", "🤣",
        "trop drole", "je rigole"
    ]
},

# SERVEUR
"règles": {
    "patterns": [
        "regles", "règles", "c'est quoi les regles",
        "les regles du serveur"
    ]
},

"role": {
    "patterns": [
        "role", "roles", "comment avoir un role",
        "donne moi un role"
    ]
},

"staff": {
    "patterns": [
        "staff", "admin", "modo",
        "contacter staff", "y'a un admin"
    ]
},

# GAMING
"game": {
    "patterns": [
        "on joue", "tu joues", "game",
        "on joue a quoi", "tu veux jouer"
    ]
},

"win": {
    "patterns": [
        "j'ai gagne", "win", "gg",
        "victoire", "on a gagne"
    ]
},

"lose": {
    "patterns": [
        "j'ai perdu", "lose",
        "defaite", "on a perdu"
    ]
},

# INSULTES (soft)
"nul": {
    "patterns": [
        "t'es nul", "c'est nul",
        "zero", "trop mauvais"
    ]
},

"idiot": {
    "patterns": [
        "idiot", "debile",
        "t'es con", "t'es bete"
    ]
},

# TEMPS
"heure": {
    "patterns": [
        "quelle heure", "il est quelle heure",
        "heure actuelle"
    ]
},

"jour": {
    "patterns": [
        "quel jour", "on est quel jour",
        "date aujourd'hui"
    ]
},

# MOTIVATION
"motivation": {
    "patterns": [
        "motivation", "motive moi",
        "encourage moi"
    ]
},

"fatigue": {
    "patterns": [
        "je suis fatigue", "fatigue",
        "j'ai sommeil", "creve"
    ]
},

"triste": {
    "patterns": [
        "je suis triste", "triste",
        "deprime", "sad"
    ]
},

# RANDOM
"ok": {
    "patterns": [
        "ok", "d'accord", "dac"
    ]
},

"oui": {
    "patterns": [
        "oui", "ouais", "yes"
    ]
},

"non": {
    "patterns": [
        "non", "nop", "no"
    ]
},

# BOT
"ping": {
    "patterns": [
        "ping", "test ping"
    ]
},

"latence": {
    "patterns": [
        "latence", "ping bot",
        "combien de ms"
    ]
},

"update": {
    "patterns": [
        "update", "maj",
        "mise a jour"
    ]
},

# NIGHT
"dormir": {
    "patterns": [
        "je vais dormir", "bonne nuit",
        "je vais dodo"
    ]
},

"nuit": {
    "patterns": [
        "bonne nuit", "nuit"
    ]
},

"tard": {
    "patterns": [
        "il est tard", "trop tard"
    ]
},

# SOCIAL
"invite": {
    "patterns": [
        "invite", "inviter quelqu'un",
        "comment inviter"
    ]
},

"ami": {
    "patterns": [
        "ami", "pote",
        "friend"
    ]
},

# FUN
"boss": {
    "patterns": [
        "c'est qui le boss",
        "qui est le boss"
    ]
},

"meilleur": {
    "patterns": [
        "le meilleur", "c'est le meilleur"
    ]
},

"hack": {
    "patterns": [
        "tu hack", "hack",
        "pirate"
    ]
},

"secret": {
    "patterns": [
        "secret", "dis moi un secret"
    ]
},

# ERREUR
"bug": {
    "patterns": [
        "bug", "ca bug",
        "glitch"
    ]
},

"erreur": {
    "patterns": [
        "erreur", "error",
        "probleme"
    ]
},

# BONUS
"ennui": {
    "patterns": [
        "je m'ennuie", "ennui",
        "bored", "je fais rien"
    ]
},

}

# -------- RESPONSES -------- #
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
# -------- DETECTION PHRASE -------- #
def detect_intent(text):
    text = normalize(text)

    best_score = 0
    best_intent = None

    for intent, data in INTENTS.items():
        for pattern in data["patterns"]:
            score = difflib.SequenceMatcher(
                None,
                text,
                normalize(pattern)
            ).ratio()

            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score > 0.6:
        return best_intent

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

        # 🧠 détection phrases
        intent = detect_intent(text)

        if intent and intent in RESPONSES:
            await message.channel.send(random.choice(RESPONSES[intent]))
            return

        # 💾 mémoire
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
