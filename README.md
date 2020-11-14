Eorzea's Only Hope Bot
======================

_Joke'Bot! You're Eorzea's Only Hope!_

This bot collects and outputs the names of the "famous" Warriors of Light
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

Usage
-----

### General Commands

| Command                     | Behaviour                                     |
|-----------------------------|-----------------------------------------------|
| `!cat`                      | Gets a random cat pic from thecatapi.com      |
| `!selfcare`                 | Reminds people (how) to look after themselves |
| `!buscare`                  | Self care variant for Desert Bus For Hope     |
| `!selfcute` / `!selfcat`    | Reminds people to do a cute thing             |
| `!order <number>`           | Gets a donation amount to get a Order total   |

### Time Keeping Commands

| Command                     | Behaviour                                     |
|-----------------------------|-----------------------------------------------|
| `!march`                    | Gets the current date in March 2020           |
| `!bus`                      | Countdown to Desert Bus, in Points            |


### FFXIV Related Commands

| Command                     | Behaviour                                     |
|-----------------------------|-----------------------------------------------|
| `!onlyhope`                 | Retrieve a random name for the archives.      |
| `!onlyhope <name>`          | Add a name to the archives (discord only)     |
| `!party [<count>]`          | Form a part of `count` names (up to 24)       |
| `!stats`                    | Get the number of names and commands used.    |

There are also a number of call-and-responses for FFXIV. Saying some variation
on this trigger phrases will cause the bot to respond in kind (max once per
ten seconds):

 - > gobbie boom
 - > lali-ho
 - > la-hee
 - > scree
 - > wasshoi

### Minecraft Commands

| Command                     | Behaviour                                     |
|-----------------------------|-----------------------------------------------|
| `!nether <number>...`       | Converts Minecraft nether location to world.  |
| `!overworld <number>...`    | Converts Minecraft world location to nether.  |
| `!pillars <span> [<width>]` | Calculate Minecraft pillar placement.         |


Pillars Command
---------------

The pillars command is used to find pillar spacing to fill `span` blocks
using pillars of width `width`.
Note that this does not include external pillars; if you want pillars at
the end, shorten your `span` by twice your `width`.

For example, calling `!pillars 15` will give:

```
For pillars of 1 blocks spanning 15 blocks:
  7 pillars 1 blocks apart;
  4 pillars 2 blocks apart, with extra centre block;
  3 pillars 3 blocks apart;
  2 pillars 4 blocks apart, with extra centre block
```

These would be built as:

```
#+++++++++++++++#
# | | | | | | | #  7 pillars 1 blocks apart
#+++++++++++++++#
#  |  |   |  |  #  4 pillars 2 blocks apart, with extra centre block
#+++++++++++++++#
#   |   |   |   #  3 pillars 3 blocks apart
#+++++++++++++++#
#    |     |    #  2 pillars 4 blocks apart, with extra centre block
#+++++++++++++++#
```

Note: only one extra block will ever be added, in the centre of an odd number
of gaps (even number of pillars).

Order Command
-------------

The order command looks for nice round totals that are near to the given
number (increases only).
A "round" number is one which:

 - Is all the same digit.
 - Ends more than half in zeroes.
 - Is all the same digit, except some zeros at the end.
 - Has digits that increase or decrease (e.g. `1234`).
 - Has alternating digits (e.g. `35353`).
 - Is Nice (made up of `69` and `420`)
