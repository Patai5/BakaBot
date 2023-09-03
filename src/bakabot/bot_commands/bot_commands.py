import core.predictor as predictor
import disnake
from constants import SUBJECTS
from core.grades.grades import Grades
from disnake.ext import commands
from utils.utils import os_environ, write_db

from bakabot.core.schedule.schedule import Schedule


class General(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    async def scheduleCommand(
        self,
        inter: disnake.ApplicationCommandInteraction,
        dayStart: int = 1,
        dayEnd: int = 5,
        week: int = 1,
        showDay: bool | None = None,
        showClassroom: bool | None = None,
    ):
        await inter.response.defer()
        await inter.response.send_message(
            file=await Schedule.db_schedule(bool(week - 1)).render(dayStart, dayEnd, showDay, showClassroom)
        )

    slashScheduleCommand = commands.InvokableSlashCommand(
        scheduleCommand,
        name="schedule",
        description="Sends the schedule",
        options=[
            disnake.Option(
                name="day_start",
                description="The first day of the schedule",
                choices=[disnake.OptionChoice(name=str(i), value=i) for i in range(1, 6)],
                type=disnake.OptionType.integer,
            ),
            disnake.Option(
                name="day_end",
                description="The last day of the schedule",
                choices=[disnake.OptionChoice(name=str(i), value=i) for i in reversed(range(1, 6))],
                type=disnake.OptionType.integer,
            ),
            disnake.Option(
                name="week",
                description="Current or future week of the schedule",
                choices=[disnake.OptionChoice(name=str(i), value=i) for i in range(1, 3)],
                type=disnake.OptionType.integer,
            ),
            disnake.Option(
                name="show_day",
                description="Whether to show the days or not",
                type=disnake.OptionType.boolean,
            ),
            disnake.Option(
                name="show_classroom",
                description="Whether to show the classrooms or not",
                type=disnake.OptionType.boolean,
            ),
        ],
    )

    async def gradesPrediction(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str,
    ):
        if not isinstance(inter.channel, disnake.TextChannel):
            raise Exception("Channel is not a text channel")

        await inter.response.send_message("Sending predictor embed message", delete_after=0)
        await predictor.predict_embed(subject, inter.channel, self.client)

    slashGradePrediction = commands.InvokableSlashCommand(
        gradesPrediction,
        name="grade_prediction",
        description="Makes a prediction of your grades",
        options=[
            disnake.Option(
                name="subject",
                description="Subject to predict the grade for",
                choices=[
                    disnake.OptionChoice(name=val, value=key)
                    for key, val in sorted(SUBJECTS.items(), key=lambda item: item[1])
                ],
                type=disnake.OptionType.string,
            )
        ],
    )

    async def gradesAverage(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject: str,
    ):
        subjectLongName = SUBJECTS.get(subject)
        average = Grades.db_grades().by_subject(subject).average()
        if average == None:
            await inter.response.send_message(f'Pro předmět "{subjectLongName}" nemáte dosud žádné známky.')
            return

        embed = disnake.Embed()
        embed.set_author(name=f"Průměr z {subjectLongName}:")
        embed.title = str(average)
        embed.color = disnake.Color.from_rgb(0, 255, 255)

        await inter.response.send_message(embed=embed)

    slashGradesAverage = commands.InvokableSlashCommand(
        gradesAverage,
        name="grade_average",
        description="Gets the average grade for a given subject",
        options=[
            disnake.Option(
                name="subject",
                description="Subject to get the average for",
                choices=[
                    disnake.OptionChoice(name=val, value=key)
                    for key, val in sorted(SUBJECTS.items(), key=lambda item: item[1])
                ],
                type=disnake.OptionType.string,
            ),
        ],
    )


def admin_user_check(inter: disnake.ApplicationCommandInteraction) -> bool:
    return inter.author.id == os_environ("adminID")


class Admin(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    group = commands.group(name="admin", description="Admin commands")

    async def updateScheduleDatabase(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        schedule1 = await Schedule.get_schedule(False, self.client)
        schedule2 = await Schedule.get_schedule(True, self.client)
        if schedule1 is None or schedule2 is None:
            await inter.followup.send("Bakalari's server is currently down.")
        else:
            write_db("schedule1", schedule1)
            write_db("schedule2", schedule2)
            await inter.followup.send("Updated schedule database")

    slashUpdateScheduleDatabase = commands.InvokableSlashCommand(
        updateScheduleDatabase,
        name="update_schedule_database",
        description="Updates the schedule database",
        checks=[admin_user_check],
        group=group,
    )

    async def updateGradesDatabase(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        grades = await Grades.getGrades(self.client)
        if grades is None:
            await inter.followup.send("Bakalari's server is currently down.")
        else:
            write_db("grades", Grades.db_save(grades))
            await inter.followup.send("Updated grades database")

    slashUpdateGradesDatabase = commands.InvokableSlashCommand(
        updateGradesDatabase,
        name="update_grades_database",
        description="Updates the grades database",
        checks=[admin_user_check],
        group=group,
    )


class Settings(commands.Cog):
    def __init__(self, client: disnake.Client):
        self.client = client

    group = commands.group(name="settings", description="Edits the bot's settings")

    scheduleSettings = {"Show_day": "showDay", "show_classroom": "showClassroom"}

    async def scheduleSettingsCommand(
        self,
        inter: disnake.ApplicationCommandInteraction,
        setting: str,
        boolean: bool,
    ):
        write_db(self.scheduleSettings[setting], boolean)
        await inter.response.send_message(f"Setting {setting} set to {boolean}", ephemeral=True)

    slashScheduleSettings = commands.InvokableSlashCommand(
        scheduleSettingsCommand,
        name="settings",
        description="Edits the bot's settings",
        checks=[admin_user_check],
        group=group,
        options=[
            disnake.Option(
                name="setting",
                description="Which setting to change",
                choices=[disnake.OptionChoice(name=key, value=key) for key in scheduleSettings.keys()],
                type=disnake.OptionType.string,
            ),
            disnake.Option(
                name="bool",
                description="True or False value",
                type=disnake.OptionType.boolean,
            ),
        ],
    )

    async def reminderShortSettings(
        self,
        inter: disnake.ApplicationCommandInteraction,
        boolean: bool,
    ):
        write_db("reminderShort", boolean)
        await inter.response.send_message(f"Setting Reminder_short set to {boolean}", ephemeral=True)

    slashReminderShortSettings = commands.InvokableSlashCommand(
        reminderShortSettings,
        name="reminder_short",
        description="Whether to use the short lesson name or full name",
        checks=[admin_user_check],
        group=group,
        options=[disnake.Option(name="bool", description="True or False value", type=disnake.OptionType.boolean)],
    )

    channels = ["Schedule", "Grades", "Predictor", "Reminder"]

    async def channelSchedule(self, inter: disnake.ApplicationCommandInteraction, function: str):
        write_db(f"channel{function}", inter.channel_id)
        await inter.response.send_message(f"channel_{function.lower()} changed to this channel", ephemeral=True)

    slashChannelSchedule = commands.InvokableSlashCommand(
        channelSchedule,
        name="channel",
        description="Use this command in the channel where you want to have the bot's functions to send messages",
        checks=[admin_user_check],
        group=group,
        options=[
            disnake.Option(
                name="function",
                description="Select the function for this channel",
                choices=[disnake.OptionChoice(name=channel, value=channel) for channel in channels],
                type=disnake.OptionType.string,
            ),
        ],
    )


COGS: list[commands.CogMeta] = [General]
