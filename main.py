import asyncio
import copy
import datetime
import json
import os
import re
import time

import discord
import requests
from bs4 import BeautifulSoup
from replit import db

from keep_alive import keep_alive


def main():
    keep_alive()
    client = discord.Client()

    @client.event
    async def on_ready():
        print("Ready!")
        await client.change_presence(activity=discord.Activity(name="Bakaláři", type=3))
        reminder_task = asyncio.create_task(createReminder(client))
        rozvrhchange_task = asyncio.create_task(rozvrhchange(client))
        await reminder_task
        await rozvrhchange_task

    @client.event
    async def on_message(message):
        if not message.author.bot:
            await botcommands(message, client)

    token = os.environ["token"]
    client.run(token)


async def botcommands(message, client):
    async def gethelp(function=""):
        general = 'Nedokázal jsem rozluštit váš příkaz.\nPužijte "BakaBot Help" pro nápovědu'
        rozvrhhelp = (
            "Špatný argument pro funkci Rozvrh\nBakaBot Rozvrh den(jeden den(DEN)|více dní(DEN-DEN)|celý "
            'týden(TÝDEN)) ?příští(jaký týden(PŘÍŠTÍ))\nDEN = "pondělí|monday|1", DEN-DEN = '
            '"DEN-DEN|týden|week", PŘÍŠTÍ = "příští|aktuální|now|next|1|2" '
        )
        settingshelp = (
            "ShowDen (bool)\nShowTrida (bool)\nChannelZmeneno (message channel)\n"
            "ChannelZnamky (message channel)\nChannelHodiny (message channel)"
        )

        if function == "rozvrhhelp":
            await message.channel.send(rozvrhhelp)
        elif function == "settings":
            await message.channel.send(settingshelp)
        else:
            await message.channel.send(general)

    async def settings(message, command):
        if message.author.id == 335793327431483392:
            command = command.replace("settings ", "").replace("setting ", "")
            args = command.split(" ")[:3]
            if len(args) != 2:
                args.insert(1, "")
            if args[0].lower().startswith("showden"):
                if re.match("(true|ano|1)", args[1].lower()):
                    db["showden"] = True
                    await message.channel.send("showden = True")
                elif re.match("(false|ne|0)", args[1].lower()):
                    db["showden"] = False
                    await message.channel.send("showden = False")
                else:
                    await gethelp("settings")
            elif args[0].lower().startswith("showtrida"):
                if re.match("(true|ano|1)", args[1].lower()):
                    db["showtrida"] = True
                    await message.channel.send("showtrida = True")
                elif re.match("(false|ne|0)", args[1].lower()):
                    db["showtrida"] = False
                    await message.channel.send("showtrida = False")
                else:
                    await gethelp("settings")
            elif args[0].lower().startswith("channelzmeneno"):
                db["channelZmeneno"] = message.channel.id
                await message.channel.send("channelZmeneno = This channel")
            elif args[0].lower().startswith("channelznamky"):
                db["channelZnamky"] = message.channel.id
                await message.channel.send("channelZnamky = This channel")
            elif args[0].lower().startswith("channelhodiny"):
                db["channelHodiny"] = message.channel.id
                await message.channel.send("channelHodiny = This channel")
            else:
                await gethelp("settings")
        else:
            await message.channel.send("Můj majitel je Patai5 ty mrdko!")

    async def rozvrh(message, command):
        if re.search("^rozvrh", command.lower()):
            command = command.replace("rozvrh ", "")
        else:
            command = command.replace("r ", "")
        args = command.split(" ")[:2]
        if len(args) != 2:
            args.insert(1, "1")
        daystart = 0
        dayend = 0
        nextweek = False
        crashed = False
        if re.search("-", args[0].lower()):
            daystart, dayend = args[0].split("-")[:2]
            daystart = daystart.lower()
            dayend = dayend.lower()
            crashed = False
            if re.match("(pond[ěe]l[íi]|monday|1)", daystart):
                daystart = 1
            elif re.match("([úu]ter[ýy]|tuesday|2)", daystart):
                daystart = 2
            elif re.match("(st[řr]eda|wednesday|3)", daystart):
                daystart = 3
            elif re.match("([čc]]tvrtek|thursday|4)", daystart):
                daystart = 4
            elif re.match("(p[áa]tek|friday|5)", daystart):
                daystart = 5
            else:
                crashed = True
                await gethelp("rozvrhhelp")
            if not crashed:
                if re.match("(pond[ěe]l[íi]|monday|1)", dayend):
                    dayend = 1
                elif re.match("([úu]ter[ýy]|tuesday|2)", dayend):
                    dayend = 2
                elif re.match("(st[řr]eda|wednesday|3)", dayend):
                    dayend = 3
                elif re.match("([čc]]tvrtek|thursday|4)", dayend):
                    dayend = 4
                elif re.match("(p[áa]tek|friday|5)", dayend):
                    dayend = 5
                else:
                    crashed = True
                    await gethelp("rozvrhhelp")
        else:
            if re.match("(t[ýy]den|week|0|7|t)", args[0]):
                daystart = 1
                dayend = 5
            elif re.match("(pond[ěe]l[íi]|monday|1)", args[0]):
                daystart = 1
                dayend = 1
            elif re.match("([úu]ter[ýy]|tuesday|2)", args[0]):
                daystart = 2
                dayend = 2
            elif re.match("(st[řr]eda|wednesday|3)", args[0]):
                daystart = 3
                dayend = 3
            elif re.match("([čc]]tvrtek|thursday|4)", args[0]):
                daystart = 4
                dayend = 4
            elif re.match("(p[áa]tek|friday|5)", args[0]):
                daystart = 5
                dayend = 5
            else:
                crashed = True
                await gethelp("rozvrhhelp")
        if args[1]:
            if re.match("(aktu[áa]ln[íi]|now|1)", args[1]):
                nextweek = False
            elif re.match("(p[řr][íi][šs]t[íi]|next|2)", args[1]):
                nextweek = True
            else:
                crashed = True
                await gethelp("rozvrhhelp")
        if not crashed:
            zprava = rozvrhshow(daystart, dayend, nextweek)
            await message.channel.send(zprava)

    async def forceUpdateLessonDatabase(message):
        rozvrh1 = getrozvrh(False)
        rozvrh2 = getrozvrh(True)
        db["rozvrh1"] = jsondumps(rozvrh1)
        db["rozvrh2"] = jsondumps(rozvrh2)
        zprava = "Updated lesson database"
        await message.channel.send(zprava)

    async def forceUpdateZnamkyDatabase(message):
        znamky = getznamky()
        db["znamky"] = jsondumpsZnamky(znamky)
        zprava = "Updated znamky database"
        await message.channel.send(zprava)

    if re.search("^([ -/]*?[Bb][Aa][Kk][Aa][Bb][Oo][Tt]|[ -/]*?[Bb])", message.content):
        if re.search("^[ -/]*?[Bb][Aa][Kk][Aa][Bb][Oo][Tt]", message.content):
            command = re.split("^[ -/]*?[Bb][Aa][Kk][Aa][Bb][Oo][Tt] ", message.content)[1]
        else:
            command = re.split("^[ -/]*?[Bb] ", message.content)[1]
        if re.search("^(rozvrh|r)", command.lower()):
            await rozvrh(message, command)
        elif command.lower().startswith("setting"):
            await settings(message, command)
        elif command.lower().startswith("forceupdatelessondatabase"):
            await forceUpdateLessonDatabase(message)
        elif command.lower().startswith("forceupdateznamkydatabase"):
            await forceUpdateZnamkyDatabase(message)
        elif command.lower().startswith("help"):
            await gethelp(command.split(" ")[0])
        else:
            await gethelp()


class Lesson:
    def __init__(self, hodina, predmet, trida, changeinfo=None):
        self.hodina = hodina
        self.predmet = predmet
        self.trida = trida
        self.changeinfo = changeinfo


class Day:
    def __init__(self, lessons, den, prazdny):
        self.lessons = lessons
        self.den = den
        self.prazdny = prazdny


class Rozvrh:
    def __init__(self, days, pristi):
        self.days = days
        self.pristi = pristi


def getrozvrh(nextweek):
    url = "https://bakalari.ceskolipska.cz/Login"
    session = login(url)
    if nextweek:
        result = session.get("https://bakalari.ceskolipska.cz/next/rozvrh.aspx?s=next")
    else:
        result = session.get("https://bakalari.ceskolipska.cz/next/rozvrh.aspx")
    session.close()

    html = BeautifulSoup(result.text, "html.parser")
    days = html.find_all("div", {"class": "day-row"})
    for i, day in enumerate(days):
        lessons = day.div.div.find_all("div", {"class": "day-item"})
        prazdny = False
        if not lessons:
            prazdny = True
            for i2 in range(13):
                lessons.append(Lesson(i2, " ", " "))
        else:
            for i2, lesson in enumerate(lessons):
                data = lesson.find_all("div", {"class": "day-item-hover"})
                changeInfo = re.findall('(?<="changeinfo":").*?(?=")', str(data))
                if changeInfo:
                    changeInfo = changeInfo[0]
                    if "Suplování" in changeInfo:
                        teacherDiv = lesson.find("div", {"class": "bottom"})
                        teacher = re.findall("(?<=>).*(?=</)", str(teacherDiv))[0]
                        changeInfo += " --> " + teacher
                else:
                    changeInfo = re.findall('(?<="removedinfo":").*?(?=")', str(data))
                    if changeInfo:
                        changeInfo = changeInfo[0]
                if changeInfo == "":
                    changeInfo = None

                name = lesson.find("div", {"class": "middle"})
                if name:
                    reg = re.findall("(?<=>).*(?=</)", str(name))[0]
                    if reg != "":
                        data = lesson.find_all("div", {"class": "day-item-hover"})
                        reg2 = re.findall('(?<="room":").*?(?=")', str(data))
                        if reg2:
                            reg2 = reg2[0]
                        else:
                            reg2 = " "

                        lessons[i2] = Lesson(i2, reg, reg2, changeInfo)
                    else:
                        lessons[i2] = Lesson(i2, " ", " ", changeInfo)
                else:
                    lessons[i2] = Lesson(i2, " ", " ", changeInfo)
        lessons.pop(6)
        for i2, lesson in enumerate(lessons):
            lessons[i2] = Lesson(i2, lesson.predmet, lesson.trida, lesson.changeinfo)
        daynazev = day.div.div.div.div
        daynazev = re.findall("(?<=<div>)\s*?(..)(?=<br/>)", str(daynazev))[0]
        if prazdny:
            days[i] = Day(lessons, daynazev, True)
        else:
            days[i] = Day(lessons, daynazev, False)
    rozvrh = Rozvrh(days, nextweek)
    return rozvrh


def rozvrhshow(daystart, dayend, nextweek=False, showden=None, showtrida=None, exclusives=None, rozvrh=None):
    if showden == None:
        showden = readdb("showden")
        if showden == None:
            showden = False
    if showtrida == None:
        showtrida = readdb("showtrida")
        if showtrida == None:
            showtrida = False

    if not rozvrh:
        rozvrh = getrozvrh(nextweek)
    rozvrh.days = rozvrh.days[daystart - 1 : dayend]

    neprazdnyDen = None
    for i, day in enumerate(rozvrh.days):
        if not day.prazdny:
            neprazdnyDen, startNeprazdnyDen = day, i
            break
    if neprazdnyDen:
        lowest = 0
        for i, lesson in enumerate(rozvrh.days[startNeprazdnyDen].lessons):
            if lesson.predmet != " ":
                lowest = i
                break
        for day in rozvrh.days:
            if not day.prazdny:
                largest = 0
                for i, lesson in enumerate(day.lessons):
                    if lesson.predmet != " ":
                        if largest < i:
                            largest = i
                        break
                if lowest > largest:
                    lowest = largest
        for day in rozvrh.days:
            if not day.prazdny:
                day.lessons = day.lessons[lowest:]

        lowest = 0
        for i, lesson in enumerate(reversed(rozvrh.days[startNeprazdnyDen].lessons)):
            if lesson.predmet != " ":
                lowest = i
                break
        for day in rozvrh.days:
            if not day.prazdny:
                largest = 0
                for i, lesson in enumerate(reversed(day.lessons)):
                    if lesson.predmet != " ":
                        if largest < i:
                            largest = i
                        break
                if lowest > largest:
                    lowest = largest
        for day in rozvrh.days:
            if not day.prazdny:
                if lowest == 0:
                    lowest = 1
                day.lessons = day.lessons[:-lowest]
        if exclusives:
            columns = []
            if showden:
                column = [ColumnItem(" ", True)]
                for day in rozvrh.days:
                    if showtrida:
                        column.append(ColumnItem(day.den, False))
                        column.append(ColumnItem(" ", True))
                    else:
                        column.append(ColumnItem(day.den, True))
                columns.append(column)
            for i in range(len(rozvrh.days[0].lessons)):
                column = [ColumnItem(str(rozvrh.days[0].lessons[i].hodina) + ".", True)]
                for day_i, day in enumerate(rozvrh.days):
                    if showtrida:
                        column.append(
                            ColumnItem(day.lessons[i].predmet, False, exclusives[day_i][day.lessons[i].hodina])
                        )
                        column.append(ColumnItem(day.lessons[i].trida, True, exclusives[day_i][day.lessons[i].hodina]))
                    else:
                        column.append(
                            ColumnItem(day.lessons[i].predmet, True, exclusives[day_i][day.lessons[i].hodina])
                        )
                columns.append(column)
            output = "```" + table(columns) + "```"
        else:
            columns = []
            if showden:
                column = [ColumnItem(" ", True)]
                for day in rozvrh.days:
                    if showtrida:
                        column.append(ColumnItem(day.den, False))
                        column.append(ColumnItem(" ", True))
                    else:
                        column.append(ColumnItem(day.den, True))
                columns.append(column)
            for i in range(len(rozvrh.days[0].lessons)):
                column = [ColumnItem(str(rozvrh.days[0].lessons[i].hodina) + ".", True)]
                for day in rozvrh.days:
                    if showtrida:
                        column.append(ColumnItem(day.lessons[i].predmet, False))
                        column.append(ColumnItem(day.lessons[i].trida, True))
                    else:
                        column.append(ColumnItem(day.lessons[i].predmet, True))
                columns.append(column)
            output = "```" + table(columns) + "```"
        return output
    else:
        return "```V rozvrhu nic není```"


def login(url):
    username = os.environ["username"]
    password = os.environ["password"]
    data = {"username": username, "password": password}
    session = requests.Session()
    session.post(url, data)
    return session


def repeat(char, times):
    string = ""
    for i in range(times):
        string = string + char
    return string


def spaceout(string, spaces):
    output = ""
    spaces2int = int((spaces - len(string)) / 2)
    spaces2float = (spaces - len(string)) / 2
    if spaces2int != 0:
        output = repeat(" ", spaces2int)
    if spaces2float != spaces2int:
        if string.endswith("."):
            output = output + " " + string
        else:
            output = output + string + " "
    else:
        output = output + string
    if spaces2int != 0:
        output = output + repeat(" ", spaces2int)
    return output


class ColumnItem:
    def __init__(self, value, newline, exclusive=False):
        self.value = value
        self.newline = newline
        self.exclusive = exclusive


def table(columns):
    rows = []
    rowsint = 2
    for item in columns[0]:
        if item.newline:
            rowsint = rowsint + 2
        else:
            rowsint = rowsint + 1
    for row in range(rowsint):
        rows.append("")

    for column_i, column in enumerate(columns):
        longest = 0
        for item in column:
            if len(item.value) > longest:
                longest = len(item.value)
        for i in range(len(column)):
            column[i].value = spaceout(column[i].value, longest)

        rows[0] = rows[0] + repeat("═", longest + 2) + "╤"
        z = 1
        for i, item in enumerate(column):
            if item.exclusive:
                rows[z] = rows[z] + " " + item.value + " " + "║"
            elif len(columns) > column_i + 1:
                if columns[column_i + 1][i].exclusive:
                    rows[z] = rows[z] + " " + item.value + " " + "║"
                else:
                    rows[z] = rows[z] + " " + item.value + " " + "│"
            else:
                rows[z] = rows[z] + " " + item.value + " " + "│"
            if item.newline:
                if i != len(column) - 1:
                    z = z + 1
                    if item.exclusive or column[i + 1].exclusive:
                        rows[z] = rows[z] + repeat("═", longest + 2) + "●"
                    elif len(columns) > column_i + 1:
                        if columns[column_i + 1][i].exclusive:
                            rows[z] = rows[z] + repeat("─", longest + 2) + "●"
                        elif columns[column_i + 1][i + 1].exclusive:
                            rows[z] = rows[z] + repeat("─", longest + 2) + "●"
                        else:
                            rows[z] = rows[z] + repeat("─", longest + 2) + "┼"
                    else:
                        rows[z] = rows[z] + repeat("─", longest + 2) + "┼"
            z = z + 1
        rows[z] = rows[z] + repeat("═", longest + 2) + "╧"

    for i in range(len(rows)):
        if i == 0:
            rows[i] = "╔" + rows[i][:-1] + "╗"
        elif i == len(rows) - 1:
            rows[i - 1] = "╚" + rows[i - 1][:-1] + "╝"
    z = 0
    for i, item in enumerate(columns[0]):
        z = z + 1
        if item.newline:
            rows[z] = "║" + rows[z][:-1] + "║"
            if z == len(rows) - 3:
                break
            z = z + 1
            rows[z] = "╟" + rows[z][:-1] + "╢"
        else:
            rows[z] = "║" + rows[z][:-1] + "║"

    output = ""
    for row in rows:
        output = output + row + "\n"
    return output


def readdb(name):
    if len(db.prefix(name)) == 0:
        return None
    else:
        return db[name]


def getSec():
    timeX = time.localtime()
    sec = timeX.tm_hour * 3600 + timeX.tm_min * 60 + timeX.tm_sec + time.timezone + 3600
    return sec


def from_sec_to_time(sec: int):
    hour = int(sec / 3600)
    min = int((sec - hour * 3600) / 60)
    sec = sec - hour * 3600 - min * 60

    if min < 10:
        minPrint = "0" + str(min)
    else:
        minPrint = min
    output = str(hour) + ":" + str(minPrint)
    return output


REMIND = [21600, 26100, 29400, 32700, 36600, 39900, 43200, 46500, 47700, 51000, 54000, 57000, 60000]
LESSON_TIMES = [
    [25500, 28200],
    [28800, 31500],
    [32100, 34800],
    [36000, 38700],
    [39300, 42000],
    [42600, 45300],
    [45900, 48600],
    [47100, 49800],
    [50400, 53100],
    [53400, 56100],
    [56100, 59100],
    [59400, 62100],
]


async def createReminder(client):
    weekday = datetime.datetime.today().weekday()
    if weekday == 4 and getSec() > REMIND[-1]:
        when = 86400 - getSec() + 172800 + REMIND[0]
        await reminder(client, when)
    elif weekday == 5:
        when = 86400 - getSec() + 86400 + REMIND[0]
        await reminder(client, when)
    elif weekday == 6:
        when = 86400 - getSec() + REMIND[0]
        await reminder(client, when)
    else:
        lesson = get_next_lesson_for_reminder()
        if lesson:
            for remindTime in REMIND:
                if remindTime > getSec():
                    when = remindTime - getSec()
                    break
            await reminder(client, when)
        else:
            when = 86400 - getSec() + REMIND[0]
            await reminder(client, when)


def get_next_lesson_for_reminder(current=None):
    rozvrh = jsonloads(db["rozvrh1"])
    todayDayInt = datetime.datetime.today().weekday()
    day = rozvrh.days[todayDayInt]

    outputLesson = None
    currentTimeSec = getSec()
    for lesson in day.lessons:
        if current:
            if REMIND[lesson.hodina] > currentTimeSec - 10:
                if lesson.predmet != " ":
                    outputLesson = lesson
                    break
        else:
            if REMIND[lesson.hodina] > currentTimeSec:
                if lesson.predmet != " ":
                    outputLesson = lesson
                    break
    return outputLesson


async def reminder(client, when):
    await asyncio.sleep(when)

    channel = db["channelHodiny"]
    embed = discord.Embed()
    lesson = get_next_lesson_for_reminder(current=True)
    if lesson:
        hodina, predmet, trida = db["lastLesson"]
        lastLesson = Lesson(hodina, predmet, trida)
        if (
            lesson.hodina != lastLesson.hodina
            or lesson.predmet != lastLesson.predmet
            or lesson.trida != lastLesson.trida
        ):
            column = [ColumnItem(lesson.predmet, False), ColumnItem(lesson.trida, True)]
            predmet = "```" + table([column]) + "```"
            time1 = from_sec_to_time(LESSON_TIMES[lesson.hodina][0])
            time2 = from_sec_to_time(LESSON_TIMES[lesson.hodina][1])
            lessonHodina = time1 + " - " + time2
            embed.add_field(name=lessonHodina, value=predmet)
            await client.get_channel(channel).send(embed=embed)
            db["lastLesson"] = [lesson.hodina, lesson.predmet, lesson.trida]
    await asyncio.sleep(1)
    await createReminder(client)


def jsondumps(rozvrh):
    output = '{"days": ['
    for day in rozvrh.days:
        output = output + '{"lessons": ['
        for lesson in day.lessons:
            output = output + json.dumps(lesson.__dict__) + ", "
        output = output[:-2] + "]"
        output = output + ', "den": "' + day.den + '", "prazdny": ' + str(day.prazdny).lower() + "}, "
    output = output[:-2] + "]"
    output = output + ', "pristi": ' + str(rozvrh.pristi).lower() + "}"
    return output


def jsonloads(jsonstring):
    dictRozvrh = json.loads(jsonstring)
    days = []
    for day in dictRozvrh["days"]:
        lessons = []
        for lesson in day["lessons"]:
            lessons.append(Lesson(lesson["hodina"], lesson["predmet"], lesson["trida"], lesson["changeinfo"]))
        days.append(Day(lessons, day["den"], day["prazdny"]))
    rozvrh = Rozvrh(days, dictRozvrh["pristi"])
    return rozvrh


async def rozvrhchange(client):
    def detectchange(rozvrhOld, rozvrhNew):
        changedlist = []
        for (dayOld, dayNew) in zip(rozvrhOld.days, rozvrhNew.days):
            for (lessonOld, lessonNew) in zip(dayOld.lessons, dayNew.lessons):
                changed = lessonOld, lessonNew, dayOld.den
                if (
                    lessonOld.predmet != lessonNew.predmet
                    or lessonOld.trida != lessonNew.trida
                    or lessonOld.changeinfo != lessonNew.changeinfo
                ):
                    changedlist.append(changed)
        if len(changedlist) != 0:
            return changedlist
        else:
            return None

    async def zmenenomessage(changed, tyden, client, rozvrh):
        def zmenapredmet(lessonOld, lessonNew):
            column = []
            column.append(ColumnItem(lessonOld.predmet, False))
            column.append(ColumnItem(lessonOld.trida, True))
            lessonOldTable = table([column])

            column = []
            column.append(ColumnItem(lessonNew.predmet, False))
            column.append(ColumnItem(lessonNew.trida, True))
            lessonNewTable = table([column])

            tableListOld = lessonOldTable.split("\n")
            tableListNew = lessonNewTable.split("\n")
            output = "```"
            for rowOld, rowNew, i in zip(tableListOld, tableListNew, range(4)):
                if i != 2:
                    output = output + rowOld + "     " + rowNew
                else:
                    output = output + rowOld + " --> " + rowNew
                output = output + "\n"
            output = output + "```"
            return output

        channel = db["channelZmeneno"]
        embed = discord.Embed()
        embed.title = "Detekována změna v rozvrhu"
        for changedItem in changed:
            if len(embed.fields) >= 23:
                embed.add_field(
                    name="Maximální počet embedů v jedné zprávě vyplýtván",
                    value="Asi Hrnec změnil hodně " "předmětů najednou :(",
                    inline=True,
                )
                embed.add_field(name="\u200b", value="\u200b", inline=False)
                break
            lessonOld, lessonNew, den = changedItem
            nazev = ""
            if tyden:
                nazev = "Příští týden, "
            else:
                nazev = "Tento týden, "
            nazev = nazev + den + ", " + str(lessonOld.hodina) + ". hodina"
            obsah = zmenapredmet(lessonOld, lessonNew)
            embed.add_field(name=nazev, value=obsah, inline=True)

            if lessonNew.changeinfo:
                nazev = "Change info"
                obsah = lessonNew.changeinfo
                embed.add_field(name=nazev, value=obsah, inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.remove_field(len(embed.fields) - 1)
        embed.color = discord.Color.from_rgb(200, 36, 36)
        await client.get_channel(channel).send(embed=embed)

        exclusives = [[False for i in range(12)] for i in range(5)]
        for item in changed:
            if item[2] == "po":
                den = 0
            elif item[2] == "út":
                den = 1
            elif item[2] == "st":
                den = 2
            elif item[2] == "čt":
                den = 3
            elif item[2] == "pá":
                den = 4
            exclusives[den][item[1].hodina] = True
        rozvrhToShow = rozvrhshow(
            1, 5, nextweek=tyden, showden=True, showtrida=True, exclusives=exclusives, rozvrh=copy.deepcopy(rozvrh)
        )
        await client.get_channel(channel).send(rozvrhToShow)

    await znamkychange(client)
    if len(db.prefix("rozvrh1")) == 0:
        rozvrh1 = getrozvrh(False)
        rozvrh2 = getrozvrh(True)
        db["rozvrh1"] = jsondumps(rozvrh1)
        db["rozvrh2"] = jsondumps(rozvrh2)
    else:
        change = False
        rozvrhNew1 = getrozvrh(False)
        rozvrhNew2 = getrozvrh(True)
        rozvrhOld1 = jsonloads(db["rozvrh1"])
        rozvrhOld2 = jsonloads(db["rozvrh2"])
        changed = detectchange(rozvrhOld1, rozvrhNew1)
        if changed:
            await zmenenomessage(changed, False, client, rozvrhNew1)
            change = True
        changed = detectchange(rozvrhOld2, rozvrhNew2)
        if changed:
            await zmenenomessage(changed, True, client, rozvrhNew2)
            change = True
        if change:
            db["rozvrh1"] = jsondumps(rozvrhNew1)
            db["rozvrh2"] = jsondumps(rozvrhNew2)
    await asyncio.sleep(60)
    await rozvrhchange(client)


def jsondumpsZnamky(znamky):
    output = '{"znamky": ['
    for znamka in znamky.znamky:
        output = output + json.dumps(znamka.__dict__) + ", "
    output = output[:-2] + "]}"

    return output


def jsonloadsZnamky(jsonstring):
    dictZnamky = json.loads(jsonstring)
    znamky = []
    for znamka in dictZnamky["znamky"]:
        znamky.append(
            Znamka(
                znamka["id"],
                znamka["caption"],
                znamka["predmet"],
                znamka["vaha"],
                znamka["poznamka"],
                znamka["date"],
                znamka["znamka"],
            )
        )
    znamky = Znamky(znamky)
    return znamky


class Znamky:
    def __init__(self, znamky):
        self.znamky = znamky

    def byPredmet(self, predmet):
        znamkyByPremdet = []
        for znamka in self.znamky:
            if znamka.predmet == predmet:
                znamkyByPremdet.append(znamka)
        return Znamky(znamkyByPremdet)

    def prumer(self):
        totalNumberZnamek = 0
        totalZnamka = 0
        for znamka in self.znamky:
            totalNumberZnamek += znamka.vaha
            totalZnamka += znamka.znamka * znamka.vaha
        return self.roundPrumer(totalZnamka / totalNumberZnamek)

    def budouciPrumer(self):
        self.znamky.append(Znamka(*[None for i in range(3)], 12, *[None for i in range(2)], 5))
        nejhorsi = self.roundPrumer(self.prumer())
        self.znamky.pop(-1)
        self.znamky.append(Znamka(*[None for i in range(3)], 12, *[None for i in range(2)], 1))
        nejlepsi = self.roundPrumer(self.prumer())
        self.znamky.pop(-1)
        return f"{nejhorsi} - {nejlepsi}"

    @staticmethod
    def roundPrumer(float):
        if float % 1 == 0:
            return int(float)
        if float % 10 == 0:
            return int(float * 10) / 10
        else:
            return int(float * 100) / 100


class Znamka:
    def __init__(self, id, caption, predmet, vaha, poznamka, date, znamka):
        self.id = id
        self.caption = caption
        self.predmet = predmet
        self.vaha = vaha
        self.poznamka = poznamka
        self.date = date
        self.znamka = znamka

    def znamkaString(self):
        if self.znamka % 1 != 0:
            return str(int(self.znamka)) + "-"
        else:
            return str(int(self.znamka))

    def print(self):
        return (
            f"ID: {self.id}; Caption: {self.caption}; Predmet: {self.predmet}; Vaha: {self.vaha}; Poznamka: "
            f"{self.poznamka}; Date: {self.date}; Znamka: {self.znamka}"
        )


PREDMETY = {
    "Inf": "Informatika a výpočetní technika",
    "EvV": "Estetická výchova - výtvarná",
    "EvH": "Estetická výchova - hudební",
    "Zsv": "Základy společenských věd",
    "Čj": "Český jazyk a literatura",
    "Fj": "Jazyk francouzský",
    "Tv": "Tělesná výchova",
    "Aj": "Jazyk anglický",
    "M": "Matematika",
    "Bi": "Biologie",
    "Fy": "Fyzika",
    "Ch": "Chemie",
    "D": "Dějepis",
    "Z": "Zeměpis",
}

PREDMETYNAOPAK = {}
for key, value in zip(PREDMETY.keys(), PREDMETY.values()):
    PREDMETYNAOPAK.update({value: key})


def getznamky():
    url = "https://bakalari.ceskolipska.cz/Login"
    session = login(url)
    result = session.get("https://bakalari.ceskolipska.cz/next/prubzna.aspx?s=chrono")
    session.close()

    html = BeautifulSoup(result.text, "html.parser")
    data = html.find("div", {"id": "cphmain_DivByTime"}).script.text
    data = re.findall("\[\{.*?(?=;)", data)[0]

    znamky = Znamky([])
    dictData = json.loads(data)
    for row in dictData:
        caption = row["caption"]
        id = row["id"]
        predmet = row["nazev"]
        vaha = row["vaha"]
        poznamka = row["poznamkakzobrazeni"]
        date = row["udel_datum"]
        znamka = row["MarkText"]

        if caption == "":
            caption = None
        else:
            caption = caption.replace(" <br>", "")
        predmet = PREDMETYNAOPAK[predmet]
        vaha = int(vaha)
        if poznamka == "":
            poznamka = None
        else:
            poznamka = poznamka.replace(" <br>", "")
        date = list(reversed([int(datum) for datum in date.split(".")]))
        if "-" in znamka:
            znamka = int(znamka.replace("-", "")) + 0.5
        else:
            znamka = int(znamka)

        znamky.znamky.append(Znamka(id, caption, predmet, vaha, poznamka, date, znamka))
    return znamky


async def znamkychange(client):
    def detectchange(znamkyOld, znamkyNew):
        newZnamky = []
        oldIDs = [znamka.id for znamka in znamkyOld.znamky]
        for znamka in znamkyNew.znamky:
            if znamka.id not in oldIDs:
                newZnamky.append(znamka)
        return newZnamky

    async def zmenenomessage(changed, znamky, client):
        channel = db["channelZnamky"]
        for znamka in changed:
            embed = discord.Embed()
            embed.set_author(name=PREDMETY[znamka.predmet])
            embed.title = znamka.znamkaString()
            poznamky = ""
            if znamka.caption:
                poznamky += "\n" + znamka.caption
            if znamka.poznamka:
                poznamky += "\n" + znamka.poznamka
            embed.description = f"Váha: {znamka.vaha}{poznamky}"

            obsah = f"Průměr z {znamka.predmet}: {znamky.byPredmet(znamka.predmet).prumer()}\nBudoucí průměr: {znamky.byPredmet(znamka.predmet).budouciPrumer()}"
            embed.add_field(name="\u200b", value=obsah, inline=False)
            embed.timestamp = datetime.datetime(*znamka.date)

            g = int(255 / 4 * (znamka.znamka - 1))
            r = int(255 - 255 / 4 * (znamka.znamka - 1))
            embed.color = discord.Color.from_rgb(g, r, 0)

            await client.get_channel(channel).send(embed=embed)

    if len(db.prefix("znamky")) == 0:
        znamky = getznamky()
        db["znamky"] = jsondumpsZnamky(znamky)
    else:
        znamkyNew = getznamky()
        znamkyOld = jsonloadsZnamky(db["znamky"])
        changed = detectchange(znamkyOld, znamkyNew)
        if changed:
            await zmenenomessage(changed, znamkyNew, client)
            db["znamky"] = jsondumpsZnamky(znamkyNew)


if __name__ == "__main__":
    main()
