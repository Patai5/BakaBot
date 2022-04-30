import discord
from utils.utils import MessageTimers

from core.grades import Grades


class Predictor:
    GRADES_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    MINUS_EMOJI = "➖"
    WEIGHT_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "0️⃣", "*️⃣"]

    @staticmethod
    async def predict_embed(subject: str, channel: int, client: discord.Client):
        """Creates and sends the predictor embed"""
        # Creation of the embed
        embed = discord.Embed()

        # Title
        embed.title = "Predictor"
        # Subject
        embed.add_field(
            name=f"Předmět: {Grades.SUBJECTS.get(Grades.SUBJECTS_LOWER.get(subject.lower()))}",
            value="\u200b",
            inline=False,
        )
        # Grade {select}
        embed.add_field(name="Známka: *\{select\}*", value="\u200b", inline=False)

        # Color
        embed.color = discord.Color.from_rgb(102, 0, 255)

        # Sends the message
        message = await channel.send(embed=embed)
        # Adds reactions
        await message.add_reaction(Predictor.MINUS_EMOJI)
        for emoji in Predictor.GRADES_EMOJIS:
            await message.add_reaction(emoji)

        client.cached_messages_react.append(message)
        # Removes the message after 5 minutes of inactivity
        await MessageTimers.delete_message(message, "predictorMessages", client, 300)

    @staticmethod
    async def update_grade(reaction: discord.Reaction, client: discord.Client):
        """Edits the embed with the reacted grade"""
        for loopReaction in reaction.userReactions:
            # If reacted with the right emoji
            if loopReaction.emoji in Predictor.GRADES_EMOJIS:
                # Prevents editing the message multiple times because of async code
                if len(reaction.message.embeds[0].fields) == 2:
                    # Gets the grade
                    grade = Predictor.GRADES_EMOJIS.index(loopReaction.emoji) + 1
                    if Predictor.MINUS_EMOJI in [emoji.emoji for emoji in reaction.userReactions]:
                        if grade != 5:
                            grade += 0.5

                    # Edits the grade into the embed
                    editedEmbed = reaction.message.embeds[0]
                    editedEmbed.set_field_at(
                        1,
                        name=f"Známka: {Grades.empty_grade(grade=grade).grade_string()}",
                        value="\u200b",
                        inline=False,
                    )

                    # Weight {select}
                    editedEmbed.add_field(name="Váha: *\{select\}*", value="\u200b", inline=False)

                    # Sends the edited message
                    await reaction.message.edit(embed=editedEmbed)

                    # Removes old reactions and adds new ones
                    await reaction.message.clear_reactions()
                    for emoji in Predictor.WEIGHT_EMOJIS:
                        await reaction.message.add_reaction(emoji)

                    # Removes the message after 5 minutes of inactivity
                    await MessageTimers.delete_message(reaction.message, "predictorMessages", client, 300)

    @staticmethod
    async def update_weight(reaction: discord.Reaction, client: discord.Client):
        """Edits the embed with the updated weight and shows the new grade average"""
        for loopReaction in reaction.userReactions:
            # If reacted with the right emoji
            if loopReaction.emoji in Predictor.WEIGHT_EMOJIS:
                # Prevents editing the message multiple times because of async code
                if len(reaction.message.embeds[0].fields) == 3:
                    # Gets the weight
                    weight = Predictor.WEIGHT_EMOJIS.index(loopReaction.emoji) + 1

                    # Makes a Grade object from the message
                    editedEmbed = reaction.message.embeds[0]
                    grade = Grades.empty_grade(
                        subject=Grades.SUBJECTS_REVERSED.get(editedEmbed.fields[0].name.replace("Předmět: ", "")),
                        weight=weight,
                        grade=editedEmbed.fields[1].name.replace("Známka: ", ""),
                    )

                    # Parses the grade an int or a float because of this "-" symbol
                    if "-" in grade.grade:
                        grade.grade = int(grade.grade.replace("-", "")) + 0.5
                    else:
                        grade.grade = int(grade.grade)

                    # Edits the weigth into the embed
                    editedEmbed.set_field_at(
                        2,
                        name=f"Váha: {grade.weight}",
                        value="\u200b",
                        inline=False,
                    )

                    # Average
                    average = Grades.db_grades().by_subject(grade.subject).future_average(grade)
                    editedEmbed.add_field(name=f"Nový průměr: {average}", value="\u200b", inline=False)

                    # Sends the edited message
                    await reaction.message.edit(embed=editedEmbed)

                    # Removes the reactions
                    await reaction.message.clear_reactions()

                    # Removes the message after 5 minutes of inactivity
                    await MessageTimers.delete_message(reaction.message, "predictorMessages", client, 300)

    @staticmethod
    def get_stage(message: discord.Message):
        """Gets the stage of the embed and returns as int"""
        fieldsLen = len(message.embeds[0].fields)
        if fieldsLen > 1:
            if fieldsLen > 2:
                if fieldsLen > 3:
                    return 3
                return 2
            return 1
