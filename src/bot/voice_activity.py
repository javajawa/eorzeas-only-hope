from __future__ import annotations

from typing import Dict, Tuple, Union

import asyncio
import time

from discord import Message, StageChannel, TextChannel, VoiceChannel, VoiceState


VOICE_RELEVANT_CHANNEL = 779101163387486244
GENERAL_VOICE_CHANNEL = 441658759249657863


_changes: Dict[int, Tuple[str, float, float]] = {}


async def voice_activity_message(message: Message) -> None:
    if message.guild and message.channel.id == VOICE_RELEVANT_CHANNEL:
        if message.content.startswith("!activity"):
            channel = message.guild.get_channel(GENERAL_VOICE_CHANNEL)

            if isinstance(channel, VoiceChannel):
                name = message.content.replace("!activity", "").strip()
                name = "General - " + name if channel.members and name else "General"

                asyncio.get_running_loop().create_task(
                    request_name_change(channel, name, "Requested by " + str(message.author))
                )


async def voice_state_event(before: VoiceState, after: VoiceState) -> None:
    # We only care about people leaving the general voice channel
    if not before.channel or before.channel.id != GENERAL_VOICE_CHANNEL:
        return

    # If they're still there, we no care.
    if after.channel and after.channel.id == GENERAL_VOICE_CHANNEL:
        return

    if before.channel.members:
        return

    asyncio.get_running_loop().create_task(
        request_name_change(before.channel, "General", "No users left in channel")
    )


async def request_name_change(
    channel: Union[StageChannel, VoiceChannel], name: str, reason: str
) -> None:
    if name == channel.name:
        return

    target, time1, time2 = _changes.get(channel.id, ("", 0, 0))

    if target == name:
        return

    _changes[channel.id] = (name, time1, time2)

    wait = time2 - time.time() + 610

    if wait > 10:
        feedback = channel.guild.get_channel(VOICE_RELEVANT_CHANNEL)
        if isinstance(feedback, TextChannel):
            await feedback.send(
                content=(
                    f"Rate limited, channel name will update "
                    f"to '{name}; later ({int(wait)}s)"
                )
            )
        await asyncio.sleep(wait)

    if _changes[channel.id][0] != name:
        return

    _changes[channel.id] = (name, time.time(), time1)
    await channel.edit(name=name, reason=reason)
