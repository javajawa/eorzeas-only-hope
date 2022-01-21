#!/bin/sh -e

# SPDX-FileCopyrightText: 2020 Benedict Harcourt <ben.harcourt@harcourtprogramming.co.uk>
#
# SPDX-License-Identifier: BSD-2-Clause

cd "${0%/*}/../src"

black .
flake8
mypy --strict .
pylint bot commands eorzea prosegen
