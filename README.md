Eorzea's Only Hope Bot
======================

_Joke'Bot! You're Eorzea's Only Hope!_

This bot collects and outputs the names of the famous Warriors of Light
seen in Final Fantasy XIV.

Currently only implemented as a Discord bot.

Messages sent to it that seem to contain 'you're Eorzea's only hope' are
parsed for character names that are added to the list.

When a user types `!onlyhope` into a channel it can read, it responses with
a randomly selected name, followed by ", you're Eorzea's only hope!".

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

Code License
------------

License: BSD 2-Clause

TODO List
---------

TODO: Add BSD 2-Clause LICENSE file 
TODO: QA the current codebase
TODO: Uncomment the python3.7 changes
  - Reenable future annotations
  - Remove all quotes from types
  - Add properties with types to classes
TODO: Run pylint and mypy over the codebase
TODO: React to messages that have been recorded with some kind of emote
