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
a simple twitch both that only implements the responding `!onlyhope`.
The discord bot adds a thumbs-up reaction emoji when it accepts a new entry.

Setting Up
----------

- Install dependencies

```shell
pip install -U -r requirements.txt
```

- Set up Discord token

Your `discord.token` file should just contain your bot's token.
For instructions on how to get a Discord Bot token, read
[https://realpython.com/how-to-make-a-discord-bot-python/]

- Set up the Twitch token

Your `twitch.token` file should contain
```
[username]::oauth:[[token]::[channel]::[...channel]
```

You can get the OAuth token from https://id.twitch.tv/oauth2/authorize.
It will be created for whichever user you're logged in as.

- Run the code

```shell
python3 src/main.py
```
