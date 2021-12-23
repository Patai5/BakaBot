from bs4 import BeautifulSoup
import re
import discord
import os
from replit import db
import json
import asyncio
from keep_alive import keep_alive

username = os.environ['username']
password = os.environ['password']
token = os.environ['token']


def main():
    keep_alive()
    
    client = discord.Client()

    @client.event
    async def on_ready():
        print('Ready!')
        await rozvrhchange(client)

    @client.event
    async def on_message(message):
        if not message.author.bot:
            await botcommands(message, client)

    @client.event
    async def on_reaction_add(reaction, user):
        if reaction.message.author.id == 917505805216010271:
            if not user.bot:
                async for user in reaction.users():
                    if user.id == 917505805216010271:
                        await reaction.remove(user)
                        if reaction.message.embeds[0].fields[0].name.startswith("Tento týden, "):
                            await reaction.message.channel.send(rozvrhshow(1, 5, showden=True, showtrida=True))
                        else:
                            await reaction.message.channel.send(rozvrhshow(1, 5, nextweek=True, showden=True, showtrida=True))
                        break


    client.run(token)


async def botcommands(message, client):
    async def gethelp(function=""):
        general = "Nedokázal jsem rozluštit váš příkaz.\nPužijte \"TestBot Help\" pro nápovědu"
        rozvrhhelp = "Špatný argument pro funkci Rozvrh\nBakaBot Rozvrh den(jeden den(DEN)|více dní(DEN-DEN)|" \
                    "celý týden(TÝDEN)) ?příští(jaký týden(PŘÍŠTÍ))\nDEN = \"pondělí|monday|1\", " \
                    "DEN-DEN = \"DEN-DEN|týden|week\", PŘÍŠTÍ = \"příští|aktuální|now|next|1|2\""
        if function == "rozvrhhelp":
            await message.channel.send(rozvrhhelp)
        else:
            await message.channel.send(general)

    async def settings(message, command):
        if message.author.id == 335793327431483392:
            command = command.replace("setting ", "")
            args = command.split(" ")[:3]
            if len(args) != 2:
                args.insert(1, "")
            if args[0].startswith("showden"):
                if re.match("(true|ano|1)", args[1].lower()):
                    db["showden"] = True
                    await message.channel.send("showden = True")
                elif re.match("(false|ne|0)", args[1].lower()):
                    db["showden"] = False
                    await message.channel.send("showden = False")
                else:
                    await gethelp("settings")
            elif args[0].startswith("showtrida"):
                if re.match("(true|ano|1)", args[1].lower()):
                    db["showtrida"] = True
                    await message.channel.send("showtrida = True")
                elif re.match("(false|ne|0)", args[1].lower()):
                    db["showtrida"] = False
                    await message.channel.send("showtrida = False")
                else:
                    await gethelp("settings")
            elif args[0].startswith("channelzmeneno"):
                db["channelZmeneno"] = message.channel.id
                await message.channel.send("channelZmeneno = This channel")
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
                crashed =True
                await gethelp("rozvrhhelp")
        if not crashed:
            zprava = rozvrhshow(daystart, dayend, nextweek)
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
        else:
            await gethelp()


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
    def __init__(self, value, newline):
        self.value = value
        self.newline = newline


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

    for column in columns:
        longest = 0
        for item in column:
            if len(item.value) > longest:
                longest = len(item.value)
        for i in range(len(column)):
            column[i].value = spaceout(column[i].value, longest)

        rows[0] = rows[0] + repeat("═", longest + 2) + "╤"
        z = 1
        for i, item in enumerate(column):
            rows[z] = rows[z] + " " + item.value + " " + "│"
            if item.newline:
                if i != len(column) - 1:
                    z = z + 1
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


class Lesson:
    def __init__(self, hodina, predmet, trida):
        self.hodina = hodina
        self.predmet = predmet
        self.trida = trida
        #self.changeinfo = changeinfo


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
    session = login(username, password, url)
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
                name = lesson.find("div", {"class": "middle"})
                if name:
                    reg = re.findall("(?<=>).*(?=</)", str(name))[0]
                    if reg != "":
                        data = lesson.find_all("div", {"class": "day-item-hover"})
                        reg2 = re.findall("(?<=\"room\":\").*?(?=\")", str(data))
                        if reg2:
                            reg2 = reg2[0]
                        else:
                            reg2 = " "
                        lessons[i2] = Lesson(i2, reg, reg2)
                    else:
                        lessons[i2] = Lesson(i2, " ", " ")
                else:
                    lessons[i2] = Lesson(i2, " ", " ")
        lessons.pop(6)
        for i2, lesson in enumerate(lessons):
            lessons[i2] = Lesson(i2, lesson.predmet, lesson.trida)
        daynazev = day.div.div.div.div
        daynazev = re.findall("(?<=<div>)\s*?(..)(?=<br/>)", str(daynazev))[0]
        if prazdny:
            days[i] = Day(lessons, daynazev, True)
        else:
            days[i] = Day(lessons, daynazev, False)
    rozvrh = Rozvrh(days, nextweek)
    return rozvrh
  


def rozvrhshow(daystart, dayend, nextweek=False, showden=None, showtrida=None):
    if showden == None:
        showden = readdb("showden")
        if showden == None:
            showden = False
    if showtrida == None:
        showtrida = readdb("showtrida")
        if showtrida == None:
            showtrida = False

    rozvrh = getrozvrh(nextweek)
    rozvrh.days = rozvrh.days[daystart - 1:dayend]

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
                day.lessons = day.lessons[:-lowest]

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


def jsondumps(rozvrh):
    output = "{\"days\": ["
    for day in rozvrh.days:
        output = output + "{\"lessons\": ["
        for lesson in day.lessons:
            output = output + json.dumps(lesson.__dict__) + ", "
        output = output[:-2] + "]"
        output = output + ", \"den\": \"" + day.den + "\", \"prazdny\": " + str(day.prazdny).lower() + "}, "
    output = output[:-2] + "]"
    output = output + ", \"pristi\": " + str(rozvrh.pristi).lower() + "}"
    return output


def jsonloads(jsonstring):
    dictRozvrh = json.loads(jsonstring)
    days = []
    for day in dictRozvrh["days"]:
        lessons = []
        for lesson in day["lessons"]:
            lessons.append(Lesson(lesson["hodina"], lesson["predmet"], lesson["trida"]))
        days.append(Day(lessons, day["den"], day["prazdny"]))
    rozvrh = Rozvrh(days, dictRozvrh["pristi"])
    return rozvrh
        

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
    return(output)
          

async def zmenenomessage(changed, tyden, client):
    channel = db["channelZmeneno"]
    embed = discord.Embed()
    embed.title = "Detekována změna v rozvrhu"
    for changedItem in changed:
        lessonOld, lessonNew, den = changedItem
        nazev = ""
        if tyden:
            nazev = "Příští týden, "
        else:
            nazev = "Tento týden, "
        nazev = nazev + den + ", " + str(lessonOld.hodina) + ". hodina"
        obsah = zmenapredmet(lessonOld, lessonNew)
        embed.add_field(name=nazev, value=obsah, inline = True)
        nazev = "Additional info"
        obsah = "WIP"
        embed.add_field(name=nazev, value=obsah, inline = True)
        embed.add_field(name='\u200b', value='\u200b', inline = False)
    embed.remove_field(len(changed) * 3 - 1)
    messageRespond = await client.get_channel(channel).send(embed=embed)
    await messageRespond.add_reaction(u'\U0001f4c5')


def detectchange(rozvrhOld, rozvrhNew):
    changedlist = []
    for (dayOld, dayNew) in zip(rozvrhOld.days, rozvrhNew.days):
        for (lessonOld, lessonNew) in zip(dayOld.lessons, dayNew.lessons):
            changed = lessonOld, lessonNew, dayOld.den
            if lessonOld.predmet != lessonNew.predmet or lessonOld.trida != lessonNew.trida:
                changedlist.append(changed)
    if len(changedlist) != 0:
       return changedlist
    else:
        return None


async def rozvrhchange(client):
    if len(db.prefix("rozvrh1")) == 0:
        rozvrh1 = getrozvrh(False)
        rozvrh2 = getrozvrh(True)
        db["rozvrh1"] = jsondumps(rozvrh1)
        db["rozvrh2"] = jsondumps(rozvrh2)
    else:
        change = False
        rozvrhNew1 = getrozvrh(False)
        rozvrhNew2 = getrozvrh(True)
        rozvrhOld1= jsonloads(db["rozvrh1"])
        rozvrhOld2 = jsonloads(db["rozvrh2"])
        changed = detectchange(rozvrhOld1, rozvrhNew1)
        if changed:
            await zmenenomessage(changed, False, client)
            change = True
        changed = detectchange(rozvrhOld2, rozvrhNew2)
        if changed:
            await zmenenomessage(changed, True, client)
            change = True
        if change:
            db["rozvrh1"] = jsondumps(rozvrhNew1)
            db["rozvrh2"] = jsondumps(rozvrhNew2)
    await asyncio.sleep(60)
    await rozvrhchange(client) 


def czechletters(string):
    return re.sub("[ěščřžýáíéúůňĚŠČŘŽÝÁÍÉÚŮŇ∞ˇ]", "*", string)


def login(username, password, url):
    data = {"username": username, "password": password}
    session = requests.Session()
    session.post(url, data)
    return session


if __name__ == "__main__":
    main()