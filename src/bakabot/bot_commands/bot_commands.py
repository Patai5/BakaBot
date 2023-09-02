import discord
from discord.ext import commands

from bakabot.core.grades.grades import Grades
from bakabot.core.predictor import Predictor
from bakabot.core.schedule.schedule import Schedule
from bakabot.utils.utils import os_environ, write_db


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
    async def grades_prediction(
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

    @commands.slash_command(name="grade_average", description="Gets the average grade for a given subject")
    async def grades_average(
        self,
        ctx,
        subject: discord.Option(
            str,
            name="subject",
            description="Subject to get the average for",
            choices=[
                discord.OptionChoice(name=val, value=key)
                for key, val in sorted(Grades.SUBJECTS.items(), key=lambda item: item[1])
            ],
        ),
    ):
        subjectLongName = Grades.SUBJECTS.get(subject)
        average = Grades.db_grades().by_subject(subject).average()
        if average == None:
            await ctx.respond(f'Pro předmět "{subjectLongName}" nemáte dosud žádné známky.')
            return

        embed = discord.Embed()
        embed.set_author(name=f"Průměr z {subjectLongName}:")
        embed.title = str(average)
        embed.color = discord.Color.from_rgb(0, 255, 255)

        await ctx.respond(embed=embed)


class Admin(commands.Cog):
    def __init__(self, client: discord.Bot):
        self.client = client

    group = discord.SlashCommandGroup(name="admin", description="Admin commands")

    def admin_user():
        def predicate(ctx):
            return ctx.author.id == os_environ("adminID")

        return commands.check(predicate)

    async def user_not_admin(ctx: discord.ApplicationContext, error: discord.DiscordException):
        if not isinstance(error, discord.errors.CheckFailure):
            raise error
        await ctx.respond("Only admins can use this command! " + str(ctx.author.id))

    @admin_user()
    @group.command(name="update_schedule_database", description="Updates the schedule database")
    async def update_schedule_database(self, ctx):
        await ctx.response.defer(ephemeral=True)

        schedule1 = await Schedule.get_schedule(False, self.client)
        schedule2 = await Schedule.get_schedule(True, self.client)
        if schedule1 is None or schedule2 is None:
            await ctx.followup.send("Bakalari's server is currently down.")
        else:
            write_db("schedule1", schedule1)
            write_db("schedule2", schedule2)
            await ctx.followup.send("Updated schedule database")

    @update_schedule_database.error
    async def update_schedule_database_error(self, ctx, error):
        await Admin.user_not_admin(ctx, error)

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
        await Admin.user_not_admin(ctx, error)


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

    @Admin.admin_user()
    @group.command(name="reminder_short", description="Wheter to use the short lesson name or full name")
    async def schedule_settings_command(
        self,
        ctx,
        boolean: discord.Option(bool, name="bool", description="True or False value"),
    ):
        write_db("reminderShort", boolean)
        await ctx.respond(f"Setting Reminder_short set to {boolean}", ephemeral=True)

    @schedule_settings_command.error
    async def schedule_settings_command_error(self, ctx, error):
        await Admin.user_not_admin(ctx, error)

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
        await Admin.user_not_admin(ctx, error)


COGS = [General, Settings, Admin]
