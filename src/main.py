#!/usr/bin/python3
# vim: ts=4 expandtab

# from __future__ import annotations

from storage import FileStore
from bot import DiscordBot

def main():
    with FileStore('list.txt') as storage:
        await discord_bot(storage)

async def discord_bot(storage: FileStore):
    with open('discord.token', 'r') as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    instance = DiscordBot(storage)
    instance.run(token)


if __name__ == '__main__':
    main()
