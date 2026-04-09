import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import os
import urllib.parse

BS_API_BASE = "https://api.brawlstars.com/v1"


def get_api_key() -> str | None:
    return os.getenv("BRAWLSTARS_API_KEY")


def format_tag(tag: str) -> str:
    tag = tag.strip().upper()
    if not tag.startswith("#"):
        tag = "#" + tag
    return tag


class BrawlStarsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    bs_group = app_commands.Group(name="bs", description="Commandes Brawl Stars")

    @bs_group.command(name="profil", description="Voir le profil Brawl Stars d'un joueur")
    @app_commands.describe(tag="Le tag du joueur (ex: #ABC123)")
    async def profil(self, interaction: discord.Interaction, tag: str):
        api_key = get_api_key()
        if not api_key:
            await interaction.response.send_message(
                "❌ Clé API Brawl Stars non configurée. Contacte un administrateur.", ephemeral=True
            )
            return

        await interaction.response.defer()
        tag = format_tag(tag)
        encoded_tag = urllib.parse.quote(tag)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BS_API_BASE}/players/{encoded_tag}",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send("❌ Joueur introuvable. Vérifie le tag.")
                    return
                elif resp.status == 403:
                    await interaction.followup.send("❌ Clé API invalide ou IP non autorisée.")
                    return
                elif resp.status != 200:
                    await interaction.followup.send(f"❌ Erreur API ({resp.status}). Réessaie plus tard.")
                    return
                data = await resp.json()

        brawlers = data.get("brawlers", [])
        max_brawler = max(brawlers, key=lambda b: b["trophies"], default=None) if brawlers else None
        club = data.get("club", {})

        embed = discord.Embed(
            title=f"🎮 {data['name']}",
            description=f"Tag : `{data['tag']}`",
            color=discord.Color.from_str("#FFDD00"),
        )
        embed.add_field(name="🏆 Trophées", value=f"{data['trophies']:,}", inline=True)
        embed.add_field(name="📈 Record", value=f"{data['highestTrophies']:,}", inline=True)
        embed.add_field(name="⭐ Niveau", value=str(data["expLevel"]), inline=True)
        embed.add_field(name="⚔️ Victoires 3v3", value=f"{data.get('3vs3Victories', 0):,}", inline=True)
        embed.add_field(name="🥇 Victoires Solo", value=f"{data.get('soloVictories', 0):,}", inline=True)
        embed.add_field(name="🤝 Victoires Duo", value=f"{data.get('duoVictories', 0):,}", inline=True)
        embed.add_field(name="🎯 Brawlers débloqués", value=str(len(brawlers)), inline=True)

        if max_brawler:
            embed.add_field(
                name="🌟 Meilleur Brawler",
                value=f"{max_brawler['name']} ({max_brawler['trophies']:,} 🏆)",
                inline=True,
            )

        if club:
            embed.add_field(name="🏠 Club", value=club.get("name", "Aucun"), inline=True)
        else:
            embed.add_field(name="🏠 Club", value="Aucun", inline=True)

        embed.set_footer(text="Brawl Stars • api.brawlstars.com")
        await interaction.followup.send(embed=embed)

    @bs_group.command(name="brawlers", description="Voir les brawlers d'un joueur")
    @app_commands.describe(tag="Le tag du joueur (ex: #ABC123)")
    async def brawlers(self, interaction: discord.Interaction, tag: str):
        api_key = get_api_key()
        if not api_key:
            await interaction.response.send_message(
                "❌ Clé API Brawl Stars non configurée.", ephemeral=True
            )
            return

        await interaction.response.defer()
        tag = format_tag(tag)
        encoded_tag = urllib.parse.quote(tag)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BS_API_BASE}/players/{encoded_tag}",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send("❌ Joueur introuvable. Vérifie le tag.")
                    return
                elif resp.status != 200:
                    await interaction.followup.send(f"❌ Erreur API ({resp.status}).")
                    return
                data = await resp.json()

        brawlers = sorted(data.get("brawlers", []), key=lambda b: b["trophies"], reverse=True)

        if not brawlers:
            await interaction.followup.send("❌ Aucun brawler trouvé.")
            return

        embed = discord.Embed(
            title=f"🎭 Brawlers de {data['name']}",
            description=f"**{len(brawlers)}** brawlers débloqués",
            color=discord.Color.from_str("#FF6B35"),
        )

        top_15 = brawlers[:15]
        lines = []
        for b in top_15:
            rank = f"Rang {b['rank']}" if b.get("rank") else ""
            power = b.get("power", "?")
            lines.append(f"**{b['name']}** — Niv.{power} | {b['trophies']:,} 🏆 {rank}")

        embed.description = "\n".join(lines)
        if len(brawlers) > 15:
            embed.set_footer(text=f"Affichage des 15 meilleurs sur {len(brawlers)} brawlers")
        await interaction.followup.send(embed=embed)

    @bs_group.command(name="club", description="Voir les infos d'un club Brawl Stars")
    @app_commands.describe(tag="Le tag du club (ex: #ABC123)")
    async def club(self, interaction: discord.Interaction, tag: str):
        api_key = get_api_key()
        if not api_key:
            await interaction.response.send_message(
                "❌ Clé API Brawl Stars non configurée.", ephemeral=True
            )
            return

        await interaction.response.defer()
        tag = format_tag(tag)
        encoded_tag = urllib.parse.quote(tag)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BS_API_BASE}/clubs/{encoded_tag}",
                headers={"Authorization": f"Bearer {api_key}"},
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send("❌ Club introuvable. Vérifie le tag.")
                    return
                elif resp.status != 200:
                    await interaction.followup.send(f"❌ Erreur API ({resp.status}).")
                    return
                data = await resp.json()

        members = data.get("members", [])
        top_member = members[0] if members else None

        embed = discord.Embed(
            title=f"🏠 {data['name']}",
            description=data.get("description", "*Pas de description*"),
            color=discord.Color.from_str("#4CAF50"),
        )
        embed.add_field(name="Tag", value=f"`{data['tag']}`", inline=True)
        embed.add_field(name="🏆 Trophées", value=f"{data.get('trophies', 0):,}", inline=True)
        embed.add_field(name="👥 Membres", value=f"{len(members)}/30", inline=True)
        embed.add_field(name="🔒 Type", value=data.get("type", "?").capitalize(), inline=True)
        embed.add_field(name="🏅 Trophées requis", value=f"{data.get('requiredTrophies', 0):,}", inline=True)

        if top_member:
            embed.add_field(
                name="🌟 Meilleur membre",
                value=f"{top_member['name']} ({top_member.get('trophies', 0):,} 🏆)",
                inline=True,
            )

        embed.set_footer(text="Brawl Stars • api.brawlstars.com")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BrawlStarsCog(bot))
