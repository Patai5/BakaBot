import re

import discord
from utils.utils import write_db

from core.grades import Grades
from core.schedule import Schedule


class Commands:
    def __init__(self, message: discord.Message, client: discord.Client):
        self.message = message
        self.client = client

        if not Commands.is_bakabot(message):
            return None
        self.parse_message(message)

    def parse_message(self, message: discord.Message):
        self.content = message.content
        self.channel = message.channel
        self.author = message.author

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

        blanc = "BakaBota zavoláž pomocí jeho jména pokračujíc mezerou funkcí mezerou a následnými argumenty.\nFunkce: Rozvrh; Settings"
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
                        schedule = (await Schedule.db_schedule(nextWeek)).show(dayStart, dayEnd)
                        await message.channel.send(f"```{schedule}```")
                    else:
                        # Gets the full week and sends it
                        schedule = (await Schedule.db_schedule(nextWeek)).show(1, 5)
                        await message.channel.send(f"```{schedule}```")
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
                        schedule1 = Schedule.get_schedule(False)
                        schedule2 = Schedule.get_schedule(True)
                        write_db("schedule1", Schedule.json_dumps(schedule1))
                        write_db("schedule2", Schedule.json_dumps(schedule2))
                        response = "Updated schedule database"
                        await message.channel.send(response)
                    elif arg1.lower() == "forceupdategradesdatabase":
                        grades = Grades.get_grades()
                        write_db("grades", Grades.json_dumps(grades))
                        response = "Updated grades database"
                        await message.channel.send(response)
                    else:
                        await message.channel.send(f'{cls.blanc}: "{arg1}"')
            else:
                await message.channel.send("Můj majitel je Patai5 ty mrdko!")

    COMMANDS = {
        "r": Schedule,
        "rozvrh": Schedule,
        "s": Schedule,
        "schedule": Schedule,
        "help": Help,
        "setting": Settings,
        "settings": Settings,
        "admin": Admin,
    }

    # Executes the message's command
    async def execute(self):
        command = self.COMMANDS.get(self.command.lower())
        if command:
            await command.execute(self)
        else:
            await self.Help.execute(self)
