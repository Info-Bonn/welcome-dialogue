from typing import Union

import discord
from discord.ext import commands

from ..environment import GUILD, ROLES, ONBOARDING_ROLE, START_CHANNEL


"""
Used to start a new dialogue on the server
"""

class EntryPointButton(discord.ui.Button):
    def __init__(self, bot: commands.Bot, label: str):
        super().__init__()
        self.bot = bot
        self.label = label
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=OnboardingButtons(self.bot), ephemeral=True)


class EntryPointView(discord.ui.View):
    def __init__(self, bot: commands.Bot, label: str):
        super().__init__()

        self.add_item(EntryPointButton(bot, label))


"""
Used for the actual onboarding
"""


class SelectionButton(discord.ui.Button):
    """ Button representing one role that can be selected """

    def __init__(self, label: str, role_id: int):
        super().__init__()
        self.og_label = label
        self.label = label
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        """ Toggle between green and gray and add checkmark, representing selection or not selection """
        if self.style == discord.ButtonStyle.gray:
            self.style = discord.ButtonStyle.green
            self.label = f"{self.label} \u2705"

        elif self.style == discord.ButtonStyle.green:
            self.style = discord.ButtonStyle.grey
            self.label = self.og_label

        # Make sure to update the message with our updated selves
        await interaction.response.edit_message(view=self.view)


class CommitButton(discord.ui.Button):
    """ Button used to call the function that gives the roles """
    def __init__(self, label: str, default_roles: list[int] = None):
        super().__init__()

        self.label = label
        self.style = discord.ButtonStyle.danger
        self.default_roles = default_roles

    async def callback(self, interaction: discord.Interaction):

        await self.view.commit_selection(interaction, default_roles=self.default_roles)


class OnboardingButtons(discord.ui.View):
    """ The view that contains the selection buttons as well as the commit button """

    def __init__(self, bot: commands.Bot):
        super().__init__()

        self.bot = bot
        self.buttons: list[Union[SelectionButton, CommitButton]] = []

        # buttons will be generated from that
        # TODO: put this into a dynamic json
        roles_dict = {
            "Ich bin Ersti": 1015979313029459998,
            "Ich studiere Informatik": 760444146505875459,
            "Ich studiere Cyber Security": 760444120769888278,
            "Ich studiere auf Lehramt": 760444168971091968
        }

        # generate buttons
        for k, v in roles_dict.items():
            button = SelectionButton(k, v)
            self.buttons.append(button)
            self.add_item(button)

        # add commit button, it's the last in the row
        commit_button = CommitButton("Bestätigen", default_roles=ROLES)
        self.buttons.append(commit_button)
        self.add_item(commit_button)

    async def commit_selection(self, interaction: discord.Interaction, default_roles: list[int] = None):
        """ Function walking all buttons, giving roles and removing the onboarding role"""
        guild = self.bot.get_guild(GUILD)
        member = guild.get_member(interaction.user.id)

        # role that member only has during onboarding
        onboarding_role = guild.get_role(ONBOARDING_ROLE)

        # member used an interaction again, but onboarding as already finished (role is missing)
        if onboarding_role not in member.roles:
            await interaction.response.edit_message(
                content="Du hast das setup bereits abgeschlossen.\n"
                        "Es wurden keine Veränderungen vorgenommen.",
                view=None  # remove buttons
            )
            return

        # member is not on guild
        if member is None:
            await interaction.response.edit_message(
                content="Du bist nicht mehr auf dem Server.",
                view=None  # remove buttons
            )
            return

        # generate list of roles to give
        roles = [guild.get_role(button.role_id)
                 for button in self.buttons
                 if isinstance(button, SelectionButton) and button.style == discord.ButtonStyle.green]

        # add default roles to the mix
        if default_roles:
            roles.extend(guild.get_role(role) for role in default_roles)

        # add roles
        await member.add_roles(*roles, reason="Onboarding dialogue")
        # remove onboarding
        await member.remove_roles(onboarding_role, reason="Onboarding finished")
        # send message
        await interaction.response.send_message(
            content=f"Du bist nun freigeschaltet! - "
                    f"Schau doch mal in {guild.get_channel(START_CHANNEL).mention} vorbei :)",
            ephemeral=True
        )














