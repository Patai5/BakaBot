import disnake
from disnake.ext import commands
from disnake.ext.commands import InteractionBot
from disnake.interactions import ApplicationCommandInteraction

from ..constants import CHANNELS, FEATURES
from ..core.grades.grades import Grades
from ..core.predictor import predict_embed
from ..core.schedule.schedule import Schedule
from ..core.subjects.subjects_cache import SubjectsCache
from ..feature_manager.feature_manager import FeatureManager
from ..utils.utils import os_environ, read_db, write_db


class CustomCog(commands.Cog):
    def __init__(self, client: InteractionBot, featureManager: FeatureManager | None = None):
        self.client = client
        self.featureManager = featureManager


class General(CustomCog):
    async def scheduleCommand(
        self,
        inter: ApplicationCommandInteraction[InteractionBot],
        day_start: int = 1,
        day_end: int = 5,
        week: int = 1,
        show_day: bool | None = None,
        show_classroom: bool | None = None,
    ) -> None:
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
        inter: ApplicationCommandInteraction[InteractionBot],
        subject_name: str,
    ) -> None:
        if not isinstance(inter.channel, disnake.TextChannel):
            raise Exception("Channel is not a text channel")

        subject = SubjectsCache.tryGetSubjectByName(subject_name)
        if subject is None:
            return await inter.response.send_message(f'Předmět "{subject_name}" neexistuje.')

        await inter.response.send_message("Sending predictor embed message", delete_after=0)
        await predict_embed(subject_name, inter.channel, self.client)

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
        inter: ApplicationCommandInteraction[InteractionBot],
        subject_name: str,
    ) -> None:
        subject = SubjectsCache.tryGetSubjectByName(subject_name)
        if subject is None:
            return await inter.response.send_message(f'Předmět "{subject_name}" neexistuje.')

        average = Grades.db_grades().by_subject_name(subject_name).average()
        if average == None:
            return await inter.response.send_message(f'Pro předmět "{subject_name}" nemáte dosud žádné známky.')

        title = str(average)
        color = disnake.Color.from_rgb(0, 255, 255)
        embed = disnake.Embed(title=title, color=color)
        embed.set_author(name=f"Průměr z {subject.fullName}:")

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


def admin_user_check(inter: ApplicationCommandInteraction[InteractionBot]) -> bool:
    return inter.author.id == os_environ("adminID")


class Admin(CustomCog):
    group = commands.group(name="admin", description="Admin commands")

    async def updateScheduleDatabase(self, inter: ApplicationCommandInteraction[InteractionBot]) -> None:
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

    async def updateGradesDatabase(self, inter: ApplicationCommandInteraction[InteractionBot]) -> None:
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

    async def getSubjects(self, inter: ApplicationCommandInteraction[InteractionBot]) -> None:
        """Gets all cached subjects"""

        subjects = [f"{subject.shortOrFullName}: {subject.fullName}" for subject in SubjectsCache.subjects]
        await inter.send("\n".join(subjects))

    slashGetSubjects = commands.InvokableSlashCommand(
        getSubjects,
        name="get_subjects",
        description="Gets the subjects",
        checks=[admin_user_check],
        group=group,
    )


class Settings(CustomCog):
    featureManager: FeatureManager

    group = commands.group(name="settings", description="Edits the bot's settings")

    scheduleSettings = {"Show_day": "showDay", "show_classroom": "showClassroom"}

    async def scheduleSettingsCommand(
        self,
        inter: ApplicationCommandInteraction[InteractionBot],
        setting: str,
        bool: bool,
    ) -> None:
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
        inter: ApplicationCommandInteraction[InteractionBot],
        bool: bool,
    ) -> None:
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

    async def channel(self, inter: ApplicationCommandInteraction[InteractionBot], function: str) -> None:
        write_db(CHANNELS[function], inter.channel_id)
        await inter.response.send_message(f"channel `{function}` changed to this channel", ephemeral=True)

        isFunctionAFeature = function in FEATURES
        if isFunctionAFeature:
            await self.featureManager.maybe_start_feature(function, self.client)  # type: ignore[arg-type]

    slashChannel = commands.InvokableSlashCommand(
        channel,
        name="channel",
        description="Use this command in the channel where you want to have the bot's functions to send messages",
        checks=[admin_user_check],
        group=group,
        options=[
            disnake.Option(
                name="function",
                description="Select the function for this channel",
                choices=[disnake.OptionChoice(name=channel, value=channel) for channel in CHANNELS.keys()],
                type=disnake.OptionType.string,
                required=True,
            ),
        ],
    )

    async def setup(self, inter: ApplicationCommandInteraction[InteractionBot]) -> None:
        channelsToSetup = [channel for channel in CHANNELS.keys() if read_db(CHANNELS[channel]) is None]
        if len(channelsToSetup) == 0:
            await inter.response.send_message("All channels are already set up", ephemeral=True)
            return

        setupMessage = f"Setup the function channels for the bot with the following command in the desired channels:\n"
        setupMessage += "\n".join([f'"/channel function:{channel}"' for channel in channelsToSetup])

        await inter.response.send_message(setupMessage, ephemeral=True)

    slashSetup = commands.InvokableSlashCommand(
        setup,
        name="setup",
        description="Start the setup process",
        checks=[admin_user_check],
    )


COGS: list[commands.CogMeta] = [General, Admin, Settings]


def setupBotInteractions(client: commands.InteractionBot, featureManager: FeatureManager) -> None:
    """Sets up the bot's interactions (commands)"""
    for cog in COGS:
        client.add_cog(cog(client, featureManager))
