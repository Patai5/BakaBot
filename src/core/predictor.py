from typing import TYPE_CHECKING

import disnake
from disnake.ext.commands import InteractionBot

from ..constants import PREDICTOR_EMOJI
from ..message_timers import MessageTimers
from .grades.grade import Grade
from .grades.grades import Grades
from .subjects.subjects_cache import SubjectsCache

if TYPE_CHECKING:
    from ..bot_commands.reactions import Reactions

GRADES_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
MINUS_EMOJI = "➖"
WEIGHT_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "0️⃣", "*️⃣"]


async def predict_embed(subject: str, channel: disnake.TextChannel, client: InteractionBot) -> None:
    """Creates and sends the predictor embed"""

    color = disnake.Color.from_rgb(102, 0, 255)
    title = "Predictor"
    embed = disnake.Embed(title=title, color=color)

    # Subject
    embed.add_field(name=f"Předmět: {subject}", value="\u200b", inline=False)
    # Grade {select}
    embed.add_field(name="Známka: *\\{select\\}*", value="\u200b", inline=False)

    # Sends the message
    message = await channel.send(embed=embed)
    # Adds reactions
    await message.add_reaction(MINUS_EMOJI)
    for emoji in GRADES_EMOJIS:
        await message.add_reaction(emoji)

    MessageTimers.cached_messages_react.append(message)
    # Removes the message after 5 minutes of inactivity
    await MessageTimers.delete_message(message, "predictorMessages", client, 300)


async def update_grade(reaction: "Reactions", client: InteractionBot) -> None:
    """Edits the embed with the reacted grade"""
    for loopReaction in reaction.userReactions:
        emoji = str(loopReaction.emoji)

        # If reacted with the right emoji
        if not emoji in GRADES_EMOJIS:
            continue

        # Prevents editing the message multiple times because of async code
        if len(reaction.message.embeds[0].fields) == 2:
            # Gets the grade
            grade: int | float = GRADES_EMOJIS.index(emoji) + 1
            if MINUS_EMOJI in [emoji.emoji for emoji in reaction.userReactions]:
                if grade != 5:
                    grade += 0.5

            # Edits the grade into the embed
            editedEmbed = reaction.message.embeds[0]
            editedEmbed.set_field_at(
                1,
                name=f"Známka: {Grade.empty_grade(gradeValue=grade).grade_string()}",
                value="\u200b",
                inline=False,
            )

            # Weight {select}
            editedEmbed.add_field(name="Váha: *\\{select\\}*", value="\u200b", inline=False)

            # Sends the edited message
            await reaction.message.edit(embed=editedEmbed)

            # Removes old reactions and adds new ones
            await reaction.message.clear_reactions()
            for emoji in WEIGHT_EMOJIS:
                await reaction.message.add_reaction(emoji)

            # Removes the message after 5 minutes of inactivity
            await MessageTimers.delete_message(reaction.message, "predictorMessages", client, 300)


async def update_weight(reaction: "Reactions", client: InteractionBot) -> None:
    """Edits the embed with the updated weight and shows the new grade average"""
    for loopReaction in reaction.userReactions:
        emoji = str(loopReaction.emoji)

        # If reacted with the right emoji
        if not emoji in WEIGHT_EMOJIS:
            continue

        # Prevents editing the message multiple times because of async code
        if len(reaction.message.embeds[0].fields) == 3:
            # Gets the weight
            weight = WEIGHT_EMOJIS.index(emoji) + 1

            # Makes a Grade object from the message
            editedEmbed = reaction.message.embeds[0]

            # Subject
            embedSubject = editedEmbed.fields[0].name
            if embedSubject is None:
                raise ValueError("Subject not found")

            subjectName = embedSubject.replace("Předmět: ", "")
            subject = SubjectsCache.getSubjectByName(subjectName)

            # Grade
            embedGrade = editedEmbed.fields[1].name
            if embedGrade is None:
                raise ValueError("Grade not found")

            grade = Grade.empty_grade(
                subjectName=subject.fullName,
                weight=weight,
                gradeValue=float(embedGrade.replace("Známka: ", "")),
            )

            # Edits the weight into the embed
            editedEmbed.set_field_at(
                2,
                name=f"Váha: {grade.weight}",
                value="\u200b",
                inline=False,
            )

            # Average
            average = Grades.db_grades().by_subject_name(grade.subjectName).future_average(grade)
            editedEmbed.add_field(name=f"Nový průměr: {average}", value="\u200b", inline=False)

            # Sends the edited message
            await reaction.message.edit(embed=editedEmbed)

            # Removes the reactions
            await reaction.message.clear_reactions()

            # Removes the message after 5 minutes of inactivity
            await MessageTimers.delete_message(reaction.message, "predictorMessages", client, 300)


async def create_prediction(message: disnake.Message, client: InteractionBot) -> None:
    """Generates a predict message with the current subject"""
    # Subject
    embed = message.embeds[0].to_dict()

    embedAuthor = embed.get("author")
    if embedAuthor is None:
        raise Exception("No author in prediction embed")

    subjectFromEmbed = embedAuthor.get("name")
    if subjectFromEmbed is None:  # pyright: ignore[reportUnnecessaryComparison]
        raise Exception("No subject in prediction embed")

    subject = SubjectsCache.getSubjectByName(subjectFromEmbed)

    # Removes the reaction
    await MessageTimers.delete_message_reaction(message, "gradesMessages", PREDICTOR_EMOJI, client)

    messageChannel = message.channel
    if not isinstance(messageChannel, disnake.TextChannel):
        raise Exception("Message channel is not a TextChannel")

    # Sends the grade predictor
    await predict_embed(subject.fullName, messageChannel, client)


def get_stage(message: disnake.Message) -> int:
    """Gets the stage of the embed and returns as int"""
    fieldsLen = len(message.embeds[0].fields)
    if fieldsLen > 1:
        if fieldsLen > 2:
            if fieldsLen > 3:
                return 3
            return 2
        return 1
    return 0
