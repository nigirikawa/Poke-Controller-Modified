#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any
from Commands.Keys import Button
from Commands.PythonCommandBase import PythonCommand
from Commands.PythonCommandBase import ImageProcPythonCommand
from loguru import logger


# ログ出力のサンプル
class LoggingSample(ImageProcPythonCommand):
    NAME = "ログ出力のサンプル"

    def __init__(self, cam: Any):
        super().__init__(cam)

    def do(self) -> None:
        logger.debug("DEBUG")
        logger.info("INFO")
        logger.warning("WARNING")
        logger.error("ERROR")
        logger.critical("CRITICAL")
