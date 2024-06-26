import core.predictor as predictor
import disnake
from core.grades.grades import Grades
from core.schedule.schedule import Schedule
from core.subjects.subjects_cache import SubjectsCache
from disnake.ext import commands
from disnake.ext.commands import InteractionBot
from utils.utils import os_environ, write_db


class General(commands.Cog):
    def __init__(self, client: InteractionBot):
        self.client = client

    async def scheduleCommand(
        self,
        inter: disnake.ApplicationCommandInteraction,
        day_start: int = 1,
        day_end: int = 5,
        week: int = 1,
        show_day: bool | None = None,
        show_classroom: bool | None = None,
    ):
        await inter.response.defer()
        await inter.followup.send(
            file=await Schedule.db_schedule(bool(week - 1)).render(day_start, day_end, show_day, show_classroom)
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
        subject_name: str,
    ):
        if not isinstance(inter.channel, disnake.TextChannel):
            raise Exception("Channel is not a text channel")

        subject = SubjectsCache.tryGetSubjectByName(subject_name)
        if subject is None:
            return await inter.response.send_message(f'Předmět "{subject_name}" neexistuje.')

        await inter.response.send_message("Sending predictor embed message", delete_after=0)
        await predictor.predict_embed(subject_name, inter.channel, self.client)

    slashGradePrediction = commands.InvokableSlashCommand(
        gradesPrediction,
        name="grade_prediction",
        description="Makes a prediction of your grades",
        options=[
            disnake.Option(
                name="subject_name",
                description="Subject to predict the grade for",
                choices=SubjectsCache.getSlashCommandSubjectChoices(),
                type=disnake.OptionType.string,
                required=True,
            )
        ],
    )

    async def gradesAverage(
        self,
        inter: disnake.ApplicationCommandInteraction,
        subject_name: str,
    ):
        subject = SubjectsCache.tryGetSubjectByName(subject_name)
        if subject is None:
            return await inter.response.send_message(f'Předmět "{subject_name}" neexistuje.')

        average = Grades.db_grades().by_subject_name(subject_name).average()
        if average == None:
            return await inter.response.send_message(f'Pro předmět "{subject_name}" nemáte dosud žádné známky.')

        embed = disnake.Embed()
        embed.set_author(name=f"Průměr z {subject.fullName}:")
        embed.title = str(average)
        embed.color = disnake.Color.from_rgb(0, 255, 255)

        await inter.response.send_message(embed=embed)

    slashGradesAverage = commands.InvokableSlashCommand(
        gradesAverage,
        name="grade_average",
        description="Gets the average grade for a given subject",
        options=[
            disnake.Option(
                name="subject_name",
                description="Subject to get the average for",
                choices=SubjectsCache.getSlashCommandSubjectChoices(),
                type=disnake.OptionType.string,
                required=True,
            ),
        ],
    )


def admin_user_check(inter: disnake.ApplicationCommandInteraction) -> bool:
    return inter.author.id == os_environ("adminID")


class Admin(commands.Cog):
    def __init__(self, client: InteractionBot):
        self.client = client

    group = commands.group(name="admin", description="Admin commands")

    async def updateScheduleDatabase(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

        schedule1 = await Schedule.get_schedule(False, self.client)
        schedule2 = await Schedule.get_schedule(True, self.client)
        if schedule1 is None or schedule2 is None:
            await inter.followup.send("Bakalari's server is currently down.")
        else:
            schedule1.db_save()
            schedule2.db_save()

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
            grades.db_save()
            await inter.followup.send("Updated grades database")

    slashUpdateGradesDatabase = commands.InvokableSlashCommand(
        updateGradesDatabase,
        name="update_grades_database",
        description="Updates the grades database",
        checks=[admin_user_check],
        group=group,
    )

    async def getSubjects(self, inter: disnake.ApplicationCommandInteraction):
        """Gets all cached subjects"""

        subjects = [f"{subject.shortName}: {subject.fullName}" for subject in SubjectsCache.subjects]
        await inter.send("\n".join(subjects))

    slashGetSubjects = commands.InvokableSlashCommand(
        getSubjects,
        name="get_subjects",
        description="Gets the subjects",
        checks=[admin_user_check],
        group=group,
    )


class Settings(commands.Cog):
    def __init__(self, client: InteractionBot):
        self.client = client

    group = commands.group(name="settings", description="Edits the bot's settings")

    scheduleSettings = {"Show_day": "showDay", "show_classroom": "showClassroom"}

    async def scheduleSettingsCommand(
        self,
        inter: disnake.ApplicationCommandInteraction,
        setting: str,
        bool: bool,
    ):
        write_db(self.scheduleSettings[setting], bool)
        await inter.response.send_message(f"Setting {setting} set to {bool}", ephemeral=True)

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
                required=True,
            ),
            disnake.Option(
                name="bool",
                description="True or False value",
                type=disnake.OptionType.boolean,
                required=True,
            ),
        ],
    )

    async def reminderShortSettings(
        self,
        inter: disnake.ApplicationCommandInteraction,
        bool: bool,
    ):
        write_db("reminderShort", bool)
        await inter.response.send_message(f"Setting Reminder_short set to {bool}", ephemeral=True)

    slashReminderShortSettings = commands.InvokableSlashCommand(
        reminderShortSettings,
        name="reminder_short",
        description="Whether to use the short lesson name or full name",
        checks=[admin_user_check],
        group=group,
        options=[
            disnake.Option(
                name="bool",
                description="True or False value",
                type=disnake.OptionType.boolean,
                required=True,
            )
        ],
    )

    channels = ["Grades", "Schedule", "Reminder", "Status"]

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
                required=True,
            ),
        ],
    )


COGS: list[commands.CogMeta] = [General, Admin, Settings]


def setupBotInteractions(client: commands.InteractionBot):
    """Sets up the bot's interactions (commands)"""

    for cog in COGS:
        client.add_cog(cog(client))
