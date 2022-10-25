import asyncio
import copy
import datetime

import discord
from discord.ext import commands
from utils.utils import MessageTimers, os_environ, read_db, write_db

from core.betting import Betting
from core.grades import Grades
from core.predictor import Predictor
from core.schedule import Schedule


class General(commands.Cog):
    def __init__(self, client: discord.Bot):
        self.client = client

    @commands.slash_command(name="schedule", description="Sends the schedule")
    async def schedule_command(
        self,
        ctx,
        day_start: discord.Option(
            int,
            name="day_start",
            description="The first day of the schedule",
            default=1,
            choices=[discord.OptionChoice(name=str(i), value=i) for i in range(1, 6)],
        ),
        day_end: discord.Option(
            int,
            name="day_end",
            description="The last day of the schedule",
            default=5,
            choices=[discord.OptionChoice(name=str(i), value=i) for i in reversed(range(1, 6))],
        ),
        week: discord.Option(
            int,
            name="week",
            description="Current or future week of the schedule",
            default=1,
            choices=[discord.OptionChoice(name=str(i), value=i) for i in range(1, 3)],
        ),
        show_day: discord.Option(
            bool,
            name="show_day",
            description="Whether to show the days or not",
            default=None,
        ),
        show_classroom: discord.Option(
            bool,
            name="show_classroom",
            description="Whether to show the classrooms or not",
            default=None,
        ),
    ):
        await ctx.response.defer()
        await ctx.followup.send(
            file=await Schedule.db_schedule(week - 1).render(day_start, day_end, show_day, show_classroom)
        )

    @commands.slash_command(name="grade_prediction", description="Makes a prediction of your grades")
    async def grades_command(
        self,
        ctx,
        subject: discord.Option(
            str,
            name="subject",
            description="Subject to predict the grade for",
            choices=[
                discord.OptionChoice(name=val, value=key)
                for key, val in sorted(Grades.SUBJECTS.items(), key=lambda item: item[1])
            ],
        ),
    ):
        await ctx.respond("Sending predictor embed message", delete_after=0)
        await Predictor.predict_embed(subject, ctx, self.client)


class Admin(commands.Cog):
    def __init__(self, client: discord.Bot):
        self.client = client

    group = discord.SlashCommandGroup(name="admin", description="Admin commands")

    def admin_user():
        def predicate(ctx):
            return ctx.author.id == os_environ("adminID")

        return commands.check(predicate)

    async def user_not_admin(ctx):
        await ctx.respond("Only admins can use this command!")

    @admin_user()
    @group.command(name="update_schedule_database", description="Updates the schedule database")
    async def update_schedule_database(self, ctx):
        await ctx.response.defer(ephemeral=True)

        schedule1 = await Schedule.get_schedule(False, self.client)
        schedule2 = await Schedule.get_schedule(True, self.client)
        if schedule1 is None or schedule2 is None:
            await ctx.followup.send("Bakalari's server is currently down.")
        else:
            write_db("schedule1", Schedule.json_dumps(schedule1))
            write_db("schedule2", Schedule.json_dumps(schedule2))
            await ctx.followup.send("Updated schedule database")

    @update_schedule_database.error
    async def update_schedule_database_error(self, ctx, error):
        await Admin.user_not_admin(ctx)

    @admin_user()
    @group.command(name="update_grades_database", description="Updates the grades database")
    async def update_grades_database(self, ctx):
        await ctx.response.defer(ephemeral=True)

        grades = await Grades.get_grades(self.client)
        if grades is None:
            await ctx.followup.send("Bakalari's server is currently down.")
        else:
            write_db("grades", Grades.json_dumps(grades))
            await ctx.followup.send("Updated grades database")

    @update_grades_database.error
    async def update_grades_database_error(self, ctx, error):
        await Admin.user_not_admin(ctx)


class Settings(commands.Cog):
    def __init__(self, client: discord.Bot):
        self.client = client

    group = discord.SlashCommandGroup(name="settings", description="Edits the bot's settings")

    scheduleSettings = {"Show_day": "showDay", "show_classroom": "showClassroom"}

    @Admin.admin_user()
    @group.command(name="schedule", description="Settings for schedule apperance")
    async def schedule_settings_command(
        self,
        ctx,
        setting: discord.Option(
            str,
            name="setting",
            description="Which setting to change",
            choices=[discord.OptionChoice(name=key, value=key) for key in scheduleSettings.keys()],
        ),
        boolean: discord.Option(bool, name="bool", description="True or False value"),
    ):
        write_db(self.scheduleSettings[setting], boolean)
        await ctx.respond(f"Setting {setting} set to {boolean}", ephemeral=True)

    @schedule_settings_command.error
    async def schedule_settings_command_error(self, ctx, error):
        await Admin.user_not_admin(ctx)

    channels = ["Schedule", "Grades", "Predictor", "Reminder"]

    @Admin.admin_user()
    @group.command(
        name="channel",
        description="Use this command in the channel where you want to have the bot's functions to send messages",
    )
    async def channel_schedule_command(
        self,
        ctx,
        function: discord.Option(
            str,
            name="function",
            description="Select the function for this channel",
            choices=[discord.OptionChoice(name=channel, value=channel) for channel in channels],
        ),
    ):
        write_db(f"channel{function}", ctx.channel.id)
        await ctx.respond(f"channel_{function.lower()} changed to this channel", ephemeral=True)

    @channel_schedule_command.error
    async def channel_schedule_command_error(self, ctx, error):
        await Admin.user_not_admin(ctx)


COGS = [General, Settings, Admin]


class Reactions:
    def __init__(self, message: discord.Message, user: discord.Member, emoji: discord.emoji, client: discord.Client):
        self.message = message
        self.user = user
        self.emoji = emoji
        self.client = client
        self.userReactions = [reaction for reaction in self.message.reactions if reaction.count > 1]

    class Predictor:
        queryMessagesDatabase = "predictorMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    if message.edited_at:
                        editedFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.edited_at).seconds
                        if editedFromNowSec > 300:
                            await MessageTimers.delete_message(message, cls.queryMessagesDatabase, client)
                        else:
                            asyncio.ensure_future(
                                MessageTimers.delete_message(
                                    message,
                                    cls.queryMessagesDatabase,
                                    client,
                                    300 - editedFromNowSec,
                                )
                            )
                    else:
                        createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                        if createdFromNowSec > 300:
                            await MessageTimers.delete_message(message, cls.queryMessagesDatabase, client)
                        else:
                            asyncio.ensure_future(
                                MessageTimers.delete_message(
                                    message,
                                    cls.queryMessagesDatabase,
                                    client,
                                    300 - createdFromNowSec,
                                )
                            )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction):
            stage = Predictor.get_stage(reaction.message)
            if stage == 1:
                await Predictor.update_grade(reaction, reaction.client)
            elif stage == 2:
                await Predictor.update_weight(reaction, reaction.client)

    class Grades:
        queryMessagesDatabase = "gradesMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages_reactions(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                    if createdFromNowSec > 5400:
                        await MessageTimers.delete_message_reaction(
                            message, cls.queryMessagesDatabase, Grades.PREDICTOR_EMOJI, client
                        )
                    else:
                        asyncio.ensure_future(
                            MessageTimers.delete_message_reaction(
                                message,
                                cls.queryMessagesDatabase,
                                Grades.PREDICTOR_EMOJI,
                                client,
                                5400 - createdFromNowSec,
                            )
                        )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction):
            if reaction.emoji.name == Grades.PREDICTOR_EMOJI:
                await Grades.create_predection(reaction.message, reaction.client)

    class Betting:
        queryMessagesDatabase = "bettingMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages_reactions(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                    if createdFromNowSec > 43200:
                        await MessageTimers.delete_message_reaction(
                            message, cls.queryMessagesDatabase, Betting.BETT_EMOJI, client
                        )
                    else:
                        asyncio.ensure_future(
                            MessageTimers.delete_message_reaction(
                                message,
                                cls.queryMessagesDatabase,
                                Betting.BETT_EMOJI,
                                client,
                                43200 - createdFromNowSec,
                            )
                        )

        # Executes the method for of this function
        @classmethod
        async def execute(cls, reaction):
            if reaction.emoji.name == Betting.BETT_EMOJI:
                await Betting.make_bet(reaction, reaction.client)

    REACTIONS = {Predictor, Grades, Betting}

    # Executes the message's command
    async def execute(self):
        for user in self.message.reactions:
            if user.me:
                for reaction in Reactions.REACTIONS:
                    if reaction.queryMessagesDatabase:
                        for message in read_db(reaction.queryMessagesDatabase):
                            if self.message.id == message[0]:
                                await reaction.execute(self)
                                return

    @staticmethod
    async def query(client: discord.Client):
        for reaction in Reactions.REACTIONS:
            if reaction.queryMessagesDatabase:
                asyncio.ensure_future(reaction.query(client))


class Responses:
    def __init__(self, message: discord.Message, client: discord.Client):
        self.message = message
        self.client = client
        self.isResponse = message.channel.id in self.client.response_channel_cache

    class Bett:
        queryMessagesDatabase = "bettMessages"

        @classmethod
        async def query(cls, client: discord.Client):
            # Deletes some removed messages from the database while the bot was off
            messages = await MessageTimers.query_messages(cls.queryMessagesDatabase, client)
            if messages:
                for message in messages:
                    message_id = message.id
                    message_channel = message.channel.id

                    createdFromNowSec = (datetime.datetime.now(datetime.timezone.utc) - message.created_at).seconds
                    if createdFromNowSec > 300:
                        await MessageTimers.delete_message(
                            [message_id, message_channel],
                            cls.queryMessagesDatabase,
                            client,
                            0,
                            lambda: Betting.remove_unfinished_bet([message_id, message_channel], client),
                        )
                    else:
                        asyncio.ensure_future(
                            MessageTimers.delete_message(
                                [message_id, message_channel],
                                cls.queryMessagesDatabase,
                                client,
                                300 - createdFromNowSec,
                                lambda: Betting.remove_unfinished_bet([message_id, message_channel], client),
                            )
                        )

    RESPONSE_FOR = {"betting": Betting}
    RESPONSES = {Bett}

    # Executes the message's command
    async def execute(self):
        if self.isResponse:
            responseFor = self.RESPONSE_FOR.get(self.client.response_channel_cache.get(self.channel.id))
            await responseFor.response(self.message, self.client)

    @staticmethod
    async def query(client: discord.Client):
        """Queries the response channels to the client cache and removes the messages to be removed"""
        responseChannels = read_db("responseChannels")
        for responseChannel in copy.copy(responseChannels):
            users = read_db(f"{responseChannels[responseChannel]}ResponseChannel")
            for user in copy.copy(users):
                try:
                    message = await client.get_channel(responseChannel).fetch_message(users[user])
                except:
                    print(
                        f"""Couldn't get the desired message! Was probably removed!:\n
                        message_id: {users[user]}, message_channel: {responseChannel}"""
                    )
                    del users[user]
            write_db(f"{responseChannels[responseChannel]}ResponseChannel", users)
            if users:
                client.response_channel_cache[responseChannel] = responseChannels[responseChannel]
            else:
                del responseChannels[responseChannel]
        write_db("responseChannels", responseChannels)

        for response in Responses.RESPONSES:
            if response.queryMessagesDatabase:
                await response.query(client)
