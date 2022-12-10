from __future__ import annotations

from typing import Sequence

import asyncio
import logging
import time

import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext


class BadApplePlayer:
    _logger: logging.Logger = logging.getLogger("badapple")
    _frames: Sequence[str] = []

    _original_fps: int = 10  # How many frames per second the source data has
    _render_fps: float = 1 / 5  # How often to update the discord message
    _playback_speed: float = 1 / 25  # How quickly to play the video (lower = more frames)

    _downsample_ratio: int = int(_playback_speed * _original_fps / _render_fps)

    @classmethod
    def load_frames(cls) -> None:
        with open("commands/bad_apple.txt", "r", encoding="utf-8") as inp:
            cls._frames = inp.read().split("\n---\n")[:: cls._downsample_ratio]

        cls._logger.info(
            "%d frames loaded, each %s bytes", len(cls._frames), len(cls._frames[0])
        )

    _message: discord.PartialMessage

    def __init__(self, message: discord.PartialMessage) -> None:
        self._message = message
        if not BadApplePlayer._frames:
            BadApplePlayer.load_frames()

    async def play(self) -> None:
        self._logger.info(
            "Playing Bad Apple in %s",
            self._message.channel.name if hasattr(self._message.channel, "name") else "[DM]",
        )
        loop = asyncio.get_running_loop()
        start = loop.time()
        start_time = time.time()
        end = start_time + len(self._frames) / self._render_fps

        rendered_frame = -1
        rendered_frames = 0

        while True:
            frame_number = round((loop.time() - start) * self._render_fps)

            if frame_number >= len(self._frames):
                break

            if frame_number != rendered_frame:
                await self._message.edit(content=self.message(frame_number, start_time, end))
                rendered_frames += 1
                rendered_frame = frame_number
            else:
                await asyncio.sleep(1 / (8 * self._render_fps))

        log = (
            f"Bad Apple complete, took {int(loop.time() - start)}s, "
            f"playing {rendered_frames} of {len(self._frames)} frames"
        )

        await self._message.edit(content="🍎 " + log)
        self._logger.info(log)

    def message(self, frame: int, start: float, end: float) -> str:
        timestamp = int(frame / (self._original_fps / self._downsample_ratio))
        seconds = timestamp % 60
        minutes = int(timestamp / 60)

        return (
            "```" + self._frames[frame] + "``` "
            f"At {minutes}:{seconds:02d} (frame {frame} of {len(self._frames)}), "
            f"started at <t:{int(start)}:T>, and will end (approximately) <t:{int(end)}:R>"
        )


class BadAppleCommand(Command):
    def matches(self, message: str) -> bool:
        return message == "!badapple"

    async def process(self, context: MessageContext, message: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        apple = await context.reply_all("🍎")
        asyncio.get_running_loop().create_task(BadApplePlayer(apple).play())
        return True
