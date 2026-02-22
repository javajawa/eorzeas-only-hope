# SPDX-FileCopyrightText: 2026 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

"""Ancient Wisdom, Remixed"""

from __future__ import annotations as _future_annotations

import random

import bot.commands

WISDOM_SECTIONS = list(
    {
        "Float like a butterfly": ", sting like a bee",
        "All work and no play": " makes Jack a dull boy",
        "All is fair": " in love and war",
        "When life gives you lemons": ", make lemonade",
        "If you want something done": ", do it yourself",
        "Ashes to Ashes": ", dust to dust",
        "My name is Ozymandias, King of Kings": ": look on my works, ye Mighty, and despair!",
        "One in the hand": " is worth two in the bush",
        "Speak of the Devil": " and he shall appear",
        "The bigger they are": " the harder they fall",
        "When in Rome": ", do as the Romans do",
        "Better the devil you know": " than the devil you don't",
        "Do as I say": ", not as I do",
        "Ask not for whom the bell tolls": ", it tolls for thee",
        "Do unto others": " as you would have them do unto you",
        "Do not put the cart": " before the horse",
        "One who lives by the sword": ", dies by the sword",
        "Nothing ventured": ", nothing gained",
        "Ask a silly question": ", get a silly answer",
        "Caches to Caches": ", Rust to Rust",
        "Never fuck yourself into a situation": " that you can't fuck your way out of",
        "Fuck around": " and find out",
        "Do or do not": ": there is no try",
        "A bird in the hand": " is worth two in the bush",
        "Don't change horses": ", in the middle of the stream",
        "You can lead a horse to water": ", but you can't make it drink",
        "If you are stuck in a hole": " don't keep digging downwards",
        "Out of the frying pan": " and into the fire",
        "Walk softly": " and carry a big stick",
        "First come": ", first served",
        "Hell has no fury": " like a woman scorn'd",
        "If the shoe fits": ", wear it",
        "If you play with fire": ", you will get burned",
        "Learn a language": ", and you will avoid a war",
        "One who fights and runs away": " may live to fight another day",
        "No guts": ", no glory",
        "Where there is smoke": ", there is fire",
        "Where there is a will": ", there is a way",
        "Red in the morning": ": sailor takes warning",
        "Red at night": ": sailor's delight",
        "May the force": " be with you",
        "Live long": ", and prosper",
        "Women want me": ", fish fear me",
        "Not the sharpest tool": " in the drawer",
        "A few fries short": " of a Happy Meal",
        "He who laughs last": ", laughs best",
        "be polite, be efficient": "; have a plan to kill everyone you meet",
        "Too many cooks": " spoils the broth",
        "You catch more flies with honey": " than with vinegar",
        "Necessity": " is the mother of invention",
        "The squeaky wheel": " gets the grease",
        "If something's worth doing": ", it's worth doing poorly",
        "Measure never": " work forever",
        "Measure twice": "; cut once",
        "Garbage in": ", garbage out",
        "Take care of those you call your own": "and keep good company",
        "The seaweed is always greener": " in somebody else's lake",
        "The grass is always greener": " on the other side of the fence",
        "Even a stopped clock": " is right twice a day",
        "A watched pot": " never boils",
        "Always listen to chat": " - Never listen to chat!",
        "There is no 'I' in team": " but there is a 'me'",
    }.items(),
)


WISDOM_TEMPLATES = [
    "{first}{second}",
    "{first}{second}",
    "{first}{second}",
    "{first}{second}?",
    "{first}{second}!",
    "Kitteh, they say: {first}{second}",
]


class Wisdom(bot.commands.SimpleCommand):
    """Roll for Wisdom"""

    def __init__(self) -> None:
        super().__init__("wisdom")

    @property
    def group(self) -> str:
        return "Stats"

    def matches(self, message: str) -> bool:
        """Check if this command is matched"""
        m_lower = message.lower()

        if m_lower in {"!wis", "!wisdom"}:
            return True

        return m_lower.startswith(("!wis ", "!wisdom "))

    async def message(self) -> str:
        [first, _], [_, second] = random.sample(list(WISDOM_SECTIONS), k=2)

        template = random.choice(WISDOM_TEMPLATES)

        return template.format(first=first, second=second).capitalize()
