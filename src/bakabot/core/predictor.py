import disnake
from bot_commands.reactions import Reactions
from constants import SUBJECTS, SUBJECTS_LOWER, SUBJECTS_REVERSED
from core.grades.grade import Grade
from core.grades.grades import Grades
from message_timers import MessageTimers

GRADES_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
MINUS_EMOJI = "➖"
WEIGHT_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟", "0️⃣", "*️⃣"]


async def predict_embed(subject: str, channel: disnake.TextChannel, client: disnake.Client):
    """Creates and sends the predictor embed"""
    # Creation of the embed
    embed = disnake.Embed()

    # Title
    embed.title = "Predictor"

    subjectText = SUBJECTS_LOWER.get(subject.lower())
    if subjectText is None:
        raise ValueError("Subject not found")

    # Subject
    embed.add_field(
        name=f"Předmět: {SUBJECTS.get(subjectText)}",
        value="\u200b",
        inline=False,
    )
    # Grade {select}
    embed.add_field(name="Známka: *\\{select\\}*", value="\u200b", inline=False)

    # Color
    embed.color = disnake.Color.from_rgb(102, 0, 255)

    # Sends the message
    message = await channel.send(embed=embed)
    # Adds reactions
    await message.add_reaction(MINUS_EMOJI)
    for emoji in GRADES_EMOJIS:
        await message.add_reaction(emoji)

    MessageTimers.cached_messages_react.append(message)
    # Removes the message after 5 minutes of inactivity
    await MessageTimers.delete_message(message, "predictorMessages", client, 300)


async def update_grade(reaction: Reactions, client: disnake.Client):
    """Edits the embed with the reacted grade"""
    for loopReaction in reaction.userReactions:
        # If reacted with the right emoji
        if loopReaction.emoji in GRADES_EMOJIS:
            # Prevents editing the message multiple times because of async code
            if len(reaction.message.embeds[0].fields) == 2:
                # Gets the grade
                grade = GRADES_EMOJIS.index(loopReaction.emoji) + 1
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


async def update_weight(reaction: Reactions, client: disnake.Client):
    """Edits the embed with the updated weight and shows the new grade average"""
    for loopReaction in reaction.userReactions:
        # If reacted with the right emoji
        if loopReaction.emoji in WEIGHT_EMOJIS:
            # Prevents editing the message multiple times because of async code
            if len(reaction.message.embeds[0].fields) == 3:
                # Gets the weight
                weight = WEIGHT_EMOJIS.index(loopReaction.emoji) + 1

                # Makes a Grade object from the message
                editedEmbed = reaction.message.embeds[0]

                # Subject
                embedSubject = editedEmbed.fields[0].name
                if embedSubject is None:
                    raise ValueError("Subject not found")

                subject = SUBJECTS_REVERSED.get(embedSubject.replace("Předmět: ", ""))
                if subject is None:
                    raise ValueError("Subject not found in subjects")

                # Grade
                embedGrade = editedEmbed.fields[1].name
                if embedGrade is None:
                    raise ValueError("Grade not found")

                grade = Grade.empty_grade(
                    subject=subject,
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
                average = Grades.db_grades().by_subject(grade.subject).future_average(grade)
                editedEmbed.add_field(name=f"Nový průměr: {average}", value="\u200b", inline=False)

                # Sends the edited message
                await reaction.message.edit(embed=editedEmbed)

                # Removes the reactions
                await reaction.message.clear_reactions()

                # Removes the message after 5 minutes of inactivity
                await MessageTimers.delete_message(reaction.message, "predictorMessages", client, 300)


def get_stage(message: disnake.Message):
    """Gets the stage of the embed and returns as int"""
    fieldsLen = len(message.embeds[0].fields)
    if fieldsLen > 1:
        if fieldsLen > 2:
            if fieldsLen > 3:
                return 3
            return 2
        return 1
