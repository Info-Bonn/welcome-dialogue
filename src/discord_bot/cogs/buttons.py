import json
from typing import Union

import discord
from discord.ext import commands

from ..environment import GUILD, ROLES, ONBOARDING_ROLE, START_CHANNEL, ROLE_OPTION_FILE

"""
Used to start a new dialogue on the server
"""

class EntryPointButton(discord.ui.Button["Onboarding"]):
    def __init__(self, bot: commands.Bot, label: str):
        super().__init__()
        self.bot = bot
        self.label = label
        self.style = discord.ButtonStyle.green

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=OnboardingButtons(self.bot), ephemeral=True)


class EntryPointView(discord.ui.View):
    def __init__(self, bot: commands.Bot, label: str, timeout=None):
        super().__init__(timeout=timeout)

        self.add_item(EntryPointButton(bot, label))


"""
Used for the actual onboarding
"""


class SelectionButton(discord.ui.Button["Onboarding"]):
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


class CommitButton(discord.ui.Button["Onboarding"]):
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

    def __init__(self, bot: commands.Bot, timeout=None):
        super().__init__(timeout=timeout)

        self.bot = bot
        self.buttons: list[Union[SelectionButton, CommitButton]] = []

        # buttons will be generated from that
        with open(ROLE_OPTION_FILE, "r") as f:
            button_option_dict: dict = json.load(f)
            # we can assume that there is only one key since this bot is currently single server
            guild_key = list(button_option_dict.keys())[0]  # TODO: come up with a better solution
            self.button_option_dict = button_option_dict[guild_key]["role_buttons"]

        # generate buttons
        for k, v in self.button_option_dict.items():
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

        # add default roles to the mix and remove onboarding role if user is new
        onboarding_role = guild.get_role(ONBOARDING_ROLE)  # role that member only has during onboarding
        if default_roles and onboarding_role in member.roles:
            roles.extend(guild.get_role(role) for role in default_roles)
            update_message = (f"Du bist nun freigeschaltet! - "
                              f"Schau doch mal in {guild.get_channel(START_CHANNEL).mention} vorbei :)")
            reason = "First time onboarding"
            # remove onboarding
            await member.remove_roles(onboarding_role, reason=reason)

        # member was already here before
        else:
            update_message = f"Deine Rollen wurden aktualisiert. Viel Spaß weiterhin!"
            reason = "Role Update via buttons"

        available_roles = [guild.get_role(button.role_id)
                           for button in self.buttons
                           if isinstance(button, SelectionButton)]

        selected_roles = [guild.get_role(button.role_id)
                          for button in self.buttons
                          if isinstance(button, SelectionButton) and button.style == discord.ButtonStyle.green]

        # add roles
        # all roles from that menu the user has at the moment (roles not given trough that menu removed via intersect)
        member_roles_set = set(member.roles).intersection(available_roles)
        selected_roles_set = set(selected_roles)

        # roles member selected but does not have yet
        to_give = selected_roles_set.difference(member_roles_set)
        await member.add_roles(*to_give, reason=reason)

        # roles member has but does not want
        to_remove = member_roles_set.difference(selected_roles_set)
        await member.remove_roles(*to_remove, reason="Onboarding finished")

        # send message
        await interaction.response.send_message(
            content=update_message,
            ephemeral=True
        )
