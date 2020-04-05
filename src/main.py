#!/usr/bin/python3
# vim: ts=4 expandtab nospell

from __future__ import annotations

from multiprocessing import Process

from storage import FileStore
from bot import DiscordBot, TwitchBot


def main():
    with FileStore("list.txt") as storage:
        twitch = Process(target=twitch_bot, args=(storage,))
        discord = Process(target=discord_bot, args=(storage,))

        discord.start()
        twitch.start()

        try:
            twitch.join()
            discord.join()
        except KeyboardInterrupt:
            twitch.terminate()
            discord.terminate()


def twitch_bot(storage: FileStore) -> None:
    with open("twitch.token", "r") as token_handle:
        [nick, token, *channels] = token_handle.read().strip().split("::")

    instance = TwitchBot(token, nick, storage, channels)
    instance.run()


def discord_bot(storage: FileStore) -> None:
    with open("discord.token", "r") as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    instance = DiscordBot(storage)
    instance.run(token)


if __name__ == "__main__":
    main()
