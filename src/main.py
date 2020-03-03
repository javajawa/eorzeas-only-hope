#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

import asyncio

from storage import FileStore
from bot import DiscordBot, TwitchBot

def main():
    with FileStore('list.txt') as storage:
        discord_promise = asyncio.create_task(discord_bot(storage))
        twitch_promise = asyncio.create_task(twich_bot(storage))

        print('All bots spawned')

        await discord_promise
        await twitch_promise

        print('All bots shutdown')


async def twich_bot(storage: FileStore):
    with open('twitch.token', 'r') as token_handle:
        [token, id] = token_handle.read().strip().split(':', 1)
        instance = TwichBot(token, id, 'eorzeas_only_hope', storage)
        instance.join('sugarsh0t')
        instance.run()


async def discord_bot(storage: FileStore):
    with open('discord.token', 'r') as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    instance = DiscordBot(storage)
    instance.run(token)


if __name__ == '__main__':
    main()
