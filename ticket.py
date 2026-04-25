import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import datetime, timezone
from utils import data_path

TICKETS_FILE = data_path("tickets.json")
CONFIG_FILE = data_path("ticket_config.json")


# ================== FILE UTILS ================== #

def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_tickets(data):
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ================== SELECT ================== #

class TicketCategorySelect(discord.ui.Select):
    def __init__(self, guild_id):
        config = load_config()
        guild_config = config.get(str(guild_id), {})
        categories = guild_config.get("categories", [])

        options = [
            discord.SelectOption(
                label=cat["label"],
                value=cat["id"],
                description=cat["description"],
            )
            for cat in categories
        ]

        if not options:
            options = [
                discord.SelectOption(
                    label="Aucune catégorie",
                    value="none",
                    description="Utilise /ticket config",
                )
            ]

        super().__init__(
            placeholder="Choisis une catégorie...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select",
        )

    async def callback(self, interaction: discord.Interaction):
        category_id = self.values[0]

        config = load_config()
        guild_config = config.get(str(interaction.guild_id), {})
        categories = guild_config.get("categories", [])

        category = next((c for c in categories if c["id"] == category_id), None)

        if not category:
            await interaction.response.send_message("❌ Catégorie invalide.", ephemeral=True)
            return

        tickets = load_tickets()

        for t in tickets.values():
            if (
                t["guild_id"] == str(interaction.guild_id)
                and t["user_id"] == str(interaction.user.id)
                and not t["closed"]
            ):
                await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket : <#{t['channel_id']}>",
                    ephemeral=True,
                )
                return

        await interaction.response.send_message("⏳ Création du ticket...", ephemeral=True)

        guild = interaction.guild

        staff_role_id = guild_config.get("staff_role_id")
        staff_role = guild.get_role(int(staff_role_id)) if staff_role_id else None

        ticket_category = (
            guild.get_channel(int(guild_config["category_id"]))
            if guild_config.get("category_id")
            else None
        )

        ticket_number = guild_config.get("ticket_count", 0) + 1
        channel_name = f"ticket-{ticket_number:04d}-{interaction.user.name[:10].lower()}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True)

        channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
        )

        guild_config["ticket_count"] = ticket_number
        config[str(guild.id)] = guild_config
        save_config(config)

        tickets[str(channel.id)] = {
            "channel_id": str(channel.id),
            "guild_id": str(guild.id),
            "user_id": str(interaction.user.id),
            "category": category_id,
            "closed": False,
        }

        save_tickets(tickets)

        embed = discord.Embed(
            title=f"{category['label']} — Ticket #{ticket_number}",
            description="Explique ton problème.",
            color=discord.Color.green(),
        )

        staff_mention = staff_role.mention if staff_role else "Staff"

        await channel.send(
            content=f"{interaction.user.mention} | {staff_mention}",
            embed=embed,
            view=TicketCloseView(),
        )

        await interaction.edit_original_response(
            content=f"✅ Ticket créé : {channel.mention}"
        )


# ================== VIEW ================== #

class TicketPanelView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect(guild_id))


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="🔒 Fermer",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close_button"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        tickets = load_tickets()
        key = str(interaction.channel_id)

        if key not in tickets:
            return

        tickets[key]["closed"] = True
        save_tickets(tickets)

        await interaction.response.send_message("🔒 Fermeture...")

        import asyncio
        await asyncio.sleep(3)

        await interaction.channel.delete()


# ================== COG ================== #

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ticket_group = app_commands.Group(name="ticket", description="Système de tickets")

    # SETUP
    @ticket_group.command(name="setup", description="Configurer les tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        role_staff: discord.Role,
        categorie: discord.CategoryChannel = None,
    ):
        config = load_config()

        config[str(interaction.guild_id)] = {
            "panel_channel_id": str(salon.id),
            "staff_role_id": str(role_staff.id),
            "category_id": str(categorie.id) if categorie else None,
            "ticket_count": 0,
            "categories": [],
        }

        save_config(config)

        embed = discord.Embed(
            title="🎫 Tickets",
            description="Choisis une catégorie",
        )

        await salon.send(embed=embed, view=TicketPanelView(interaction.guild_id))

        await interaction.response.send_message("✅ Config faite", ephemeral=True)

    # AJOUT CATEGORIE
    @ticket_group.command(name="config", description="Ajouter une catégorie")
    @app_commands.describe(
        nom="Nom de la catégorie",
        description="Description"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def config_ticket(self, interaction: discord.Interaction, nom: str, description: str):
        config = load_config()
        guild_id = str(interaction.guild_id)

        if guild_id not in config:
            await interaction.response.send_message("❌ Fais /ticket setup", ephemeral=True)
            return

        categories = config[guild_id].get("categories", [])

        # Anti doublon
        if any(c["label"].lower() == nom.lower() for c in categories):
            await interaction.response.send_message("❌ Déjà existant.", ephemeral=True)
            return

        categories.append({
            "id": nom.lower().replace(" ", "_"),
            "label": nom,
            "description": description,
        })

        config[guild_id]["categories"] = categories
        save_config(config)

        await interaction.response.send_message("✅ Catégorie ajoutée", ephemeral=True)

        # 🔥 UPDATE PANEL AUTO
        channel_id = config[guild_id].get("panel_channel_id")
        if channel_id:
            channel = interaction.guild.get_channel(int(channel_id))

            embed = discord.Embed(
                title="🎫 Tickets",
                description="Choisis une catégorie",
            )

            await channel.send(embed=embed, view=TicketPanelView(interaction.guild_id))


# ================== LOAD ================== #

async def setup(bot):
    await bot.add_cog(TicketCog(bot))

    config = load_config()

    for guild_id in config.keys():
        bot.add_view(TicketPanelView(guild_id))

    bot.add_view(TicketCloseView())
