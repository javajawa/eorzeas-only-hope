import bot.commands

from prosegen import ProseGen


class ProseGenCommand(bot.commands.SimpleCommand):
    """Gets the current date in March 2020"""

    _data: ProseGen

    def __init__(self, name: str, data: ProseGen) -> None:
        super().__init__(name)
        self._data = data

    def message(self) -> str:
        return self._data.make_statement(24)
