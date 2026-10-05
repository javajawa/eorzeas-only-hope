# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import asyncio
import datetime
import email.utils
import logging
import pathlib
import random
from concurrent.futures import ThreadPoolExecutor

import discord

from bot.commands import Command, MessageContext
from bot.discord import DiscordMessageContext

from .animation import Player, ThrowLog
from .physics import CurlingGame, WrongTeamError
from .rules import Team


class CurlingCommand(Command):
    """Allows users to throw a stone down an empty curling sheet."""

    _logger: logging.Logger
    _tasks: set[asyncio.Task[None]]
    _games: dict[str, CurlingGame]
    _render_pool: ThreadPoolExecutor
    _path: pathlib.Path

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._tasks = set()
        self._games = {}
        self._render_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="curling")
        self._path = pathlib.Path("curls")

        active = self._path / "active"
        active.mkdir(parents=True, exist_ok=True)

        for existing_game in active.glob("*.json"):
            try:
                channel = existing_game.name.removesuffix(".json")
                game = CurlingGame.load(logger.getChild(channel), existing_game)
                if game.to_throw:
                    self._games[channel] = game
            except Exception as exc:
                self._logger.exception(
                    "Failed loading %s, not restoring",
                    existing_game,
                    exc_info=exc,
                )

    @property
    def command_hint(self) -> str | None:
        return "!curl"

    @property
    def group(self) -> str | None:
        return "Interactive"

    def matches(self, message: str) -> bool:
        return message == "!curl" or message.startswith("!curl ")

    async def process(self, context: MessageContext, message: str) -> bool:
        if not isinstance(context, DiscordMessageContext):
            return False

        args = message.split(" ")[1:]

        match len(args):
            case 0:
                return await self._current_state(context)

            case 1:
                match args[0].lower():
                    case "help":
                        return await self._help(context)
                    case _:
                        now = email.utils.format_datetime(datetime.datetime.now(datetime.UTC))
                        await context.reply_all(
                            "```\nHTTP/2 407 Proxy Authentication Required\n"
                            f"date: {now}\n"
                            'proxy-authenticate: Quest realm="eorzea-bot"\n'
                            "server: HopeBot/1.0\nx-clacks-overhead: GNU Terry Pratchett\n"
                            "```",
                        )
                        return False

            case 3 | 4:
                return await self.throw(context, args)

            case _:
                now = email.utils.format_datetime(datetime.datetime.now(datetime.UTC))
                await context.reply_all(
                    "```\nHTTP/2 407 Proxy Authentication Required\n"
                    f"date: {now}\n"
                    'proxy-authenticate: Quest realm="eorzea-bot"\n'
                    "server: HopeBot/1.0\nx-clacks-overhead: GNU Terry Pratchett\n"
                    "```",
                )
                return False

    async def throw(self, context: DiscordMessageContext, args: list[str]) -> bool:
        try:
            args.append("0")
            offset, speed, spin, target = map(float, args[0:4])
        except ValueError:
            await context.reply_all("Didn't get three or four numbers?")
            return False

        channel = str(context.message.channel.id)

        if channel not in self._games:
            self._games[channel] = CurlingGame(logging.getLogger(channel))

        if abs(offset) > 220 or abs(target) > 300 or abs(spin) > 120 or speed < 300 or speed > 600:
            await context.reply_all("Values out of range (see !curl help)")
            return False

        offset = (offset + clamped_gauss(2)) / 10
        speed = (speed + clamped_gauss(2)) / 10
        target = (target + clamped_gauss(6)) / 10
        spin = (spin + clamped_gauss(1)) * (1 + clamped_gauss(0.02))
        release_time = random.randrange(8, 20) / 100

        game = self._games[channel]
        player = Player(
            str(context.message.author.id),
            context.message.author.display_name,
            context.message.author.mention,
        )

        try:
            throw = game.play_turn(player, offset, speed, spin, target, release_time)
        except WrongTeamError:
            await context.reply_all(
                f"Sorry {player.mention}, you're already playing for the other team",
            )
            return True

        game.save(self._path / f"active/{channel}.json")

        message = await context.reply_all("Throw complete, rendering...")

        task = asyncio.create_task(self.render(throw, message))
        task.add_done_callback(self._tasks.discard)
        self._tasks.add(task)

        if not game.to_throw:
            task = asyncio.create_task(self.score(game, task, context))
            task.add_done_callback(self._tasks.discard)
            self._tasks.add(task)

        return True

    async def _help(self, message: MessageContext) -> bool:
        await message.reply_all(
            "Usage `!curl <center line offset> <speed> <spin> [<target intercept>]`\n\n"
            "Throw a stone down the curling rink, and see a little animation. "
            "For this help, directions are given as seen from the thrower, so "
            "'right' is towards the top of the animation.\n"
            "- The 'center line offset' is measured in centimeters, "
            "with positive to the left and negative to the right. "
            "Accepts values between -220 and 220\n"
            "- The speed is measured in cm/s as the stone is released. "
            "You need at least 350 to get to the hog line; over 420ish "
            "will push you over the backline -- unless you hit something on the way. "
            "A release at 402 should land you in the center of the house. "
            "Accepts values between 300 and 600.\n"
            "- Spin is the initial rotation, in degrees per second "
            "(positive to the right, negative to the left). You normally want "
            "the spin and offset to have the same sign to curve around the center."
            "Accepts values between -120 and 120.\n"
            "- The target intercept is like the center line offset, bit it is "
            "the point on the tee line you are aiming the stone towards. "
            "This value is optional, with a default of 0 (i.e. throwing the "
            "stone towards the center of the house). This value does not take "
            "into account the curling effect of spin. "
            "Accept values between -300 and 300 -- note that extreme values "
            "will need spin to prevent them from leaving the lane.\n\n"
            "You can use `!curl` to see the current state of the house with "
            "some overlay guides showing the offset positions and the expected "
            "distance from straight shots.",
        )

        return True

    async def _current_state(self, message: DiscordMessageContext) -> bool:
        game = self._games.get(str(message.message.channel.id))

        if not game:
            await message.reply_all(
                "There is currently no active curling game in this channel.\n"
                "Start a game with `!curl [center line offset] [speed] [spin]`.\n"
                "Use `!curl help` for guidance on the values.",
            )
            return True

        latest = game.turns[-1]
        next_stone = min(game.to_throw)
        stones = len(game.stones) / 2

        path = pathlib.Path(f"render-{game.id}.png")
        try:
            await asyncio.get_running_loop().run_in_executor(
                self._render_pool,
                latest.generate_state_image,
                path,
            )

            text = (
                f"Next Stone: {next_stone} ({stones} stones each; Red have the hammer)\n"
                f"Yellow Players: {', '.join(p.name for p in game.players[Team.YELLOW])}\n"
                f"Red Players: {', '.join(p.name for p in game.players[Team.RED])}\n"
            )

            await message.message.channel.send(content=text, file=discord.File(path))
        finally:
            self._render_pool.submit(path.unlink, missing_ok=True)

        return True

    async def render(self, throw: ThrowLog, message: discord.Message) -> None:
        path = self._path / f"{throw.id}.svg"
        throw.generate_animated_svg(path)

        # First update: link the animated SVG
        text = (
            "; ".join(throw.messages)
            + f"\n[View Animation](https://tea-cats.co.uk/curling/{path.name})"
        )
        await message.edit(content=text + " [Video still rendering].")

        path = pathlib.Path(f"render-{throw.id}.gif")
        try:
            renderer = asyncio.get_running_loop().run_in_executor(
                self._render_pool,
                throw.generate_gif,
                path,
            )

            # Second update: upload the video
            await renderer
            await message.edit(
                content=text,
                attachments=[discord.File(path)],
            )
        finally:
            path.unlink(missing_ok=True)

    async def score(
        self,
        game: CurlingGame,
        last_render: asyncio.Task[None],
        context: DiscordMessageContext,
    ) -> None:
        await last_render

        del self._games[str(context.message.channel.id)]

        scores = sorted(game.score(), reverse=True)

        mess = "### End Completed!\n"
        mess += "\n".join(
            (
                f"Team {score.team.name.title()}: "
                f"{score.score} {':curling_stone:' * score.score} "
                f"{' '.join(p.mention for p in score.players)}"
            )
            for score in scores
        )
        await context.reply_all(mess)


def clamped_gauss(sigma: float) -> float:
    return max(-3 * sigma, min(3 * sigma, random.gauss(0, sigma)))


def jitter(value: float, jit: float) -> float:
    return value + ((random.random() - 0.5) * 2 * jit)


def main() -> None:
    logger = logging.getLogger("curl")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    game = CurlingGame(logger)
    turn = game.play_turn(Player("Kitteh", "Kitteh", "Kitteh"), 0, 40.18, 0, 0, 0.14)
    turn.generate_state_image(pathlib.Path("demo.png"))
