import asyncio
import copy
import datetime
import re

import discord
from utils.utils import MessageTimers, read_db, write_db

from core.betting import Betting
from core.grades import Grades
from core.predictor import Predictor
from core.schedule import Schedule


class Commands:
    def __init__(self, message: discord.Message, client: discord.Client):
        self.message = message
        self.client = client
        self.parse_message(message)

    def is_response_message(self, message: discord.Message):
        if message.channel.id in self.client.response_channel_cache:
            return True

    def parse_message(self, message: discord.Message):
        self.content = message.content
        self.channel = message.channel
        self.author = message.author

        self.isBaka = self.is_bakabot(self.message)
        self.isResponse = self.is_response_message(message)

        if self.isBaka:
            search = re.search("^(bakabot|b)($|\s)", self.content, flags=2)
            self.baka = search

            withoutBaka = self.content[search.span()[1] :]
            othersWithoutBaka = re.findall("[a-zěščřžýáíéóúůďťňĎŇŤŠČŘŽÝÁÍÉÚŮĚÓ0-9\-]+", withoutBaka, flags=2)
            self.command = othersWithoutBaka[0]

            self.arguments = othersWithoutBaka[1:]

    # Decides if the function was meant for BakaBot
    @staticmethod
    def is_bakabot(message: discord.Message):
        content = message.content
        if re.search("^(bakabot|b)($|\s)", content, flags=2):
            return True
        else:
            return False

    # Gets True or False from various forms out of a string
    @staticmethod
    def true_or_false_string(string: str):
        search = re.search(
            "^(1|pravda|ano|p|a|true|t|yes|y)|(0|[sšŠ]patn[eěĚ]|[sšŠ]|ne|n|false|f|no|nepravda)$", string, flags=2
        )
        if search:
            # True
            if search.group(1):
                return True
            # False
            else:
                return False
        else:
            return None

    class Help:
        GENERAL = 'Nedokázal jsem rozluštit váš příkaz.\nPužijte "BakaBot Help" pro nápovědu'

        blanc = "BakaBota zavoláž pomocí jeho jména pokračujíc mezerou funkcí mezerou a následnými argumenty.\nFunkce: Rozvrh; Settings, Známka"
        schedule = "Argumenty: den (začátek)-den (konec)"
        settings = "Špatný argument pro funkci Settings"

        ARGUMENTS = {"rozvrh": schedule, "schedule": schedule, "settings": settings}

        # Executes the method for of this function
        @classmethod
        async def execute(cls, message):
            # Check if the user inputed at least one argument
            if len(message.arguments) == 0:
                await message.channel.send(cls.blanc)
            else:
                argument = message.arguments[0]
                Commands.Help.ARGUMENTS.get(argument)
                response = Commands.COMMANDS.get(message.command)
                if response:
                    await message.channel.send(response)
                else:
                    await message.channel.send(Commands.Help.GENERAL)

    class Schedule:
        blanc = "Špatný argument pro funkci Rozvrh"

        # Executes the method for of this function
        @classmethod
        async def execute(cls, message):
            # Check if the user inputed at least one argument
            if len(message.arguments) == 0:
                await message.channel.send(cls.blanc)
            else:
                # Gets the parameters of the days to show in the schedule
                dayStartEndArg = message.arguments[0]
                dayStartEnd = re.search(
                    "^((([1-5])|(pond[eěĚ]l[iíÍ]|[uúÚ]ter[yýÝ]|st[rřŘ]eda|[cčČ]tvrtek|p[aáÁ]tek)|(p|[uúÚ]|s|[cčČ]|p))\-(([1-5])|(pond[eěĚ]l[iíÍ]|[uúÚ]ter[yýÝ]|st[rřŘ]eda|[cčČ]tvrtek|p[aáÁ]tek)|(p|[uúÚ]|s|[cčČ]|p))|(7|t|t[yýÝ]den)|(([1-5])|(pond[eěĚ]l[iíÍ]|[uúÚ]ter[yýÝ]|st[rřŘ]eda|[cčČ]tvrtek|p[aáÁ]tek)|(p|[uúÚ]|s|[cčČ]|p)))$",
                    dayStartEndArg,
                    flags=2,
                )
                # If the argument is valid
                if dayStartEnd:
                    # Gets if the week is the current or the next. Default is current week
                    if len(message.arguments) == 1:
                        nextWeek = False
                    else:
                        nextWeekArg = message.arguments[1]
                        search = re.search(
                            "^((1|2)|(aktu[aáÁ]ln[iíÍ]|p[rřŘ][iíÍ][sšŠ]t[iíÍ])|(a|p))$", nextWeekArg, flags=2
                        )
                        if search:
                            # If it's argumented by numbers
                            if search.group(2):
                                if nextWeekArg == "1":
                                    nextWeek = False
                                else:
                                    nextWeek = True
                            # If it's argumented by full name
                            elif search.group(3):
                                if re.search("aktu[aáÁ]ln[iíÍ]", nextWeekArg, flags=2):
                                    nextWeek = False
                                else:
                                    nextWeek = True
                            # If it's argumented by short name
                            else:
                                if nextWeekArg == "a":
                                    nextWeek = False
                                else:
                                    nextWeek = True
                        else:
                            await message.channel.send(f'{cls.blanc}: "{nextWeekArg}"')
                            return

                    # Checks if the argument is not a full week passed like a single word
                    if not dayStartEnd.group(10):
                        # Gets the int of the day from various forms out of a string
                        def get_day_int(string: str):
                            # If it's argumented by numbers
                            if re.search("\d", string):
                                return int(string)
                            # If it's argumented by full name
                            elif re.search(
                                "pond[eěĚ]l[iíÍ]|[uúÚ]ter[yýÝ]|st[rřŘ]eda|[cčČ]tvrtek|p[aáÁ]tek", string, flags=2
                            ):
                                if re.search("pond[eěĚ]l[iíÍ]", string, flags=2):
                                    return 1
                                elif re.search("[uúÚ]ter[yýÝ]", string, flags=2):
                                    return 2
                                elif re.search("st[rřŘ]eda", string, flags=2):
                                    return 3
                                elif re.search("[cčČ]tvrtek", string, flags=2):
                                    return 4
                                else:
                                    return 5
                            # If it's argumented by short name
                            else:
                                if re.search("p", string, flags=2):
                                    return 1
                                elif re.search("[uúÚ]", string, flags=2):
                                    return 2
                                elif re.search("s", string, flags=2):
                                    return 3
                                elif re.search("[cčČ]", string, flags=2):
                                    return 4
                                else:
                                    return 5

                        # If it's argumented as single day
                        if dayStartEnd.group(11):
                            dayStart = get_day_int(dayStartEnd.group(11))
                            dayEnd = dayStart
                        else:
                            # Finds the desired days from the argument
                            dayStart = get_day_int(dayStartEnd.group(2))
                            dayEnd = get_day_int(dayStartEnd.group(6))

                        # Gets the week with the desired days and sends it
                        await message.channel.send(file=await Schedule.db_schedule(nextWeek).render(dayStart, dayEnd))
                    else:
                        # Gets the full week and sends it
                        await message.channel.send(file=await Schedule.db_schedule(nextWeek).render(1, 5))
                else:
                    await message.channel.send(f'{cls.blanc}: "{dayStartEndArg}"')

    class Settings:
        blanc = "Špatný argument pro funkci Settings"

        # Executes the method for of this function
        @classmethod
        async def execute(cls, message):
            # Checks if the author is Patai5#4771
            if message.author.id == 335793327431483392:
                # Check if the user inputed at least one argument
                if len(message.arguments) == 0:
                    await message.channel.send(cls.blanc)
                else:
                    arg1 = message.arguments[0]
                    if arg1.lower() == "showday":
                        await cls.boolean_setting("showDay", message)
                    elif arg1.lower() == "showclassroom":
                        await cls.boolean_setting("showClassroom", message)
                    elif arg1.lower() == "channelschedule":
                        await cls.channel_setting("channelSchedule", message)
                    elif arg1.lower() == "channelgrades":
                        await cls.channel_setting("channelGrades", message)
                    elif arg1.lower() == "channelreminder":
                        await cls.channel_setting("channelReminder", message)
                    elif arg1.lower() == "channelstatus":
                        await cls.channel_setting("channelStatus", message)
                    else:
                        await message.channel.send(f'{cls.blanc}: "{arg1}"')
            else:
                await message.channel.send("Můj majitel je Patai5 ty mrdko!")

        # Writes to database for boolean type settings
        @classmethod
        async def boolean_setting(cls, dbName: str, message):
            if len(message.arguments) > 1:
                trueFalse = Commands.true_or_false_string(message.arguments[1])
                if trueFalse != None:
                    await message.channel.send(f'Setting {dbName} changed to "{trueFalse}"')
                else:
                    await message.channel.send(f'{cls.blanc}: "{message.arguments[1]}"')
                write_db(dbName, trueFalse)
            else:
                await message.channel.send(cls.blanc)

        # Writes to database for discord channel settings
        @classmethod
        async def channel_setting(cls, dbName: str, message):
            write_db(dbName, message.channel.id)
            await message.channel.send(f'"{dbName}" changed to this channel')

    class Admin:
        blanc = "Špatný argument pro funkci Admin"

        # Executes the method for of this function
        @classmethod
        async def execute(cls, message):
            # Checks if the author is Patai5#4771
            if message.author.id == 335793327431483392:
                # Check if the user inputed at least one arguments
                if len(message.arguments) == 0:
                    await message.channel.send(cls.blanc)
                else:
                    arg1 = message.arguments[0]
                    if arg1.lower() == "forceupdatescheduledatabase":
                        schedule1 = await Schedule.get_schedule(False, message.client)
                        schedule2 = await Schedule.get_schedule(True, message.client)
                        if schedule1 is None or schedule2 is None:
                            await message.channel.send("Bakalari's server is currently down.")
                        else:
                            write_db("schedule1", Schedule.json_dumps(schedule1))
                            write_db("schedule2", Schedule.json_dumps(schedule2))
                            await message.channel.send("Updated schedule database")
                    elif arg1.lower() == "forceupdategradesdatabase":
                        grades = await Grades.get_grades(message.client)
                        if grades is None:
                            await message.channel.send("Bakalari's server is currently down.")
                        else:
                            write_db("grades", Grades.json_dumps(grades))
                            await message.channel.send("Updated grades database")
                    elif arg1.lower() == "forcenewweek":
                        await Schedule.new_week_message(
                            Schedule.db_schedule(), Schedule.db_schedule(True), message.client
                        )
                    else:
                        await message.channel.send(f'{cls.blanc}: "{arg1}"')
            else:
                await message.channel.send("Můj majitel je Patai5 ty mrdko!")

    class Grades:
        blanc = "Špatný argument pro funkci Známka"

        # Executes the method for of this function
        @classmethod
        async def execute(cls, message):
            # Check if the user inputed at least one arguments
            if len(message.arguments) == 0:
                await message.channel.send(cls.blanc)
            else:
                arg1 = message.arguments[0]
                if re.search("^(Inf|EvV|EvH|Zsv|[cčČ]j|Fj|Tv|Aj|M|Bi|Fy|Ch|D|Z)$", arg1, flags=2):
                    arg1 = arg1.lower().replace("c", "Č")
                    await Predictor.predict_embed(arg1, message.channel, message.client)
                else:
                    await message.channel.send(f'{cls.blanc}: "{arg1}"')

    COMMANDS = {
        "r": Schedule,
        "rozvrh": Schedule,
        "s": Schedule,
        "schedule": Schedule,
        "help": Help,
        "setting": Settings,
        "settings": Settings,
        "admin": Admin,
        "grade": Grades,
        "znamka": Grades,
        "známka": Grades,
    }

    # Executes the message's command
    async def execute(self):
        if self.isBaka:
            command = self.COMMANDS.get(self.command.lower())
            if command:
                await command.execute(self)
            else:
                await self.Help.execute(self)
        elif self.isResponse:
            await Responses(self.message, self.client).execute()


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
                        editedFromNowSec = (datetime.datetime.utcnow() - message.edited_at).seconds
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
                        createdFromNowSec = (datetime.datetime.utcnow() - message.created_at).seconds
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
                    createdFromNowSec = (datetime.datetime.utcnow() - message.created_at).seconds
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
                    createdFromNowSec = (datetime.datetime.utcnow() - message.created_at).seconds
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


class Responses(Commands):
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

                    createdFromNowSec = (datetime.datetime.utcnow() - message.created_at).seconds
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
