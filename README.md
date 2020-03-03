Eorzea's Only Hope Bot
======================

_Joke'Bot! You're Eorzea's Only Hope!_

This bot collects and outputs the names of the famous Warriors of Light
seen in Final Fantasy XIV.

Messages sent to it that seem to contain 'you're Eorzea's only hope' are
parsed for character names that are added to the list.

When a user types `!onlyhope` into a channel it can read, it responses with
a randomly selected name, followed by ", you're Eorzea's only hope!".

Currently implemented as a Discord bot that implements both functions, and
a simple twitch both that only implements `!onlyhope`.
The discord bot adds a thumbs-up reaction emoji when it accepts a new entry.

Setting Up
----------

```shell
pip install -U -r requirements.txt

cat >discord.token
[paste your discord token, end with Ctrl+D]

pyhton3 src/main.py
```

For instructions on how to get a Discord Bot token, read
[https://realpython.com/how-to-make-a-discord-bot-python/]
