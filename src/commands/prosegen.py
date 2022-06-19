import bot.commands

from prosegen import ProseGen


class ProseGenCommand(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    def __init__(self, name: str, data: ProseGen) -> None:
        super().__init__(name, data.make_statement)
