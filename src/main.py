#!/usr/bin/python3
# vim: ts=4 expandtab

from __future__ import annotations

from storage import FileStore
from bot import DiscordBot, TwitchBot


def main():
    with FileStore('list.txt') as storage:
        discord_bot(storage)
        print('All bots shutdown')


def twich_bot(storage: FileStore) -> None:
    with open('twitch.token', 'r') as token_handle:
        [token, client_id] = token_handle.read().strip().split(':', 1)
        instance = TwitchBot(token, int(client_id), 'eorzeas_only_hope', storage)
        instance.join('sugarsh0t')
        instance.run()


def discord_bot(storage: FileStore) -> None:
    with open('discord.token', 'r') as token_handle:
        token = token_handle.read().strip()

    if not token:
        raise Exception("Unable to load token from token file")

    instance = DiscordBot(storage)
    instance.run(token)


if __name__ == '__main__':
    main()
