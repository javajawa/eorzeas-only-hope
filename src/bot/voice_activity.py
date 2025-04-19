# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import time

from discord import Member, Message, StageChannel, TextChannel, VoiceChannel, VoiceState

VOICE_RELEVANT_CHANNEL = 779101163387486244
GENERAL_VOICE_CHANNEL = 441658759249657863
PRIORITY_SPEAKER_ROLE = 1359617115597963315


_changes: dict[int, tuple[str, float, float]] = {}


async def voice_message(message: Message) -> None:
    if not message.guild or message.channel.id != VOICE_RELEVANT_CHANNEL:
        return

    if message.content.startswith("!activity"):
        await _voice_activity_message(message)
    if message.content.startswith("!conch"):
        await _set_priority_speaker(message)


async def _voice_activity_message(message: Message) -> None:
    if not message.guild:
        return

    channel = message.guild.get_channel(GENERAL_VOICE_CHANNEL)

    if not isinstance(channel, VoiceChannel):
        return

    name = message.content.replace("!activity", "").strip()
    name = "General - " + name if channel.members and name else "General"

    asyncio.get_running_loop().create_task(
        request_name_change(channel, name, "Requested by " + str(message.author)),
    )


async def _set_priority_speaker(message: Message) -> None:
    if not message.guild:
        return

    role = message.guild.get_role(PRIORITY_SPEAKER_ROLE)

    if not role:
        await message.channel.send("Unable to find the priority speaker role")
        return

    current = role.members
    targets: list[Member] = message.mentions  # type: ignore[assignment]

    if set(role.members) == set(targets):
        return

    for member in current:
        if member not in targets:
            await member.remove_roles(role, reason="Conch has been passed")
    for member in targets:
        if member not in current:
            await member.add_roles(role, reason="Conch has been passed")

    await message.channel.send("The conch has been passed")


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
        request_name_change(before.channel, "General", "No users left in channel"),
    )


async def request_name_change(
    channel: StageChannel | VoiceChannel,
    name: str,
    reason: str,
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
                    f"Rate limited, channel name will update to '{name}; later ({int(wait)}s)"
                ),
            )
        await asyncio.sleep(wait)

    if _changes[channel.id][0] != name:
        return

    _changes[channel.id] = (name, time.time(), time1)
    await channel.edit(name=name, reason=reason)
