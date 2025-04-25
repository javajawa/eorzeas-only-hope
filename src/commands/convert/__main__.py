# SPDX-FileCopyrightText: 2025 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations as _future_annotations

import logging
import sys

from . import ConvertorBot


def main() -> None:
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    converter = ConvertorBot(logger)
    sys.stdout.write(converter.converter.run(" ".join(sys.argv[1:])))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
