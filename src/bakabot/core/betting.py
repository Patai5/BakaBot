import asyncio
import re

import discord

from bakabot.core.schedule import Schedule
from bakabot.utils.utils import (
    MessageTimers,
    fetch_message,
    rand_rgb,
    read_db,
    write_db,
)


class Betting:
    BETT_EMOJI = "🎲"

    @staticmethod
    async def start_betting(client: discord.Client):
        channel = read_db("channelSchedule")

        embed = discord.Embed()
        embed.title = "Get scammed"

        bettingScore = Betting.sort_betting_score(read_db("bettingScore"))
        if bettingScore:
            scoreboard = ""
            for place, user in enumerate(bettingScore.items()):
                scoreboard += f"`#{place + 1}` {user[1]} - <@{user[0]}>\n"
            scoreboard[:-1]
        else:
            scoreboard = "No users yet"

        embed.description = scoreboard
        embed.color = discord.Color.from_rgb(255, 200, 36)

        message = await client.get_channel(channel).send(embed=embed)
        # Adds the reaction emoji
        await message.add_reaction(Betting.BETT_EMOJI)
        # Removes the emoji after 12 hours
        asyncio.ensure_future(
            MessageTimers.delete_message_reaction(message, "bettingMessages", Betting.BETT_EMOJI, client, 43200)
        )

    @staticmethod
    async def make_bet(reaction: discord.Reaction, client: discord.Client):
        betts = read_db("betts")
        if reaction.user.id not in betts:
            embed = discord.Embed()
            embed.title = f"{reaction.user.name}'s bet"

            # Removed lessons {type}
            embed.add_field(name="Počet odpadlých hodin: *\{type\}*", value="\u200b", inline=False)

            embed.color = discord.Color.from_rgb(*rand_rgb())

            message = await reaction.message.channel.send(embed=embed)

            MessageTimers.response_channel(message.channel.id, reaction.user.id, message.id, "betting", client)
            betts[reaction.user.id] = [message.id]
            write_db("betts", betts)

            # Removes the message after 5 minutes of inactivity
            await MessageTimers.delete_message(
                message,
                "bettMessages",
                client,
                300,
                lambda: Betting.remove_unfinished_bet([message.id, message.channel.id], client),
            )

    @staticmethod
    async def update_removed_lessons(message: discord.Message, client: discord.Client):
        users = read_db("betts")
        for user in users:
            if user == message.author.id:
                maxRemovedLessons = Betting.get_max_removed(Schedule.json_loads(read_db("bettingSchedule")))
                if int(message.content) <= maxRemovedLessons:
                    updateMessage = await fetch_message(message.channel.id, users[user][0], client)
                    if updateMessage:
                        editedEmbed = updateMessage.embeds[0]

                        editedEmbed.set_field_at(
                            0,
                            name=f"Počet odpadlých hodin: {message.content}",
                            value="\u200b",
                            inline=False,
                        )

                        editedEmbed.add_field(name="Počet přidaných hodin: *\{type\}*", value="\u200b", inline=False)

                        editedEmbed.color = discord.Color.from_rgb(*rand_rgb())

                        await message.add_reaction("✅")

                        # Sends the edited message
                        await updateMessage.edit(embed=editedEmbed)

                        betts = read_db("betts")
                        betts[user] = [betts[user][0], int(message.content)]
                        write_db("betts", betts)

                        MessageTimers.response_channel(message.channel.id, user, message.id, "betting", client)
                    else:
                        MessageTimers.response_channel(message.channel.id, user, message.id, "betting", client, True)
                        betts = read_db("betts")
                        del betts[user]
                        write_db("betts", betts)
                else:
                    await message.channel.send(f"Tento týden může odpadnout maximálně {maxRemovedLessons} hodin!")
                    MessageTimers.response_channel(message.channel.id, user, message.id, "betting", client)

    @staticmethod
    async def update_added_lessons(message: discord.Message, client: discord.Client):
        users = read_db("betts")
        for user in users:
            if user == message.author.id:
                maxAddedLessons = Betting.get_max_added(Schedule.json_loads(read_db("bettingSchedule")))
                if int(message.content) <= maxAddedLessons:
                    updateMessage = await fetch_message(message.channel.id, users[user][0], client)
                    if updateMessage:
                        editedEmbed = updateMessage.embeds[0]

                        betts = read_db("betts")
                        scoreAfterBet = Betting.score_after_bet(betts[user][1], int(message.content), user)

                        editedEmbed.set_field_at(
                            1,
                            name=f"Počet přidaných hodin: {message.content}",
                            value="\u200b",
                            inline=False,
                        )

                        editedEmbed.add_field(
                            name=f"Aktualní počet bodů: {scoreAfterBet}", value="\u200b", inline=False
                        )

                        editedEmbed.color = discord.Color.from_rgb(*rand_rgb())

                        await message.add_reaction("✅")

                        # Sends the edited message
                        await updateMessage.edit(embed=editedEmbed)

                        betts[user] = [betts[user][0], betts[user][1], int(message.content)]
                        write_db("betts", betts)

                        bettingScore = read_db("bettingScore")
                        bettingScore[user] = scoreAfterBet
                        write_db("bettingScore", bettingScore)

                        MessageTimers.stop_message_removal(
                            [updateMessage.id, updateMessage.channel.id], "bettMessages", client
                        )
                    else:
                        MessageTimers.response_channel(message.channel.id, user, message.id, "betting", client, True)
                        betts = read_db("betts")
                        del betts[user]
                        write_db("betts", betts)
                else:
                    await message.channel.send(f"Tento týden může přibýt maximálně {maxAddedLessons} hodin!")
                    MessageTimers.response_channel(message.channel.id, user, message.id, "betting", client)

    @staticmethod
    async def response(message: discord.Message, client: discord.Client):
        if re.search(r"^\d+$", message.content):
            betts = read_db("betts")
            if message.author.id in betts:
                if len(betts[message.author.id]) == 1:
                    MessageTimers.response_channel(
                        message.channel.id, message.author.id, message.id, "betting", client, True
                    )
                    await Betting.update_removed_lessons(message, client)
                elif len(betts[message.author.id]) == 2:
                    MessageTimers.response_channel(
                        message.channel.id, message.author.id, message.id, "betting", client, True
                    )
                    await Betting.update_added_lessons(message, client)

    @staticmethod
    def score_after_bet(removedBet: int, addedBet: int, user: int):
        users = read_db("bettingScore")
        if user not in users:
            users[user] = 0
            write_db("bettingScore", users)
        return users[user] - removedBet - addedBet

    @staticmethod
    async def add_user(id, points):
        bettingScore = read_db("bettingScore")
        bettingScore[id] = points
        write_db("bettingScore", bettingScore)

    @staticmethod
    def remove_unfinished_bet(message, client: discord.Client):
        """Removes the message's unfinished bet from the database"""
        betts = read_db("betts")
        for item in betts.copy().items():
            if message[0] == item[1][0]:
                if len(item[1]) != 4:
                    del betts[item[0]]
                    write_db("betts", betts)
                    MessageTimers.response_channel(message[1], item[0], message[0], "betting", client, True)

    @staticmethod
    def sort_betting_score(bettingScore):
        return dict(sorted(bettingScore.items(), key=lambda item: item[1], reverse=True))

    @staticmethod
    def get_removed_added(startSchedule, endSchedule):
        """Returns list (removed, added) of the amount of removed and added lessons"""
        removed = 0
        added = 0
        for dayStart, dayEnd in zip(startSchedule.days, endSchedule.days):
            for lessonStart, lessonEnd in zip(dayStart.lessons, dayEnd.lessons):
                if not lessonStart.empty and lessonEnd.empty:
                    removed += 1
                elif lessonStart.empty and not lessonEnd.empty:
                    added += 1
        return removed, added

    @staticmethod
    def get_max_removed(schedule):
        """Returns the maximum amount of possible removed lessons for the week"""
        possible = 0
        for day in schedule.days:
            for lesson in day.lessons:
                if not lesson.empty:
                    possible += 1
        return possible

    @staticmethod
    def get_max_added(schedule):
        """Returns the maximum amount of possible added lessons for the week"""
        possible = 0
        for day in schedule.days:
            for lesson in day.lessons:
                if lesson.empty:
                    possible += 1
        return possible

    @staticmethod
    def update_week(endSchedule: Schedule):
        startSchedule = Schedule.json_loads(read_db("bettingSchedule"))
        removedLessons, addedLessons = Betting.get_removed_added(startSchedule, endSchedule)

        users = read_db("betts")
        bettingScore = read_db("bettingScore")
        for user in users:
            removedBet = users[user][1]
            addedBet = users[user][2]
            if (removedLessons - abs(removedLessons - removedBet) * 2) * 2 > 0:
                bettingScore[user] += (removedLessons - abs(removedLessons - removedBet) * 2) * 2
            if (addedLessons - abs(addedLessons - addedBet) * 2) * 2 > 0:
                bettingScore[user] += (addedLessons - abs(addedLessons - addedBet) * 2) * 2
        write_db("bettingSchedule", Schedule.json_dumps(endSchedule))
        write_db("bettingScore", bettingScore)
        write_db("betts", {})
